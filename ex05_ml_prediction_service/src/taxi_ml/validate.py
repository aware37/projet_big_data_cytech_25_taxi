import pandas as pd


TRAIN_REQUIRED_COLS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "rate_code_id",
    "payment_type_id",
    "pu_location_id",
    "do_location_id",
    "total_amount",
]

INFER_REQUIRED_COLS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "rate_code_id",
    "payment_type_id",
    "pu_location_id",
    "do_location_id",
]


def validate_train_df(df: pd.DataFrame) -> None:
    """Validate training dataframe schema and basic constraints."""
    missing = [c for c in TRAIN_REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for training: {missing}")

    if df["total_amount"].isna().any():
        raise ValueError("total_amount contains NaN")

    if (df["trip_distance"] < 0).any():
        raise ValueError("trip_distance contains negative values")


def validate_infer_df(df: pd.DataFrame) -> None:
    """Validate inference dataframe schema and basic constraints."""
    missing = [c for c in INFER_REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for inference: {missing}")

    if (df["trip_distance"] < 0).any():
        raise ValueError("trip_distance contains negative values")
