import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import java.util.Properties
import org.apache.spark.sql.SaveMode
import java.time.YearMonth
import scala.io.StdIn

object SparkApp extends App {

  val argsMap = args.sliding(2, 2).collect { case Array(k, v) => k -> v }.toMap

  def readValue(argKey: String, envKey: String, prompt: String): String = {
    argsMap.get(argKey)
      .orElse(sys.env.get(envKey))
      .getOrElse { print(prompt); StdIn.readLine() }
      .trim
  }

  def generateMonths(start: String, end: String): Seq[String] = {
    var current = YearMonth.parse(start)
    val last    = YearMonth.parse(end)
    val buf     = scala.collection.mutable.ArrayBuffer[String]()
    while (!current.isAfter(last)) { buf += current.toString; current = current.plusMonths(1) }
    buf.toSeq
  }

  val startDate = readValue("--start", "START_DATE", "Date de début (YYYY-MM): ")
  val endDate   = readValue("--end",   "END_DATE",   "Date de fin   (YYYY-MM): ")
  val months    = generateMonths(startDate, endDate)

  println(s"Traitement de ${months.size} mois: ${months.mkString(", ")}\n")

  val spark = SparkSession.builder()
    .appName("SparkApp")
    .master("local[*]")
    .config("spark.hadoop.fs.s3a.access.key", "minio")
    .config("spark.hadoop.fs.s3a.secret.key", "minio123")
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000/")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3a.attempts.maximum", "1")
    .config("spark.hadoop.fs.s3a.connection.establish.timeout", "6000")
    .config("spark.hadoop.fs.s3a.connection.timeout", "5000")
    .getOrCreate()
  spark.sparkContext.setLogLevel("WARN")

  val postgresUrl = "jdbc:postgresql://localhost:5432/bigdata_db"
  val dbProps = new Properties()
  dbProps.put("user", "postgres")
  dbProps.put("password", "postgres")
  dbProps.put("driver", "org.postgresql.Driver")
  dbProps.put("batchsize", "10000")
  dbProps.put("reWriteBatchedInserts", "true")

  months.foreach { month =>
    println(s"═══ Mois: $month ═══")
    val t0 = System.currentTimeMillis()

    val inputPath = s"s3a://nyc-yellow-tripdata/raw/yellow_tripdata_$month.parquet"
    val parquetFileDF = spark.read.parquet(inputPath)
    val rowCount = parquetFileDF.count()
    println(s"  Lignes lues : $rowCount")

    // Branche 1 : nettoyage + upload vers MinIO
    val mlDF = parquetFileDF
      .filter(col("trip_distance") > 0.0)
      .filter(col("passenger_count") > 0)
      .filter(col("total_amount") >= 0.0)
      .withColumn("tpep_pickup_datetime", col("tpep_pickup_datetime").cast("timestamp"))
      .withColumn("tpep_dropoff_datetime", col("tpep_dropoff_datetime").cast("timestamp"))
      .filter(col("tpep_dropoff_datetime") > col("tpep_pickup_datetime"))
      .withColumnRenamed("VendorID", "vendor_id")
      .withColumnRenamed("RatecodeID", "rate_code_id")
      .withColumnRenamed("PULocationID", "pu_location_id")
      .withColumnRenamed("DOLocationID", "do_location_id")
      .withColumnRenamed("payment_type", "payment_type_id")
      .withColumnRenamed("Airport_fee", "airport_fee")

    val outputPath = s"s3a://nyc-yellow-tripdata/cleaned/yellow_tripdata_$month"
    mlDF.write.mode(SaveMode.Overwrite).parquet(outputPath)
    println(s"  [Branche 1] Cleaned → MinIO  (${mlDF.count()} lignes)")

    // Branche 2 : filtrage + upload vers PostgreSQL
    val dwDF = parquetFileDF
      .withColumnRenamed("VendorID", "vendor_id")
      .withColumnRenamed("RatecodeID", "rate_code_id")
      .withColumnRenamed("PULocationID", "pu_location_id")
      .withColumnRenamed("DOLocationID", "do_location_id")
      .withColumnRenamed("payment_type", "payment_type_id")
      .withColumnRenamed("Airport_fee", "airport_fee")
      .withColumnRenamed("cbd_congestion_fee", "cbd_congestion_fee")
      // Filter valid FK values
      .filter(col("vendor_id").isin(1, 2, 5, 6, 7) || col("vendor_id").isNull)
      .filter(col("payment_type_id").between(0, 6) || col("payment_type_id").isNull)
      .filter(col("rate_code_id").isin(1, 2, 3, 4, 5, 6, 99) || col("rate_code_id").isNull)
      .filter(col("pu_location_id").between(1, 265) || col("pu_location_id").isNull)
      .filter(col("do_location_id").between(1, 265) || col("do_location_id").isNull)
      // Filter numeric overflow (DECIMAL(10,2) max = 99999999.99)
      .filter(abs(col("fare_amount")) < 1e8 || col("fare_amount").isNull)
      .filter(abs(col("total_amount")) < 1e8 || col("total_amount").isNull)
      .filter(abs(col("tip_amount")) < 1e8 || col("tip_amount").isNull)
      .filter(abs(col("tolls_amount")) < 1e8 || col("tolls_amount").isNull)
      .filter(abs(col("trip_distance")) < 1e8 || col("trip_distance").isNull)

    val dwCount = dwDF.count()
    println(s"  Insertion PostgreSQL en cours ($dwCount lignes après filtrage)...")
    dwDF.repartition(4).write.mode(SaveMode.Append).jdbc(postgresUrl, "fact_trips", dbProps)

    val elapsed = (System.currentTimeMillis() - t0) / 1000
    println(s"  [Branche 2] fact_trips → Postgres (${rowCount} lignes)")
    println(s"$month terminé en ${elapsed}s\n")
  }

  println(s"Traitement terminé pour ${months.size} mois !")
  spark.stop()

}

