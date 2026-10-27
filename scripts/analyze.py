"""Build a reproducible maintenance KPI table from UCI's AI4I 2020 CSV."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlretrieve
import zipfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SOURCE = DATA / "source.zip"
SOURCE_URL = (
    "https://archive.ics.uci.edu/static/public/601/"
    "ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip"
)
MODE_COLS = ["TWF", "HDF", "PWF", "OSF", "RNF"]
TYPE_NAMES = {"L": "Low", "M": "Medium", "H": "High"}
WEAR_LABELS = ["01 0–49", "02 50–99", "03 100–149", "04 150–199", "05 200+"]


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        urlretrieve(SOURCE_URL, SOURCE)

    with zipfile.ZipFile(SOURCE) as archive:
        source = pd.read_csv(io.BytesIO(archive.read("ai4i2020.csv")))
    if source.shape != (10000, 14):
        raise ValueError(f"Unexpected source shape: {source.shape}")
    if source.isna().any().any() or source["UDI"].nunique() != len(source):
        raise ValueError("Missing fields or non-unique UDI")
    if set(source["Type"]) != set(TYPE_NAMES):
        raise ValueError("Unexpected product type")
    if not source[["Machine failure", *MODE_COLS]].isin([0, 1]).all().all():
        raise ValueError("Non-binary target or mode flag")

    events = source.rename(columns={
        "Product ID": "ProductID",
        "Air temperature [K]": "AirTempK",
        "Process temperature [K]": "ProcessTempK",
        "Rotational speed [rpm]": "SpeedRPM",
        "Torque [Nm]": "TorqueNm",
        "Tool wear [min]": "ToolWearMin",
        "Machine failure": "Failure",
    }).copy()
    events["TypeName"] = events["Type"].map(TYPE_NAMES)
    events["CycleCount"] = 1
    events["ThermalGapK"] = (events["ProcessTempK"] - events["AirTempK"]).round(1)
    events["MechanicalPowerW"] = (
        events["TorqueNm"] * events["SpeedRPM"] * (2 * np.pi / 60)
    ).round(1)
    events["WearBand"] = pd.cut(
        events["ToolWearMin"], [-1, 49, 99, 149, 199, np.inf],
        labels=WEAR_LABELS,
    ).astype(str)
    events["PowerBand"] = pd.cut(
        events["MechanicalPowerW"], [-np.inf, 3500, 9000, np.inf],
        labels=["01 Below 3.5 kW", "02 3.5–9 kW", "03 Above 9 kW"],
        right=False,
    ).astype(str)
    events["ModeFlagCount"] = events[MODE_COLS].sum(axis=1)
    events["LabelMismatch"] = (
        events["Failure"] != (events["ModeFlagCount"] > 0).astype(int)
    ).astype(int)
    events["PrimaryMode"] = "No failure"
    failed = events["Failure"] == 1
    events.loc[failed & (events["ModeFlagCount"] == 0), "PrimaryMode"] = "Unspecified"
    events.loc[failed & (events["ModeFlagCount"] > 1), "PrimaryMode"] = "Multiple flags"
    for mode in MODE_COLS:
        events.loc[
            failed & (events["ModeFlagCount"] == 1) & (events[mode] == 1),
            "PrimaryMode",
        ] = mode

    # This is sequence order, not a calendar date or elapsed machine life.
    events["SequenceBlock"] = ((events["UDI"] - 1) // 500 + 1).astype(int)
    events["SequenceBlockLabel"] = events["SequenceBlock"].map(lambda n: f"{n:02d}")

    cols = [
        "UDI", "ProductID", "Type", "TypeName", "AirTempK", "ProcessTempK",
        "ThermalGapK", "SpeedRPM", "TorqueNm", "MechanicalPowerW",
        "ToolWearMin", "WearBand", "PowerBand", "Failure", "PrimaryMode",
        "ModeFlagCount", "LabelMismatch", "SequenceBlock", "SequenceBlockLabel",
        "CycleCount", *MODE_COLS,
    ]
    events[cols].to_csv(DATA / "events.csv", index=False, lineterminator="\n")

    def group_report(group: str) -> pd.DataFrame:
        frame = events.groupby(group, observed=True).agg(
            Cycles=("CycleCount", "sum"), Failures=("Failure", "sum"),
            LabelMismatches=("LabelMismatch", "sum"),
        ).reset_index()
        frame["FailureRate"] = frame["Failures"] / frame["Cycles"]
        return frame

    for group, name in [
        ("TypeName", "by-type.csv"),
        ("WearBand", "by-wear.csv"),
        ("PowerBand", "by-power.csv"),
        ("SequenceBlockLabel", "by-sequence.csv"),
    ]:
        group_report(group).to_csv(REPORTS / name, index=False, float_format="%.6f")

    modes = events.loc[failed].groupby("PrimaryMode").agg(
        Failures=("Failure", "sum"),
    ).reset_index().sort_values("Failures", ascending=False)
    modes.to_csv(REPORTS / "failure-mode-summary.csv", index=False)

    metrics = {
        "cycles": int(len(events)),
        "failures": int(events["Failure"].sum()),
        "failure_rate": float(events["Failure"].mean()),
        "label_mismatches": int(events["LabelMismatch"].sum()),
        "failed_without_mode": int((failed & (events["ModeFlagCount"] == 0)).sum()),
        "nonfailed_with_mode": int((~failed & (events["ModeFlagCount"] > 0)).sum()),
        "failures_with_multiple_modes": int((failed & (events["ModeFlagCount"] > 1)).sum()),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "source_rows": int(len(source)),
    }
    assert modes["Failures"].sum() == metrics["failures"]
    assert metrics["failed_without_mode"] + metrics["nonfailed_with_mode"] == metrics["label_mismatches"]
    assert group_report("TypeName")["Failures"].sum() == metrics["failures"]
    (REPORTS / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
