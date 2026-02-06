# Exercice 6 — Orchestration Airflow

## Objectif

Automatiser et orchestrer le pipeline Big Data complet à l'aide d'**Apache Airflow**.

## Pourquoi Airflow ?

Le pipeline du projet comporte plusieurs étapes séquentielles et interdépendantes :

1. **Téléchargement** des nouveaux parquets depuis NYC TLC (ex01)
2. **Ingestion Spark** : nettoyage → MinIO + PostgreSQL (ex02)
3. **Ré-entraînement ML** quand de nouvelles données arrivent (ex05)

Airflow permet de :
- **Planifier** l'exécution automatique (cron mensuel par ex.)
- **Chaîner** les tâches avec des dépendances (DAG)
- **Monitorer** l'état du pipeline (succès, échec, retry)
- **Alerter** en cas de problème

## Architecture prévue

```
DAG: nyc_taxi_pipeline (mensuel)
│
├── download_parquet        → ex01 (sbt run)
├── spark_ingestion         → ex02 (sbt run)
│   ├── branch_1_minio      → parquet nettoyé → MinIO
│   └── branch_2_postgres   → fact_trips → PostgreSQL
├── retrain_model           → ex05 (train.py)
└── notify_completion       → log / email
```

## Statut

⬜ Non implémenté — Ce dossier est prévu pour une future automatisation du pipeline.

## Notes

- Airflow est déjà listé dans les dépendances du `pyproject.toml`
- L'infrastructure Docker existante (MinIO, PostgreSQL, Spark) est compatible avec Airflow
- Les scripts ex01/ex02 (SBT) et ex05 (Python) sont tous exécutables en ligne de commande, donc orchestrables via `BashOperator` ou `PythonOperator`
