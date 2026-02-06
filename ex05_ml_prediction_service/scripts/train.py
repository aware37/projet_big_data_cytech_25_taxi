import argparse
import json
import os
import glob
import gc
import pandas as pd
from joblib import dump
from sklearn.model_selection import train_test_split

from taxi_ml.io import read_parquet_any, minio_storage_options
from taxi_ml.validate import validate_train_df
from taxi_ml.features import add_time_features, split_xy
from taxi_ml.model import build_model, rmse
from taxi_ml.config import Paths


NEEDED_COLS = [
    "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance",
    "rate_code_id", "payment_type_id",
    "pu_location_id", "do_location_id",
    "total_amount",
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, nargs="+",
                   help="One or more parquet paths (local or s3://). "
                        "Supports multiple months: --input s3://bucket/cleaned/2022-01/ s3://bucket/cleaned/2022-02/")
    p.add_argument("--minio-endpoint", default=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
    p.add_argument("--minio-access", default=os.getenv("MINIO_ACCESS_KEY", "minio"))
    p.add_argument("--minio-secret", default=os.getenv("MINIO_SECRET_KEY", "minio123"))
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--max-rows", type=int, default=None,
                   help="Cap total rows (random sample after concat). "
                        "If omitted, uses ALL rows.")
    return p.parse_args()


def main():
    args = parse_args()
    paths = Paths()
    os.makedirs(paths.artifacts_dir, exist_ok=True)

    storage_options = None
    if any(p.startswith("s3://") for p in args.input):
        storage_options = minio_storage_options(
            args.minio_endpoint, args.minio_access, args.minio_secret)

    # ── Read all input files, keeping only needed columns ────────
    frames = []
    for src in args.input:
        print(f"[TRAIN] Reading {src} ...")
        so = storage_options if src.startswith("s3://") else None
        chunk = read_parquet_any(src, storage_options=so)
        # Keep only necessary columns to save RAM
        keep = [c for c in NEEDED_COLS if c in chunk.columns]
        chunk = chunk[keep]
        frames.append(chunk)
        print(f"         → {len(chunk):,} rows")

    df = pd.concat(frames, ignore_index=True)
    del frames
    gc.collect()
    print(f"[TRAIN] Total: {len(df):,} rows  "
          f"({df.memory_usage(deep=True).sum()/1e6:.0f} MB)")

    # Optional cap
    if args.max_rows and len(df) > args.max_rows:
        print(f"[TRAIN] Capping to {args.max_rows:,} rows")
        df = df.sample(n=args.max_rows, random_state=42).reset_index(drop=True)

    validate_train_df(df)

    df = add_time_features(df)
    X, y, feature_cols = split_xy(df)
    del df
    gc.collect()

    categorical_cols = ["rate_code_id", "payment_type_id",
                        "pu_location_id", "do_location_id"]
    numeric_cols = [c for c in feature_cols if c not in categorical_cols]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42
    )
    del X, y
    gc.collect()

    model = build_model(categorical_cols, numeric_cols)
    print("[TRAIN] Fitting model …")
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    score = rmse(y_test, pred)

    metrics = {"rmse": score, "n_rows": int(len(X_train) + len(X_test)),
               "features": feature_cols}

    dump(model, paths.model_path)
    with open(paths.metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[TRAIN] RMSE={score:.4f}")
    print(f"[TRAIN] model saved -> {paths.model_path}")
    print(f"[TRAIN] metrics saved -> {paths.metrics_path}")


if __name__ == "__main__":
    main()
