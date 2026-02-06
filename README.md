# Projet Big Data — NYC Yellow Taxi 🚕

Projet Big Data CY Tech 2025 — Pipeline complet d'ingestion, analyse et prédiction sur les données NYC Yellow Taxi Trip Records.

## Exercices

| Exercice | Description | Status |
|----------|-------------|--------|
| [ex01](ex01_data_retrieval/) | Récupération des données (Scala → MinIO) | ✅ |
| [ex02](ex02_data_ingestion/) | Ingestion Spark (MinIO → PostgreSQL + Parquet nettoyé) | ✅ |
| [ex03](ex03_sql_table_creation/) | Création du schéma en étoile (SQL) | ✅ |
| [ex04](ex04_dashboard/) | Dashboard analytique (Streamlit + Plotly) | ✅ |
| [ex05](ex05_ml_prediction_service/) | Prédiction ML du montant (scikit-learn) | ✅ |
| [ex06](ex06_airflow/) | Orchestration Airflow | ⬜ |

## Architecture

```
NYC TLC (web)
    ↓  ex01 (Scala/SBT)
MinIO (S3) — raw/
    ↓  ex02 (Spark)
    ├── MinIO — cleaned/          → ex05 (ML)
    └── PostgreSQL — fact_trips   → ex04 (Dashboard)
            ↑
       ex03 (DDL + dimensions)
```

## Prérequis

- **Docker** et **Docker Compose**
- **SBT** (Scala Build Tool)
- **Python 3.10+**
- **uv** — gestionnaire de packages Python

```sh
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Démarrage rapide

### 1. Initialiser l'environnement Python

```sh
uv sync
```

### 2. Lancer l'infrastructure Docker

```sh
sudo docker-compose up -d
```

Services démarrés :
- **MinIO** — stockage S3 : [http://localhost:9001](http://localhost:9001) (`minio` / `minio123`)
- **PostgreSQL** — base `bigdata_db` : port 5432 (`postgres` / `postgres`)
- **Spark** — master + 2 workers

### 3. Télécharger les données (ex01)

```sh
cd ex01_data_retrieval
sbt "run --start 2022-01 --end 2022-12"
cd ..
```

### 4. Vérifier les tables de dimension (ex03)

Les tables sont créées automatiquement au premier lancement du conteneur PostgreSQL.

```sh
sudo docker exec -it postgres psql -U postgres -d bigdata_db
```

```sql
SELECT COUNT(*) FROM dim_location;      -- 265
SELECT COUNT(*) FROM dim_vendor;        -- 5
SELECT COUNT(*) FROM dim_payment_type;  -- 7
SELECT COUNT(*) FROM dim_rate_code;     -- 7
\q
```

### 5. Ingérer les données (ex02)

```sh
cd ex02_data_ingestion
sbt "run --start 2022-01 --end 2022-12"
cd ..
```

Résultat : ~39.6M lignes dans `fact_trips` + parquets nettoyés dans MinIO.

### 6. Lancer le dashboard (ex04)

```sh
cd ex04_dashboard
uv run streamlit run app.py
```

→ [http://localhost:8501](http://localhost:8501)

### 7. Entraîner le modèle ML (ex05)

```sh
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

### 8. Prédictions ML (ex05)

```sh
PYTHONPATH=ex05_ml_prediction_service/src uv run python \
  ex05_ml_prediction_service/scripts/predict.py \
  --input s3://nyc-yellow-tripdata/cleaned/yellow_tripdata_2022-12/ \
  --output ex05_ml_prediction_service/artifacts/predictions.csv \
  --max-rows 100000
```

---

## Résumé des commandes

```sh
# 0. Environnement Python
uv sync

# 1. Infrastructure
sudo docker-compose up -d

# 2. Téléchargement des données
cd ex01_data_retrieval && sbt "run --start 2022-01 --end 2022-12" && cd ..

# 3. Ingestion Spark
cd ex02_data_ingestion && sbt "run --start 2022-01 --end 2022-12" && cd ..

# 4. Dashboard
cd ex04_dashboard && uv run streamlit run app.py

# 5. ML — entraînement (voir ex05/README.md pour la commande complète)
# 6. ML — prédiction (voir ex05/README.md)
```

---

## Stack technique

| Technologie      | Usage                              |
|------------------|------------------------------------|
| Scala 2.13 / SBT | Téléchargement + ETL Spark        |
| Apache Spark 3.5  | Traitement distribué des données  |
| MinIO             | Stockage S3-compatible (parquets) |
| PostgreSQL 15     | Data Warehouse (star schema)      |
| Streamlit + Plotly| Dashboard interactif              |
| scikit-learn      | Modèle ML (HGBR)                 |
| Docker Compose    | Orchestration des services        |
| uv                | Gestion des dépendances Python    |

## Dépannage

### Vider MinIO (si stockage plein)

```sh
sudo docker exec -it minio mc rb --force minio/nyc-yellow-tripdata
```

### Redémarrer PostgreSQL

```sh
sudo docker-compose restart postgres
```

### Tout recommencer

```sh
sudo docker-compose down
sudo docker volume prune
sudo docker-compose up -d
```

---

## Modalités de rendu

1. Pull Request vers la branch `master`
2. Dépôt du rapport et du code source zippé dans cours.cyu.fr

**Date limite : 7 février 2026**