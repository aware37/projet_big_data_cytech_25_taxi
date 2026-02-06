import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create basic time features from pickup/dropoff datetimes."""
    out = df.copy()
    out["tpep_pickup_datetime"] = pd.to_datetime(out["tpep_pickup_datetime"])
    out["tpep_dropoff_datetime"] = pd.to_datetime(out["tpep_dropoff_datetime"])

    duration_sec = (out["tpep_dropoff_datetime"] - out["tpep_pickup_datetime"]).dt.total_seconds()
    out["trip_duration_min"] = (duration_sec / 60.0).clip(lower=0)

    out["pickup_hour"] = out["tpep_pickup_datetime"].dt.hour
    out["pickup_dayofweek"] = out["tpep_pickup_datetime"].dt.dayofweek
    out["pickup_day"] = out["tpep_pickup_datetime"].dt.day

    return out


def split_xy(df: pd.DataFrame):
    """Return X, y with selected columns."""
    feature_cols = [
        "passenger_count",
        "trip_distance",
        "trip_duration_min",
        "pickup_hour",
        "pickup_dayofweek",
        "pickup_day",
        "rate_code_id",
        "payment_type_id",
        "pu_location_id",
        "do_location_id",
    ]
    X = df[feature_cols].copy()
    y = df["total_amount"].copy() if "total_amount" in df.columns else None
    return X, y, feature_cols
