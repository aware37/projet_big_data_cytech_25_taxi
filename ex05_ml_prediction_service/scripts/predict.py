import argparse
import gc
import os
import pandas as pd
from joblib import load

from taxi_ml.io import read_parquet_any, minio_storage_options
from taxi_ml.validate import validate_infer_df
from taxi_ml.features import add_time_features, split_xy
from taxi_ml.config import Paths


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, nargs="+",
                   help="One or more parquet paths (local or s3://)")
    p.add_argument("--output", default="artifacts/predictions.csv")
    p.add_argument("--minio-endpoint", default=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
    p.add_argument("--minio-access", default=os.getenv("MINIO_ACCESS_KEY", "minio"))
    p.add_argument("--minio-secret", default=os.getenv("MINIO_SECRET_KEY", "minio123"))
    p.add_argument("--max-rows", type=int, default=None,
                   help="Cap total rows (random sample). If omitted, uses ALL rows.")
    return p.parse_args()


def main():
    args = parse_args()
    paths = Paths()

    storage_options = None
    if any(p.startswith("s3://") for p in args.input):
        storage_options = minio_storage_options(
            args.minio_endpoint, args.minio_access, args.minio_secret)

    frames = []
    for src in args.input:
        print(f"[PREDICT] Reading {src} ...")
        so = storage_options if src.startswith("s3://") else None
        chunk = read_parquet_any(src, storage_options=so)
        frames.append(chunk)
        print(f"          → {len(chunk):,} rows")

    df = pd.concat(frames, ignore_index=True)
    del frames
    gc.collect()
    print(f"[PREDICT] Total: {len(df):,} rows")

    if args.max_rows and len(df) > args.max_rows:
        print(f"[PREDICT] Capping to {args.max_rows:,} rows")
        df = df.sample(n=args.max_rows, random_state=42).reset_index(drop=True)

    validate_infer_df(df)

    df_feat = add_time_features(df)
    X, _, _ = split_xy(df_feat)
    del df, df_feat
    gc.collect()

    model = load(paths.model_path)
    preds = model.predict(X)

    out = pd.DataFrame({"prediction_total_amount": preds})
    out.to_csv(args.output, index=False)

    print(f"[PREDICT] wrote -> {args.output}")


if __name__ == "__main__":
    main()
