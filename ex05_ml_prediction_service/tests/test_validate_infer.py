import pandas as pd
import pytest
from taxi_ml.validate import validate_infer_df


def test_validate_infer_ok():
    df = pd.DataFrame({
        "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
        "tpep_dropoff_datetime": ["2025-01-01 10:10:00"],
        "passenger_count": [1],
        "trip_distance": [2.5],
        "rate_code_id": [1],
        "payment_type_id": [1],
        "pu_location_id": [100],
        "do_location_id": [200],
    })
    validate_infer_df(df)


def test_validate_infer_missing_cols():
    df = pd.DataFrame({"trip_distance": [1.0]})
    with pytest.raises(ValueError):
        validate_infer_df(df)
