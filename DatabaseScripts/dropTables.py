from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1','192.168.246.236'])
session = cluster.connect("dev")

#session.execute("DROP TABLE Station")
session.execute("DROP TABLE Station_limits")
#session.execute("DROP TABLE Monthly_Measurement")
#session.execute("DROP TABLE Daily_Measurement")
#session.execute("DROP TABLE Reservoir")
#session.execute("DROP TABLE Earthquake")
#session.execute("DROP TABLE Station_Regression_Prediction")
#session.execute("DROP TABLE Station_Naive_Bayes_Prediction")
#session.execute("DROP TABLE api_key")
#session.execute("DROP TABLE linear_model")

