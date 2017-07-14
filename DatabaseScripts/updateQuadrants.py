from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext, SparkSession
from cassandra.cluster import Cluster


def initEnvironment():
    global sc, sql
    try:
        conf = SparkConf()
        conf.setMaster("spark://192.168.246.236:7077")
        #conf.setMaster("local[*]")
        conf.setAppName("Earthquakes Quandrants parser")
        conf.set("spark.cassandra.connection.host", "192.168.246.236")
        conf.set("spark.executor.memory", "10g")
        conf.set("spark.num.executors", "2")

        sc = SparkContext(conf=conf)
        sql = SQLContext(sc)
        spark = SparkSession(sc)

        print("SparkContext => ", sc)
        print("SQLContext => ", sql)
    except:
        sc.stop()
        initEnvironment()


def getX(longitude):
    x = 0

    if 0 <= longitude < 30:
        x = 1
    elif 30 <= longitude < 60:
        x = 2
    elif 60 <= longitude < 90:
        x = 3
    elif 90 <= longitude < 120:
        x = 4
    elif 120 <= longitude < 150:
        x = 5
    elif 150 <= longitude < 180:
        x = 6
    elif -179 <= longitude < -150:
        x = 7
    elif -150 <= longitude < -120:
        x = 8
    elif -120 <= longitude < -90:
        x = 9
    elif -90 <= longitude < -60:
        x = 10
    elif -60 <= longitude < -30:
        x = 11
    elif -30 <= longitude < 0:
        x = 12

    return x


def getY(latitude):
    y = 0

    if 80 <= latitude < 60:
        y = 1
    elif 60 <= latitude < 40:
        y = 2
    elif 40 <= latitude < 20:
        y = 3
    elif 20 <= latitude < 0:
        y = 4
    elif 0 <= latitude < -20:
        y = 5
    elif -20 <= latitude < -40:
        y = 6
    elif -40 <= latitude < -60:
        y = 7
    elif -60 <= latitude < -80:
        y = 8

    return y


def parseQuadrant():
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")

    earthquakes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="earthquake")

    for earthquake in earthquakes:
        x = getX(earthquake.longitude)
        y = getY(earthquake.latitude)

        quadrantXY = str(x)+","+str(y)

        session.execute("UPDATE Earthquake SET \"quadrant\" = '%s' WHERE \"eventId\"=\""+earthquake.eventId+"\"",
                        [str(quadrantXY)])


if __name__ == "__main__":
    initEnvironment()
    parseQuadrant()
