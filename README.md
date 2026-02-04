# Projet Big Data Cytech 25
Pour l'instant voici les exercices finis :
- ex01_data_retrieval
- ex02_data_ingestion (en cours)
- ex03_sql_table_creation

## Prérequis

- Docker et Docker Compose installés
- SBT installé

---

## 1. Lancer l’infrastructure

À la racine du projet, lance :

```sh
sudo docker-compose up -d
```

Cela démarre :
- MinIO (stockage)
- PostgreSQL (base de données)
- Spark

---

## 2. Configurer MinIO

1. Ouvre [http://localhost:9000](http://localhost:9000) dans ton navigateur.
2. Connecte-toi avec :
   - **Identifiant** : `minio`
   - **Mot de passe** : `minio123`
3. Crée un bucket nommé :  
   ```
   nyc-yellow-tripdata
   ```

---

## 3. Télécharger et envoyer les données sur MinIO

Dans le dossier `ex01_data_retrieval` :

```sh
cd ex01_data_retrieval
sbt run
```

Cela télécharge le fichier Parquet et l’upload automatiquement dans le bucket MinIO.

---

## 4. Vérifier la base de données PostgreSQL

Reviens à la racine du projet, puis connecte-toi à la base :

```sh
sudo docker exec -it postgres psql -U postgres -d bigdata_db
```

### Tester les tables de dimension

Exécute les requêtes suivantes dans le client `psql` :

```sql
-- Nombre d’emplacements importés
SELECT count(*) FROM dim_location;

-- Afficher quelques emplacements
SELECT * FROM dim_location LIMIT 5;

-- Afficher quelques vendeurs
SELECT * FROM dim_vendor LIMIT 5;

-- Afficher quelques types de paiement
SELECT * FROM dim_payment_type LIMIT 5;

-- Afficher quelques codes tarifaires
SELECT * FROM dim_rate_code LIMIT 5;
```

Pour quitter `psql` :

```
\q
```

---

**Résumé des commandes principales** :

```sh
sudo docker-compose up -d
# Aller sur http://localhost:9000 et créer le bucket
cd ex01_data_retrieval
sbt run
cd ..
sudo docker exec -it postgres psql -U postgres -d bigdata_db
# (puis requêtes SQL ci-dessus)
```

---


Le code minimal pour faire fonctionner un code avec Minio :
```scala
import org.apache.spark.sql.{SparkSession, DataFrame}

object SparkApp extends App {
  val spark = SparkSession.builder()
    .appName("SparkApp")
    .master("local")
    .config("fs.s3a.access.key", "minio")
    .config("fs.s3a.secret.key", "minio123")
    .config("fs.s3a.endpoint", "http://localhost:9000/") // A changer lors du déploiement
    .config("fs.s3a.path.style.access", "true")
    .config("fs.s3a.connection.ssl.enable", "false")
    .config("fs.s3a.attempts.maximum", "1")
    .config("fs.s3a.connection.establish.timeout", "6000")
    .config("fs.s3a.connection.timeout", "5000")
    .getOrCreate()
  spark.sparkContext.setLogLevel("WARN")

}
```

## Modalités de rendu

1. Pull Request vers la branch `master`
2. Dépot du rapport et du code source zippé dans cours.cyu.fr (Les accès seront bientôt ouverts)

Date limite de rendu : 7 février 2026