# Exercice 1 — Récupération des données (Data Retrieval)

## Objectif

Télécharger les fichiers **Parquet** du dataset [NYC Yellow Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) depuis le site officiel de la TLC et les stocker dans **MinIO** (stockage S3-compatible).

## Fonctionnement

Le programme Scala :

1. Se connecte à MinIO et crée le bucket `nyc-yellow-tripdata` s'il n'existe pas
2. Crée un dossier `raw/` dans le bucket
3. Demande une plage de mois (début → fin au format `YYYY-MM`)
4. Pour chaque mois, télécharge le fichier Parquet depuis `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet`
5. Upload le fichier dans `s3://nyc-yellow-tripdata/raw/yellow_tripdata_YYYY-MM.parquet`

## Stack technique

| Composant      | Version       |
|----------------|---------------|
| Scala          | 2.13.17       |
| SBT            | 1.x           |
| MinIO SDK      | 8.5.7         |
| requests (HTTP)| 0.8.0         |

## Prérequis

- **SBT** installé
- **MinIO** lancé via Docker Compose (voir racine du projet)

```sh
sudo docker-compose up -d minio
```

## Lancement

```sh
cd ex01_data_retrieval
sbt run
```

Le programme demande interactivement les dates de début et fin.

### Avec arguments (non-interactif)

```sh
sbt "run --start 2022-01 --end 2022-12"
```

### Avec variables d'environnement

```sh
START_DATE=2022-01 END_DATE=2022-12 sbt run
```

## Vérification

Ouvrir la console MinIO : [http://localhost:9001](http://localhost:9001)

- Login : `minio` / `minio123`
- Naviguer dans le bucket `nyc-yellow-tripdata/raw/`
- Les fichiers `yellow_tripdata_YYYY-MM.parquet` doivent être présents

## Structure du dossier

```
ex01_data_retrieval/
├── build.sbt              → dépendances SBT
├── project/
│   └── build.properties   → version SBT
├── src/main/scala/
│   └── Main.scala         → programme principal
└── README.md
```
