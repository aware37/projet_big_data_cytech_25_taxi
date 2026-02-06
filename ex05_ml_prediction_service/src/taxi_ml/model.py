import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import HistGradientBoostingRegressor


def build_model(categorical_cols, numeric_cols) -> Pipeline:
    """Build a sklearn pipeline model.

    Uses OrdinalEncoder + HistGradientBoosting's native categorical
    support instead of OneHotEncoder, which is far more efficient
    when categories have high cardinality (e.g. 265 location IDs).
    """
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value",
                                       unknown_value=-1)),
        ]
    )

    pre = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
    )

    # OrdinalEncoder handles high-cardinality categories (>255),
    # so we let HGBR treat them as ordinal-encoded numeric features.
    reg = HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.05,
        max_iter=400,
        random_state=42,
    )

    return Pipeline(steps=[("preprocess", pre), ("model", reg)])


def rmse(y_true, y_pred) -> float:
    """Compute RMSE."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))
