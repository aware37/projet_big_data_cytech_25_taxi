# Exercice 2 — Ingestion des données (Data Ingestion)

## Objectif

Lire les fichiers Parquet bruts depuis MinIO, les nettoyer avec **Apache Spark** et les stocker :

- **Branche 1 (ML)** : Parquet nettoyé → MinIO (`cleaned/`)
- **Branche 2 (DW)** : Données normalisées → PostgreSQL (`fact_trips`)

## Fonctionnement

Pour chaque mois dans la plage demandée, le programme Spark :

### Branche 1 — Nettoyage pour le ML

1. Lit `s3a://nyc-yellow-tripdata/raw/yellow_tripdata_YYYY-MM.parquet`
2. Filtre : `trip_distance > 0`, `passenger_count > 0`, `total_amount >= 0`, `dropoff > pickup`
3. Renomme les colonnes (ex: `VendorID` → `vendor_id`)
4. Écrit le Parquet nettoyé dans `s3a://nyc-yellow-tripdata/cleaned/yellow_tripdata_YYYY-MM/`

### Branche 2 — Insertion dans le Data Warehouse

1. Renomme les colonnes pour correspondre au schéma `fact_trips`
2. Filtre les valeurs FK invalides (vendor_id, payment_type_id, rate_code_id, location_id)
3. Filtre les valeurs numériques hors limites (DECIMAL(10,2) max = 99 999 999.99)
4. Insère dans PostgreSQL en mode `Append` avec `repartition(4)` pour paralléliser

## Stack technique

| Composant       | Version       |
|-----------------|---------------|
| Scala           | 2.13.17       |
| Apache Spark    | 3.5.5         |
| Hadoop AWS      | 3.3.4         |
| PostgreSQL JDBC | 42.6.0        |
| MinIO SDK       | 8.5.7         |

## Prérequis

- **SBT** installé
- **MinIO**, **PostgreSQL** et **Spark** lancés :

```sh
sudo docker-compose up -d
```

- Les données brutes doivent être dans MinIO (résultat de l'ex01)
- Les tables de dimension doivent exister dans PostgreSQL (résultat de l'ex03)

## Lancement

```sh
cd ex02_data_ingestion
sbt run
```

### Avec arguments

```sh
sbt "run --start 2022-01 --end 2022-12"
```

### Avec variables d'environnement

```sh
START_DATE=2022-01 END_DATE=2022-12 sbt run
```

## Vérification

### Parquets nettoyés dans MinIO

Console MinIO ([http://localhost:9001](http://localhost:9001)) → bucket `nyc-yellow-tripdata/cleaned/`

### Données dans PostgreSQL

```sh
sudo docker exec -it postgres psql -U postgres -d bigdata_db
```

```sql
-- Nombre total de trajets
SELECT COUNT(*) FROM fact_trips;

-- Répartition par mois
SELECT to_char(tpep_pickup_datetime, 'YYYY-MM') AS mois, COUNT(*)
FROM fact_trips
GROUP BY 1 ORDER BY 1;

-- CA par vendeur
SELECT v.vendor_name, COUNT(*) AS trajets, SUM(f.total_amount) AS ca
FROM fact_trips f
JOIN dim_vendor v ON f.vendor_id = v.vendor_id
GROUP BY 1 ORDER BY ca DESC;
```

## Structure du dossier

```
ex02_data_ingestion/
├── build.sbt              → dépendances SBT (Spark, Hadoop, PostgreSQL)
├── project/
│   └── build.properties   → version SBT
├── src/main/scala/
│   └── SparkApp.scala     → programme Spark principal
└── README.md
```

## Notes techniques

- Spark tourne en mode `local[*]` (pas de cluster nécessaire)
- Le traitement est séquentiel par mois pour limiter l'utilisation mémoire
