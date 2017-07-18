from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext, SparkSession
from cassandra.cluster import Cluster


def initEnvironment():
    global sc, sql
    try:
        conf = SparkConf()
        #conf.setMaster("spark://192.168.246.236:7077")
        conf.setMaster("local[*]")
        conf.setAppName("Earthquakes Quandrants parser")
        conf.set("spark.cassandra.connection.host", "192.168.246.236")
        #conf.set("spark.executor.memory", "10g")
        #conf.set("spark.num.executors", "1")

        sc = SparkContext(conf=conf)
        sql = SQLContext(sc)
        spark = SparkSession(sc)

        print("SparkContext => ", sc)
        print("SQLContext => ", sql)
    except:
        sc.stop()


def getX(longitude):
    print("\t Longitude:" + str(longitude))
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
    elif 150 <= longitude <= 180:
        x = 6
    elif -180 <= longitude < -150:
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
    print("\t Quadrant x:" + str(x))
    return x


def getY(latitude):
    print("\t Latitude:" + str(latitude))
    y = 0

    if 60 <= latitude < 80:
        y = 1
    elif 40 <= latitude < 60:
        y = 2
    elif 20 <= latitude < 40:
        y = 3
    elif 0 <= latitude < 20:
        y = 4
    elif -20 <= latitude < 0:
        y = 5
    elif -40 <= latitude < -20:
        y = 6
    elif -60 <= latitude < -40:
        y = 7
    elif -80 <= latitude < -60:
        y = 8
    elif latitude < -80:
        y = 8
    elif 80 <= latitude:
        y = 1
  
    print("\t Quadrant y:" + str(y))
    return y



def parseQuadrant():
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")

    earthquakes = sql.read.format("org.apache.spark.sql.cassandra").load(keyspace="dev", table="earthquake")
    earthquakesFiltered = earthquakes.select("eventId","latitude","longitude")
    earthquakesFiltered.show()
    pandas_df = earthquakesFiltered.toPandas()
    
    earthquakeCounter = 1
    for index, row in pandas_df.iterrows():
        print("Parsing earthquake #" + str(earthquakeCounter))
        x = getX(float(row['longitude']))
        y = getY(float(row['latitude']))
        if x==0 or y==0:
            print (x,y)
            break

        quadrantXY = str(x)+","+str(y)

        session.execute("UPDATE Earthquake SET \"quadrant\" = %s, \"quadrantX\" = %s, \"quadrantY\" = %s WHERE \"eventId\"='"+row['eventId']+"'",(str(quadrantXY),int(x),int(y)))
        #session.execute("UPDATE Earthquake SET \"quadrantX\" = %s WHERE \"eventId\"='"+row['eventId']+"'",(x,))
        #session.execute("UPDATE Earthquake SET \"quadrantY\" = %s WHERE \"eventId\"='"+row['eventId']+"'",(y,))
        earthquakeCounter += 1

    earthquakesResultant = earthquakes.select("eventId","latitude","longitude","quadrant","quadrantX","quadrantY")
    earthquakesResultant.show()


if __name__ == "__main__":
    initEnvironment()
    parseQuadrant()
