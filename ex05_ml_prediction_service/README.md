# Exercice 5 — Service de prédiction ML (NYC Yellow Taxi)

## Objectif

**Prédire le montant total d'une course de taxi** (`total_amount`) à partir des données nettoyées du projet, en utilisant un modèle de Machine Learning entraîné sur les parquets stockés dans MinIO.

## Résultats obtenus

| Métrique           | Valeur                        |
|--------------------|-------------------------------|
| Modèle             | HistGradientBoostingRegressor |
| RMSE               | **13.56**                     |
| Lignes entraînées  | **36 817 088** (12 mois 2022) |
| Features           | 10                            |

## Stack technique

| Composant        | Rôle                                   |
|------------------|----------------------------------------|
| scikit-learn     | Pipeline ML (ColumnTransformer + HGBR) |
| pandas / pyarrow | Lecture parquet                         |
| s3fs             | Accès MinIO via protocole S3           |
| joblib           | Sérialisation du modèle                |
| pytest           | Tests unitaires                        |

## Structure du dossier

```
ex05_ml_prediction_service/
├── scripts/
│   ├── train.py          → script d'entraînement
│   └── predict.py        → script de prédiction (inférence)
├── src/taxi_ml/
│   ├── __init__.py
│   ├── config.py         → chemins des fichiers (Paths)
│   ├── io.py             → lecture parquet (local ou MinIO)
│   ├── validate.py       → validation des colonnes requises
│   ├── features.py       → feature engineering (durée, heure, jour)
│   └── model.py          → pipeline ML (preprocessing + HGBR)
├── tests/
│   ├── test_validate_train.py
│   └── test_validate_infer.py
├── artifacts/            → résultats générés (model, metrics, predictions)
├── requirements.txt
└── README.md
```

## Installation

Les dépendances sont gérées par `uv` depuis la racine du projet :

```sh
# Depuis la racine du projet
uv sync
```

## Features du modèle

| Feature           | Type        | Description                      |
|-------------------|-------------|----------------------------------|
| passenger_count   | numérique   | Nombre de passagers              |
| trip_distance     | numérique   | Distance du trajet (miles)       |
| trip_duration_min | numérique   | Durée du trajet (minutes)        |
| pickup_hour       | numérique   | Heure de prise en charge (0-23)  |
| pickup_dayofweek  | numérique   | Jour de la semaine (0-6)         |
| pickup_day        | numérique   | Jour du mois (1-31)             |
| rate_code_id      | catégoriel  | Code tarifaire                   |
| payment_type_id   | catégoriel  | Type de paiement                 |
| pu_location_id    | catégoriel  | Zone de pickup (1-265)           |
| do_location_id    | catégoriel  | Zone de dropoff (1-265)          |

## Entraînement

Depuis la **racine du projet** :

```sh
# Entraîner sur toutes les données nettoyées de 2022
PYTHONPATH=ex05_ml_prediction_service/src uv run python \
  ex05_ml_prediction_service/scripts/train.py \
  --input s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-01/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-02/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-03/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-04/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-05/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-06/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-07/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-08/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-09/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-10/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-11/ \
         s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-12/
```

### Entraîner sur un échantillon (plus rapide)

```sh
PYTHONPATH=ex05_ml_prediction_service/src uv run python \
  ex05_ml_prediction_service/scripts/train.py \
  --input s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-01/ \
  --max-rows 3000000
```

### Résultats

- `artifacts/model.joblib` — modèle sérialisé
- `artifacts/metrics.json` — RMSE + nombre de lignes + liste des features

## Prédiction (inférence)

```sh
PYTHONPATH=ex05_ml_prediction_service/src uv run python \
  ex05_ml_prediction_service/scripts/predict.py \
  --input s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-12/ \
  --output ex05_ml_prediction_service/artifacts/predictions.csv \
  --max-rows 100000
```

### Résultat

- `artifacts/predictions.csv` — une colonne `prediction_total_amount`

## Tests unitaires

```sh
PYTHONPATH=ex05_ml_prediction_service/src uv run pytest ex05_ml_prediction_service/tests/ -q
```

## Pipeline ML

```
Parquet (MinIO)
    ↓
validate_train_df()    → vérifie les colonnes requises
    ↓
add_time_features()    → trip_duration_min, pickup_hour, pickup_dayofweek, pickup_day
    ↓
split_xy()             → X (features) / y (total_amount)
    ↓
build_model()          → ColumnTransformer + HistGradientBoostingRegressor
    ↓
train/test split (80/20)
    ↓
model.fit() → model.predict() → RMSE
    ↓
dump(model) + json(metrics)
```

## Variables d'environnement MinIO

| Variable           | Défaut                  |
|--------------------|-------------------------|
| `MINIO_ENDPOINT`   | `http://localhost:9000` |
| `MINIO_ACCESS_KEY` | `minio`                 |
| `MINIO_SECRET_KEY` | `minio123`              |

## Problèmes courants

### `ModuleNotFoundError: taxi_ml`

Ajouter `PYTHONPATH=ex05_ml_prediction_service/src` avant la commande.

### Erreur MinIO / S3

Vérifier que le conteneur MinIO est lancé (`sudo docker-compose up -d minio`) et que les credentials sont corrects.
