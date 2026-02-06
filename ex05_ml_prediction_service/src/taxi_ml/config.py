from dataclasses import dataclass


@dataclass(frozen=True)
class MinioConfig:
    """Minio access configuration."""
    endpoint_url: str  # e.g. "http://localhost:9000"
    access_key: str
    secret_key: str
    bucket: str        # e.g. "nyc-processed" (branche 1)
    object_key: str    # e.g. "yellow/year=2025/month=01/part-....parquet"


@dataclass(frozen=True)
class Paths:
    """Local paths for artifacts."""
    artifacts_dir: str = "artifacts"
    model_path: str = "artifacts/model.joblib"
    metrics_path: str = "artifacts/metrics.json"
