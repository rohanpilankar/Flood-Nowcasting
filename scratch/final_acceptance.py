#!/usr/bin/env python3
"""
Chennai Urban Flood Baseline — Final 24-Check Acceptance Test Suite
Audits canonical dataset, spatial grid, target integrity, chronological split,
predictor allowlist, leakage safeguards, architecture contracts, and SHA-256 hash.
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd

CANONICAL_PARQUET = "Data/final/chennai_flood_training.parquet"
EXPECTED_SHA256 = "ce2bcd5766c26ec6ef152f518f73dd72facfaf00906bc4399cc6dc2c66a2c7b5"
FEATURE_COLUMNS_JSON = "Data/final/feature_columns.json"
TRAIN_TEST_SPLITS_JSON = "Data/final/train_test_splits.json"
RADAR_SCHEMA = "Data/docs/RADAR_NOWCAST_SCHEMA.md"
DRAINAGE_SCHEMA = "Data/docs/DRAINAGE_HYDRAULIC_SCHEMA.md"

AUDITED_PREDICTOR_ALLOWLIST = [
    "rainfall_daily_mm",
    "rainfall_cum_2d_mm",
    "rainfall_cum_3d_mm",
    "rainfall_cum_7d_mm",
    "rainfall_delta_mm",
    "elevation_m",
    "slope_deg",
    "low_lying_score",
    "built_up_ratio",
    "water_ratio",
    "vegetation_ratio",
    "worldcover_class",
    "soil_clay_0_5cm",
    "dist_to_swd_m",
    "dist_to_macro_drain_m",
    "dist_to_micro_drain_m",
    "dist_to_river_stream_m",
    "dist_to_buckingham_canal_m",
    "drainage_density_m_per_km2",
    "building_count",
    "building_area_m2",
    "dist_to_hospital_m",
    "hospital_count_1km",
    "dist_to_fire_station_m",
    "dist_to_police_m"
]

EXCLUDED_NON_PREDICTORS = [
    "grid_id",
    "date",
    "x_utm",
    "y_utm",
    "latitude",
    "longitude",
    "flood_occurred"
]

class AcceptanceSuite:
    def __init__(self):
        self.results = []
        self.failed = False

    def check(self, num, title, condition, expected, actual, reason=""):
        if condition:
            print(f"[PASS] Check {num:02d}: {title} | Actual: {actual}")
            self.results.append((num, title, "PASS", expected, actual, ""))
        else:
            print(f"[FAIL] Check {num:02d}: {title}")
            print(f"       Expected: {expected}")
            print(f"       Actual:   {actual}")
            print(f"       Reason:   {reason}")
            self.results.append((num, title, "FAIL", expected, actual, reason))
            self.failed = True

def run_acceptance_suite(check_model=False):
    suite = AcceptanceSuite()
    print("=" * 80)
    print("FLOODWATCH AI — FINAL SYSTEM ALIGNMENT & ACCEPTANCE TEST SUITE")
    print("=" * 80)

    # Pre-check: file existence
    if not os.path.exists(CANONICAL_PARQUET):
        suite.check(0, "Parquet Existence", False, "File exists", "Missing", f"{CANONICAL_PARQUET} not found")
        sys.exit(1)

    # 24. Raw Parquet Hash (Run early to guarantee data protection)
    with open(CANONICAL_PARQUET, "rb") as f:
        actual_sha256 = hashlib.sha256(f.read()).hexdigest()
    suite.check(
        24, "Raw Parquet SHA-256 Integrity",
        actual_sha256 == EXPECTED_SHA256,
        EXPECTED_SHA256, actual_sha256,
        "Canonical parquet hash has changed or is corrupted"
    )

    # Read data without modifying
    df = pd.read_parquet(CANONICAL_PARQUET)
    df["date_str"] = df["date"].astype(str)

    # Dataset integrity
    # 1. Row count
    suite.check(
        1, "Total Row Count",
        len(df) == 126816,
        126816, len(df),
        "Row count mismatch"
    )

    # 2. Column count
    suite.check(
        2, "Total Column Count",
        len(df.columns) == 33 if "date_str" in df.columns else len(df.columns) == 32,
        32, len([c for c in df.columns if c != "date_str"]),
        "Column count mismatch"
    )

    # 3. Missing values
    null_count = int(df[[c for c in df.columns if c != "date_str"]].isnull().sum().sum())
    suite.check(
        3, "Missing Values Across Dataset",
        null_count == 0,
        0, null_count,
        "Dataset contains null / NaN values"
    )

    # 4. Infinite numerical values
    num_cols = df.select_dtypes(include=np.number).columns
    inf_count = int(np.isinf(df[num_cols]).sum().sum())
    suite.check(
        4, "Infinite Numerical Values",
        inf_count == 0,
        0, inf_count,
        "Dataset contains infinite values"
    )

    # 5. Duplicate [grid_id, date]
    dup_count = int(df.duplicated(subset=["grid_id", "date"]).sum())
    suite.check(
        5, "Duplicate [grid_id, date] Indices",
        dup_count == 0,
        0, dup_count,
        "Duplicate spatial-temporal indices found"
    )

    # Spatial integrity
    # 6. CRS / coordinate convention (EPSG:32644 bounds)
    x_in_range = (df["x_utm"].min() >= 400000) and (df["x_utm"].max() <= 450000)
    y_in_range = (df["y_utm"].min() >= 1400000) and (df["y_utm"].max() <= 1480000)
    lat_in_range = (df["latitude"].min() >= 12.8) and (df["latitude"].max() <= 13.3)
    lon_in_range = (df["longitude"].min() >= 80.0) and (df["longitude"].max() <= 80.4)
    crs_valid = x_in_range and y_in_range and lat_in_range and lon_in_range
    suite.check(
        6, "CRS / Coordinate Convention (EPSG:32644)",
        crs_valid,
        "UTM Zone 44N projected coordinates [400k-450k E, 1400k-1480k N]",
        f"x:[{df['x_utm'].min()}, {df['x_utm'].max()}], y:[{df['y_utm'].min()}, {df['y_utm'].max()}]",
        "Coordinate bounds outside Chennai EPSG:32644 footprint"
    )

    # 7. Grid spacing
    xs = sorted(df["x_utm"].unique())
    ys = sorted(df["y_utm"].unique())
    diffs_x = set(round(xs[i+1] - xs[i], 2) for i in range(len(xs)-1))
    diffs_y = set(round(ys[i+1] - ys[i], 2) for i in range(len(ys)-1))
    spacing_valid = (diffs_x == {500.0}) and (diffs_y == {500.0})
    suite.check(
        7, "Metric Grid Spacing",
        spacing_valid,
        "Exact 500.0 m spacing in both X and Y dimensions",
        f"diff_x: {diffs_x}, diff_y: {diffs_y}",
        "Grid cells are not spaced at regular 500m intervals"
    )

    # 8. Unique grid cells
    unique_cells = df["grid_id"].nunique()
    suite.check(
        8, "Unique Grid Cell Count",
        unique_cells == 3963,
        3963, unique_cells,
        "Unique cell count differs from 3,963"
    )

    # Target integrity
    # 9. Target existence
    suite.check(
        9, "Target Column Existence",
        "flood_occurred" in df.columns,
        "flood_occurred present",
        "flood_occurred in columns" if "flood_occurred" in df.columns else "Missing",
        "Target column flood_occurred missing"
    )

    # 10. Target binary
    unique_targets = set(df["flood_occurred"].unique())
    suite.check(
        10, "Target Binary Values",
        unique_targets == {0, 1},
        "{0, 1}", unique_targets,
        "Target values are not strictly binary {0, 1}"
    )

    # Partitions
    train_df = df[(df["date_str"] >= "2015-10-01") & (df["date_str"] <= "2015-11-17")]
    excl_df = df[(df["date_str"] >= "2015-11-18") & (df["date_str"] <= "2015-11-29")]
    val_df = df[(df["date_str"] >= "2015-11-30") & (df["date_str"] <= "2015-12-02")]
    test_df = df[(df["date_str"] >= "2015-12-03") & (df["date_str"] <= "2015-12-10")]

    # 11. TRAIN class diversity
    train_classes = set(train_df["flood_occurred"].unique())
    suite.check(
        11, "TRAIN Class Diversity",
        train_classes == {0, 1},
        "{0, 1}", train_classes,
        "TRAIN set does not contain both 0 and 1 classes"
    )

    # 12. VALIDATION class diversity
    val_classes = set(val_df["flood_occurred"].unique())
    suite.check(
        12, "VALIDATION Class Diversity",
        val_classes == {0, 1},
        "{0, 1}", val_classes,
        "VALIDATION set does not contain both 0 and 1 classes"
    )

    # 13. TEST class diversity
    test_classes = set(test_df["flood_occurred"].unique())
    suite.check(
        13, "TEST Class Diversity",
        test_classes == {0, 1},
        "{0, 1}", test_classes,
        "TEST set does not contain both 0 and 1 classes"
    )

    # Split integrity
    # 14. Date membership
    actual_dates = (
        train_df["date_str"].nunique(),
        val_df["date_str"].nunique(),
        test_df["date_str"].nunique(),
        excl_df["date_str"].nunique()
    )
    expected_dates = (14, 3, 7, 8)
    suite.check(
        14, "Partition Date Counts (TRAIN, VAL, TEST, EXCLUDED)",
        actual_dates == expected_dates,
        "TRAIN:14, VAL:3, TEST:7, EXCLUDED:8",
        f"TRAIN:{actual_dates[0]}, VAL:{actual_dates[1]}, TEST:{actual_dates[2]}, EXCLUDED:{actual_dates[3]}",
        "Partition date counts mismatch"
    )

    # 15. Row counts
    actual_rows = (len(train_df), len(val_df), len(test_df), len(excl_df))
    expected_rows = (55482, 11889, 27741, 31704)
    suite.check(
        15, "Partition Row Counts (TRAIN, VAL, TEST, EXCLUDED)",
        actual_rows == expected_rows,
        "TRAIN:55482, VAL:11889, TEST:27741, EXCLUDED:31704",
        f"TRAIN:{actual_rows[0]}, VAL:{actual_rows[1]}, TEST:{actual_rows[2]}, EXCLUDED:{actual_rows[3]}",
        "Partition row counts mismatch"
    )

    # 16. Positive counts
    actual_pos = (
        int((train_df["flood_occurred"] == 1).sum()),
        int((val_df["flood_occurred"] == 1).sum()),
        int((test_df["flood_occurred"] == 1).sum()),
        int((excl_df["flood_occurred"] == 1).sum())
    )
    expected_pos = (1653, 1653, 1102, 0)
    suite.check(
        16, "Partition Positive Counts (TRAIN, VAL, TEST, EXCLUDED)",
        actual_pos == expected_pos,
        "TRAIN:1653, VAL:1653, TEST:1102, EXCLUDED:0",
        f"TRAIN:{actual_pos[0]}, VAL:{actual_pos[1]}, TEST:{actual_pos[2]}, EXCLUDED:{actual_pos[3]}",
        "Positive event counts mismatch across partitions"
    )

    # 17. Temporal ordering
    max_train_date = train_df["date_str"].max()
    min_val_date = val_df["date_str"].min()
    max_val_date = val_df["date_str"].max()
    min_test_date = test_df["date_str"].min()
    temporal_order_valid = (max_train_date < min_val_date) and (max_val_date < min_test_date)
    suite.check(
        17, "Temporal Ordering (max(TRAIN) < min(VAL) < min(TEST))",
        temporal_order_valid,
        "max(TRAIN) < min(VAL) and max(VAL) < min(TEST)",
        f"TRAIN max: {max_train_date} < VAL min: {min_val_date}, VAL max: {max_val_date} < TEST min: {min_test_date}",
        "Temporal ordering violated: potential future information leakage"
    )

    # Predictor integrity
    actual_predictors = [c for c in df.columns if c not in EXCLUDED_NON_PREDICTORS and c != "date_str"]

    # 18. Predictor allowlist
    suite.check(
        18, "Predictor Allowlist Conformance",
        sorted(actual_predictors) == sorted(AUDITED_PREDICTOR_ALLOWLIST),
        f"Exact 25 audited predictors (count: {len(AUDITED_PREDICTOR_ALLOWLIST)})",
        f"Actual predictor count: {len(actual_predictors)}",
        f"Predictor mismatch: Diff={set(actual_predictors) ^ set(AUDITED_PREDICTOR_ALLOWLIST)}"
    )

    # 19. Target exclusion
    suite.check(
        19, "Target Column Excluded From Predictors",
        "flood_occurred" not in actual_predictors,
        "flood_occurred absent from predictors",
        "Excluded" if "flood_occurred" not in actual_predictors else "LEAKED",
        "Target variable flood_occurred is present in predictor list"
    )

    # 20. Identifier exclusion
    leaked_ids = [c for c in ["grid_id", "date", "x_utm", "y_utm", "latitude", "longitude"] if c in actual_predictors]
    suite.check(
        20, "Spatial & Temporal Identifiers Excluded From Predictors",
        len(leaked_ids) == 0,
        "None of [grid_id, date, x_utm, y_utm, latitude, longitude] in predictors",
        f"Leaked: {leaked_ids}" if leaked_ids else "All excluded",
        f"Spatial or temporal identifiers leaked into predictor matrix: {leaked_ids}"
    )

    # 21. Leakage/provenance validation (check against feature_columns.json)
    with open(FEATURE_COLUMNS_JSON, "r") as f:
        meta_feat = json.load(f)
    meta_feat_names = [feat["feature_name"] for feat in meta_feat.get("features", [])]
    unknown_predictors = [p for p in actual_predictors if p not in meta_feat_names]
    suite.check(
        21, "Feature Provenance & Audited Inventory Membership",
        len(unknown_predictors) == 0,
        "All predictors registered in feature_columns.json",
        f"Unknown predictors: {unknown_predictors}" if unknown_predictors else "All 25 validated",
        f"Undocumented or unapproved predictors found: {unknown_predictors}"
    )

    # 22. Krishna Canal feature exclusion
    suite.check(
        22, "Krishna Water Canal Feature Exclusion",
        "dist_to_krishna_water_canal_m" not in df.columns,
        "dist_to_krishna_water_canal_m absent from dataset",
        "Absent" if "dist_to_krishna_water_canal_m" not in df.columns else "Present",
        "dist_to_krishna_water_canal_m found in dataset"
    )

    # Architecture integrity
    # 23. Interface contracts
    radar_ok = False
    drainage_ok = False
    if os.path.exists(RADAR_SCHEMA):
        with open(RADAR_SCHEMA, "r") as f:
            radar_txt = f.read()
        radar_ok = ("STATUS: FUTURE DATA INTERFACE" in radar_txt) and ("CURRENT RADAR DATA PRESENT: NO" in radar_txt)

    if os.path.exists(DRAINAGE_SCHEMA):
        with open(DRAINAGE_SCHEMA, "r") as f:
            drainage_txt = f.read()
        drainage_ok = ("STATUS: FUTURE DATA INTERFACE" in drainage_txt) and ("CURRENT DRAINAGE TELEMETRY: NOT AVAILABLE" in drainage_txt)

    contracts_valid = radar_ok and drainage_ok
    suite.check(
        23, "Future Interface Contracts Status",
        contracts_valid,
        "RADAR_NOWCAST_SCHEMA.md & DRAINAGE_HYDRAULIC_SCHEMA.md present with future status",
        f"radar_schema_ok: {radar_ok}, drainage_schema_ok: {drainage_ok}",
        "Interface contracts missing or lacking required status declarations"
    )

    # Check 25 (Model artifact validation, evaluated if requested or model files exist)
    model_json = "Models/trained/chennai_xgboost_baseline.json"
    meta_json = "Models/metadata/chennai_xgboost_baseline_metadata.json"
    metrics_json = "Models/metadata/chennai_xgboost_baseline_metrics.json"
    feat_imp_json = "Models/metadata/chennai_xgboost_baseline_feature_importance.json"

    if check_model or os.path.exists(model_json):
        model_files_exist = (
            os.path.exists(model_json) and
            os.path.exists(meta_json) and
            os.path.exists(metrics_json) and
            os.path.exists(feat_imp_json)
        )
        meta_valid = False
        if model_files_exist:
            with open(meta_json, "r") as f:
                meta = json.load(f)
            required_keys = [
                "dataset_path", "dataset_sha256", "dataset_row_count", "dataset_column_count",
                "target", "predictor_allowlist", "split_definition", "split_counts",
                "class_weight", "hyperparameters", "random_seed", "xgboost_version",
                "python_version", "early_stopping_configuration", "threshold_selection_method",
                "selected_threshold", "test_metrics"
            ]
            missing_keys = [k for k in required_keys if k not in meta]
            meta_valid = (len(missing_keys) == 0) and (meta["dataset_sha256"] == EXPECTED_SHA256)
        suite.check(
            25, "Model Artifacts & Comprehensive Metadata Validation",
            model_files_exist and meta_valid,
            "Trained model, metadata, metrics, and feature importance JSON exist with complete schema",
            f"files_exist: {model_files_exist}, metadata_valid: {meta_valid}",
            "Model artifacts missing or metadata incomplete"
        )

    print("=" * 80)
    passed_count = sum(1 for r in suite.results if r[2] == "PASS")
    total_count = len(suite.results)
    print(f"ACCEPTANCE TEST SUMMARY: {passed_count}/{total_count} CHECKS PASSED")
    print("=" * 80)

    if suite.failed:
        print("RESULT: FAIL — Acceptance criteria not satisfied.")
        sys.exit(1)
    else:
        print("RESULT: ALL REQUIRED CHECKS PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    check_model = "--check-model" in sys.argv
    run_acceptance_suite(check_model=check_model)
