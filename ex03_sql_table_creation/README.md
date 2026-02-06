# Exercice 3 — Création des tables SQL (Star Schema)

## Objectif

Mettre en place un **schéma en étoile** (star schema) dans PostgreSQL pour stocker les données des courses de taxi NYC Yellow de manière structurée et optimisée pour l'analyse.

## Schéma de la base de données

```
                    ┌──────────────┐
                    │  dim_vendor  │
                    │──────────────│
                    │ vendor_id PK │
                    │ vendor_name  │
                    └──────┬───────┘
                           │
┌────────────────┐   ┌─────┴──────────────────────┐   ┌──────────────────┐
│  dim_location  │   │        fact_trips           │   │ dim_payment_type │
│────────────────│   │─────────────────────────────│   │──────────────────│
│ location_id PK │◄──│ trip_id PK (SERIAL)         │──►│ payment_type_id  │
│ borough        │   │ vendor_id FK                │   │ payment_name     │
│ zone           │   │ rate_code_id FK             │   └──────────────────┘
│ service_zone   │   │ payment_type_id FK          │
└────────────────┘   │ pu_location_id FK           │   ┌──────────────────┐
                     │ do_location_id FK           │──►│  dim_rate_code   │
                     │ tpep_pickup_datetime        │   │──────────────────│
                     │ tpep_dropoff_datetime       │   │ rate_code_id PK  │
                     │ passenger_count             │   │ rate_description │
                     │ trip_distance DECIMAL(10,2)  │   └──────────────────┘
                     │ fare_amount DECIMAL(10,2)    │
                     │ tip_amount DECIMAL(10,2)     │
                     │ total_amount DECIMAL(10,2)   │
                     │ ...                         │
                     └─────────────────────────────┘
```

## Tables de dimension

| Table              | Description                                   | Source                     |
|--------------------|-----------------------------------------------|----------------------------|
| `dim_vendor`       | Compagnies de taxi (CMT, Curb, Uber, etc.)    | insertion.sql              |
| `dim_payment_type` | Modes de paiement (CB, cash, dispute, etc.)   | insertion.sql              |
| `dim_rate_code`    | Tarifs (standard, JFK, Newark, etc.)          | insertion.sql              |
| `dim_location`     | 265 zones NYC (borough, zone, service_zone)   | taxi_zone_lookup.csv (COPY)|

## Table de faits

| Table        | Description                                     | Volume attendu       |
|--------------|--------------------------------------------------|----------------------|
| `fact_trips` | Courses de taxi avec clés étrangères + montants | ~3-4M lignes / mois  |

## Fichiers

| Fichier        | Rôle                                                        |
|----------------|--------------------------------------------------------------|
| `creation.sql` | DDL : `DROP` + `CREATE TABLE` + index de performance         |
| `insertion.sql`| DML : `INSERT` dimensions + `COPY` dim_location depuis CSV  |

## Fonctionnement automatique

Les scripts SQL sont **exécutés automatiquement** au premier lancement du conteneur PostgreSQL grâce au montage Docker :

```yaml
# docker-compose.yml
volumes:
  - ./ex03_sql_table_creation:/docker-entrypoint-initdb.d
  - ./data/raw:/tmp    # pour taxi_zone_lookup.csv
```

PostgreSQL exécute dans l'ordre alphabétique :
1. `creation.sql` → crée les tables
2. `insertion.sql` → insère les données de dimension

## Exécution manuelle (si besoin)

Si la base a déjà été initialisée et qu'on veut recréer les tables :

```sh
# Copier le CSV dans le conteneur
sudo docker cp data/raw/taxi_zone_lookup.csv postgres:/tmp/taxi_zone_lookup.csv

# Exécuter les scripts
sudo docker exec -it postgres psql -U postgres -d bigdata_db -f /docker-entrypoint-initdb.d/creation.sql
sudo docker exec -it postgres psql -U postgres -d bigdata_db -f /docker-entrypoint-initdb.d/insertion.sql
```

## Vérification

```sh
sudo docker exec -it postgres psql -U postgres -d bigdata_db
```

```sql
SELECT COUNT(*) FROM dim_location;      -- 265 zones
SELECT COUNT(*) FROM dim_vendor;        -- 5 vendeurs
SELECT COUNT(*) FROM dim_payment_type;  -- 7 types
SELECT COUNT(*) FROM dim_rate_code;     -- 7 codes
```

## Index de performance

Des index sont créés sur les colonnes fréquemment filtrées ou jointes :

- `tpep_pickup_datetime` — filtres temporels
- `vendor_id`, `rate_code_id`, `payment_type_id` — jointures dimensions
- `pu_location_id`, `do_location_id` — analyses géographiques
