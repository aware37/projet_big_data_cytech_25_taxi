# Exercice 4 — Dashboard analytique (Streamlit)

## Objectif

Créer un **dashboard interactif** pour explorer et visualiser les données des courses de taxi NYC Yellow stockées dans PostgreSQL.

## Stack technique

| Composant  | Rôle                         |
|------------|-------------------------------|
| Streamlit  | Framework web interactif     |
| Plotly     | Graphiques interactifs       |
| psycopg2   | Connexion PostgreSQL         |
| pandas     | Manipulation des données     |

## Prérequis

- **PostgreSQL** lancé avec les données ingérées (ex02)
- Dépendances installées via `uv` (depuis la racine du projet)

```sh
uv sync
```

## Lancement

Depuis la racine du projet :

```sh
cd ex04_dashboard
uv run streamlit run app.py
```

Le dashboard s'ouvre sur [http://localhost:8501](http://localhost:8501) 🚕

## Sections du dashboard

| #  | Section                           | Type de graphique        |
|----|------------------------------------|--------------------------| 
| 1  | KPIs globaux                      | Métriques (courses, CA, panier moyen, distance, tip) |
| 2  | CA par jour                       | Area chart              |
| 3  | Distribution horaire des courses  | Bar chart               |
| 4  | Top 10 zones de pickup            | Bar chart horizontal    |
| 5  | Répartition des paiements         | Donut chart             |
| 6  | CA & courses par vendor           | Double axe (bar + scatter) |
| 7  | Tarif moyen par tranche distance  | Bar chart coloré        |
| 8  | Heatmap jour × heure              | Heatmap (imshow)        |
| 9  | Top 10 zones de dropoff           | Bar chart horizontal    |
| 10 | Comparaison mensuelle             | 3 bar charts            |
| 11 | Échantillon de trajets            | Tableau (50 lignes)     |

## Filtres

Le sidebar permet de **filtrer par mois** (multi-sélection). Toutes les visualisations se mettent à jour dynamiquement.

## Configuration de la base

La connexion PostgreSQL est gérée dans `db.py` via variables d'environnement :

| Variable     | Défaut       |
|-------------|--------------|
| `PGHOST`    | `localhost`  |
| `PGPORT`    | `5432`       |
| `PGDATABASE`| `bigdata_db` |
| `PGUSER`    | `postgres`   |
| `PGPASSWORD`| `postgres`   |

## Structure du dossier

```
ex04_dashboard/
├── app.py      → application Streamlit (466 lignes, 11 sections)
├── db.py       → connexion PostgreSQL + helper read_sql()
└── README.md
```
