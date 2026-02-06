import io.minio.{MinioClient, PutObjectArgs, MakeBucketArgs, BucketExistsArgs, UploadObjectArgs}
import scala.io.StdIn
import java.io.ByteArrayInputStream

object Main extends App {

    val endpoint = "http://localhost:9000"
    val accessKey = "minio"
    val secretKey = "minio123"
    val bucketName = "nyc-yellow-tripdata"
    val rawFolder = "raw"

    val minioClient = MinioClient.builder()
        .endpoint(endpoint)
        .credentials(accessKey, secretKey)
        .build()

    val bucketExists = minioClient.bucketExists(
        BucketExistsArgs.builder()
            .bucket(bucketName)
            .build()
    )
    
    if (!bucketExists) {
        minioClient.makeBucket(
            MakeBucketArgs.builder()
                .bucket(bucketName)
                .build()
        )
        println(s"Bucket '$bucketName' créé.")
    } else {
        println(s"Bucket '$bucketName' existe déjà.")
    }

    createFolder(rawFolder)

    val argsMap = args.sliding(2, 2).collect {
        case Array(k, v) => k -> v
    }.toMap

    val startDate = readValue("--start", "START_DATE", "Date de début (YYYY-MM): ")
    val endDate = readValue("--end", "END_DATE", "Date de fin (YYYY-MM): ")

    if (!isValidDate(startDate) || !isValidDate(endDate)) {
        println("Format invalide. Utilisez YYYY-MM")
        System.exit(1)
    }

    val months = generateMonths(startDate, endDate)
    
    if (months.isEmpty) {
        println("Aucun mois trouvé. Vérifiez les dates.")
        System.exit(1)
    }

    println(s"Téléchargement de ${months.size} mois: ${months.mkString(", ")}\n")

    months.foreach { month =>
        downloadAndUpload(month)
    }

    println("Téléchargement terminé!")

    def readValue(argKey: String, envKey: String, prompt: String): String = {
        val value = argsMap.get(argKey)
            .orElse(sys.env.get(envKey))
            .getOrElse({
                print(prompt)
                StdIn.readLine()
            })
        value.trim.replaceAll("[^0-9-]", "")
    }

    def createFolder(folderName: String): Unit = {
        try {
            val emptyContent = new ByteArrayInputStream(Array[Byte]())
            minioClient.putObject(
                PutObjectArgs.builder()
                    .bucket(bucketName)
                    .`object`(s"$folderName/.gitkeep")
                    .stream(emptyContent, 0, 1)
                    .contentType("application/octet-stream")
                    .build()
            )
            println(s"Dossier '$folderName' créé.")
        } catch {
            case e: Exception =>
                println(s"Dossier existe ou erreur: ${e.getMessage}")
        }
    }

    def isValidDate(date: String): Boolean = {
        date.matches("\\d{4}-\\d{2}")
    }

    def generateMonths(start: String, end: String): List[String] = {
        val startYear = start.substring(0, 4).toInt
        val startMonth = start.substring(5, 7).toInt
        val endYear = end.substring(0, 4).toInt
        val endMonth = end.substring(5, 7).toInt

        var months = scala.collection.mutable.ListBuffer[String]()
        var currentYear = startYear
        var currentMonth = startMonth

        while (currentYear < endYear || (currentYear == endYear && currentMonth <= endMonth)) {
            months += f"$currentYear%04d-$currentMonth%02d"
            currentMonth += 1
            if (currentMonth > 12) {
                currentMonth = 1
                currentYear += 1
            }
        }

        months.toList
    }

    def downloadAndUpload(month: String): Unit = {
        val fileURL = s"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_$month.parquet"
        val objectName = s"$rawFolder/yellow_tripdata_$month.parquet"

        try {
            println(s"Téléchargement: $month")
            println(s"  URL: $fileURL")

            // Télécharger dans un fichier temporaire d'abord
            val tempFile = java.io.File.createTempFile("yellow_tripdata_", ".parquet")
            tempFile.deleteOnExit()

            val url = new java.net.URL(fileURL)
            val connection = url.openConnection().asInstanceOf[java.net.HttpURLConnection]
            connection.setConnectTimeout(30000)
            connection.setReadTimeout(300000) // 5 minutes
            connection.setRequestProperty("User-Agent", "Mozilla/5.0")

            val responseCode = connection.getResponseCode
            if (responseCode != 200) {
                println(s"  Erreur HTTP $responseCode pour $month")
                return
            }

            val contentLength = connection.getContentLengthLong
            println(s"  Taille: ${if (contentLength > 0) s"${contentLength / (1024*1024)} Mo" else "inconnue"}")

            val inputStream = connection.getInputStream
            val outputStream = new java.io.FileOutputStream(tempFile)
            val buffer = new Array[Byte](8 * 1024 * 1024) // 8 Mo
            var bytesRead = 0
            var totalBytes = 0L

            bytesRead = inputStream.read(buffer)
            while (bytesRead != -1) {
                outputStream.write(buffer, 0, bytesRead)
                totalBytes += bytesRead
                val currentMb = totalBytes / (1024*1024)
                val prevMb = (totalBytes - bytesRead) / (1024*1024)
                if (currentMb > prevMb && currentMb % 10 == 0) {
                    println(s"  ... $currentMb Mo téléchargés")
                }
                bytesRead = inputStream.read(buffer)
            }

            outputStream.close()
            inputStream.close()
            connection.disconnect()

            println(s"  Téléchargé: ${totalBytes / (1024*1024)} Mo → ${tempFile.getAbsolutePath}")

            // Upload vers MinIO depuis le fichier local
            import io.minio.UploadObjectArgs
            minioClient.uploadObject(
                UploadObjectArgs.builder()
                    .bucket(bucketName)
                    .`object`(objectName)
                    .filename(tempFile.getAbsolutePath)
                    .contentType("application/octet-stream")
                    .build()
            )

            tempFile.delete()
            println(s"Uploadé dans MinIO: $objectName")

        } catch {
            case e: Exception =>
                println(s"Erreur pour $month: ${e.getMessage}")
                e.printStackTrace()
        }
    }
}