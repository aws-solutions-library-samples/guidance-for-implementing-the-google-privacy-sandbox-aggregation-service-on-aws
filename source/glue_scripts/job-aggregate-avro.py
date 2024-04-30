import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import DataFrame, Row
import datetime
from awsglue import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME','table','databucket','gluetablename','gluedatabasename','kds_stream_arn','kds_stream_name','windowSize'])
gluetablename=str(args['gluetablename'])
table=str(args['table'])
databucket= str(args['databucket'])
gluedatabasename=str(args['gluedatabasename'])
kds_stream_arn=str(args['kds_stream_arn'])
kds_stream_name=str(args['kds_stream_name'])
window_size=str(args['windowSize'])
path = f"s3://{databucket}/{gluetablename}"

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Amazon Kinesis-AVRO
dataframe_AmazonKinesisAVRO_node1709430408206 = glueContext.create_data_frame.from_options(
    connection_type="kinesis",
    connection_options={
        "typeOfData": "kinesis",
        "streamARN": kds_stream_arn,
        "streamName": kds_stream_name,
        "classification": "json",
        "startingPosition": "earliest",
        "inferSchema": "true",
    },
    transformation_ctx="dataframe_AmazonKinesisAVRO_node1709430408206",
)


def processBatch(data_frame, batchId):
    if data_frame.count() > 0:
        AmazonKinesisAVRO_node1709430408206 = DynamicFrame.fromDF(
            data_frame, glueContext, "from_data_frame"
        )
        
        
        # fix for 0 byte files saved to s3
        # Repartition the DynamicFrame to a single partition
        AmazonKinesisAVRO_node1709430408206_dataframe = AmazonKinesisAVRO_node1709430408206.toDF().repartition(1)

        # Convert back to a DynamicFrame for further processing
        AmazonKinesisAVRO_node1709430408206 = DynamicFrame.fromDF(
            AmazonKinesisAVRO_node1709430408206_dataframe, glueContext, "from_data_frame"
        )
        
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour

        # Script generated for node Amazon S3-AVRO
        AmazonS3AVRO_node1709431836943_path = (
            path
            + "/ingest_year="
            + "{:0>4}".format(str(year))
            + "/ingest_month="
            + "{:0>2}".format(str(month))
            + "/ingest_day="
            + "{:0>2}".format(str(day))
            + "/ingest_hour="
            + "{:0>2}".format(str(hour))
            + "/"
        )
        AmazonS3AVRO_node1709431836943 = glueContext.write_dynamic_frame.from_options(
            frame=AmazonKinesisAVRO_node1709430408206,
            connection_type="s3",
            format="avro",
            connection_options={
                "path": AmazonS3AVRO_node1709431836943_path,
                "partitionKeys": [],
            },
            format_options={"compression": "gzip"},
            transformation_ctx="AmazonS3AVRO_node1709431836943",
        )


glueContext.forEachBatch(
    frame=dataframe_AmazonKinesisAVRO_node1709430408206,
    batch_function=processBatch,
    options={
        "windowSize": window_size,
        "checkpointLocation": args["TempDir"] + "/" + args["JOB_NAME"] + "/checkpoint/",
    },
)
job.commit()
