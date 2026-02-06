import pandas as pd
import pytest
from taxi_ml.validate import validate_train_df


def test_validate_train_ok():
    df = pd.DataFrame({
        "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
        "tpep_dropoff_datetime": ["2025-01-01 10:10:00"],
        "passenger_count": [1],
        "trip_distance": [2.5],
        "rate_code_id": [1],
        "payment_type_id": [1],
        "pu_location_id": [100],
        "do_location_id": [200],
        "total_amount": [15.0],
    })
    validate_train_df(df)


def test_validate_train_missing_cols():
    df = pd.DataFrame({"total_amount": [10.0]})
    with pytest.raises(ValueError):
        validate_train_df(df)
