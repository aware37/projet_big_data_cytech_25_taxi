import os
import pandas as pd


# Mapping from original NYC TLC column names to snake_case
_COL_RENAME = {
    "VendorID": "vendor_id",
    "RatecodeID": "rate_code_id",
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",
    "payment_type": "payment_type_id",
    "Airport_fee": "airport_fee",
}


def read_parquet_any(path: str, storage_options=None) -> pd.DataFrame:
    """Read a parquet file from local path or s3-compatible path.

    Automatically renames original TLC column names to snake_case
    so downstream code can use a single naming convention.
    """
    df = pd.read_parquet(path, storage_options=storage_options)
    rename = {k: v for k, v in _COL_RENAME.items() if k in df.columns}
    if rename:
        df = df.rename(columns=rename)
    return df


def build_s3_path(bucket: str, object_key: str) -> str:
    """Build an s3:// path."""
    return f"s3://{bucket}/{object_key}"


def minio_storage_options(endpoint_url: str, access_key: str, secret_key: str) -> dict:
    """Return storage options for s3fs/Minio."""
    return {
        "key": access_key,
        "secret": secret_key,
        "client_kwargs": {"endpoint_url": endpoint_url},
    }


def env_or_default(name: str, default: str) -> str:
    """Get env var or default."""
    return os.getenv(name, default)
