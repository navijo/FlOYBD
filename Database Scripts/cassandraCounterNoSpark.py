from cassandra.cluster import Cluster
from cassandra.query import named_tuple_factory
import time

cluster = Cluster(['192.168.246.236'])
session = cluster.connect("dev")
session.row_factory = named_tuple_factory

print("Start...")
start_time = time.time()
daily = session.execute("Select count(*) from daily_measurement;",timeout=100000)
clean_daily = session.execute("Select count(*) from clean_daily_measurement;",timeout=100000)
monthly = session.execute("Select count(*) from monthly_measurement;",timeout=100000)
stations = session.execute("Select count(*) from station;",timeout=100000)
earthquakes = session.execute("Select count(*) from earthquake;",timeout=100000)
stations_limits = session.execute("Select count(*) from station_limits;",timeout=100000)

print ("Daily Normal:",daily[0])
print ("Daily Clean:",clean_daily[0])
print ("Monthly:",monthly[0])
print ("Stations:",stations[0])
print ("Stations Limits:",stations_limits[0])
print ("Earthquakes:",earthquakes[0])
print("--- %s seconds ---" % (time.time() - start_time))

