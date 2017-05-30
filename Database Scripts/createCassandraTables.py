import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from datetime import datetime
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.models import Model

#Api Key
class Api_key(Model):
    creation_date      = columns.DateTime(primary_key=True)
    apiKey             = columns.Text(primary_key=True)
    valid_until        = columns.DateTime(required=False)


#Station Model
class Station(Model):
    station_id		= columns.Text(primary_key=True)
    name			= columns.Text(index=True)
    latitude		= columns.Text(required=True)
    longitude		= columns.Text(required=True)
    altitude		= columns.Integer(required=True)
    indsinop		= columns.Text(required=True)
    province		= columns.Text(required=True)

#Measurement Model for monthly values
class Monthly_Measurement(Model):
#    measurement_id			= columns.Text(primary_key=True)
    station_id				= columns.Text(primary_key=True,required=True) #indicativo
    measure_date			= columns.DateTime(primary_key=True,required=True) #fecha
    steam_press				= columns.Decimal(required=False) #e
    evap					= columns.Decimal(required=False) #evap
    relative_humidity		= columns.Decimal(required=False) #hr
    insolation_hours 		= columns.Decimal(required=False) #inso
    covered_days 			= columns.Decimal(required=False) #n_cub
    clear_days 				= columns.Decimal(required=False) #n_des
    foggy_days				= columns.Decimal(required=False) #n_fog
    hail_days 				= columns.Decimal(required=False) #n_gra
    rain_days 				= columns.Decimal(required=False) #n_llu
    snow_days				= columns.Decimal(required=False) #n_nie
    cloud_days 				= columns.Decimal(required=False) #n_nub
    storm_days 				= columns.Decimal(required=False) #n_tor
    rain_over_01mm			= columns.Decimal(required=False) #np_001
    rain_over_1mm			= columns.Decimal(required=False) #np_010
    rain_over_10mm			= columns.Decimal(required=False) #np_100
    rain_over_30mm			= columns.Decimal(required=False) #np_300
    temp_under_0			= columns.Decimal(required=False) #nt_00
    temp_over_30			= columns.Decimal(required=False) #nt_30
    visibility_under_50m	= columns.Decimal(required=False) #nv_0050
    visibility_under_100m	= columns.Decimal(required=False) #nv_0100
    visibility_under_1000m	= columns.Decimal(required=False) #nv_01000
    wind_over_55km			= columns.Decimal(required=False) #nw_55
    wind_over_91km			= columns.Decimal(required=False) #nw_91
    max_daily_rain			= columns.Text(required=False) #p_max
    total_monthly_rain		= columns.Text(required=False) #p_mes
    month_percent_insol		= columns.Text(required=False) #p_sol
    sea_lvl_pressure_med 	= columns.Text(required=False) #q_mar
    max_abs_pressure		= columns.Text(required=False) #q_max
    med_abs_pressure		= columns.Text(required=False) #q_med
    min_abs_pressure		= columns.Text(required=False) #q_min
    max_abs_temperature		= columns.Text(required=False) #ta_max
    min_abs_temperature		= columns.Text(required=False) #ta_min
    lower_max_temperature 	= columns.Decimal(required=False) #ti_max
    med_max_temperature		= columns.Decimal(required=False) #tm_max
    med_temperature 		= columns.Decimal(required=False) #tm_mes
    med_min_temperature		= columns.Decimal(required=False) #tm_min
    high_min_temperature 	= columns.Decimal(required=False) #ts_min
    wind_med_velocity 		= columns.Decimal(required=False) #w_med
    high_gust_dir_vel_date 	= columns.Text(required=False) #w_racha

#Measurement Model for daily values
class Daily_Measurement(Model):
    station_id			= columns.Text(primary_key=True,required=True) #indicativo
    measure_date		= columns.Date(primary_key=True,required=True) #fecha
    max_temp_hour		= columns.Text(required=False) #horatmax
    min_temp_hour		= columns.Text(required=False) #horatmin
    max_temp 			= columns.Decimal(required=False,index=True) #tmax
    med_temp 			= columns.Decimal(required=False) #tmed
    min_temp 			= columns.Decimal(required=False,index=True) #tmin
    max_press_hour		= columns.Text(required=False) #horaPresMax
    min_press_hour		= columns.Text(required=False) #horaPresMin
    max_pressure 		= columns.Decimal(required=False,index=True) #presMax
    min_pressure 		= columns.Decimal(required=False,index=True) #presMin
    precip				= columns.Decimal(required=False,index=True) #prec
    wind_med_vel 		= columns.Decimal(required=False,index=True) #velmedia
    wind_dir			= columns.Text(required=False) #dir
    wind_streak 		= columns.Decimal(required=False,index=True) #racha
    wind_streak_hour	= columns.Text(required=False) #horaracha
    insolation			= columns.Decimal(required=False,index=True) #sol

#Measurement Model for cleaned daily values
class Clean_Daily_Measurement(Model):
    station_id          = columns.Text(primary_key=True,required=True) #indicativo
    measure_date        = columns.Date(primary_key=True,required=True) #fecha
    max_temp_hour       = columns.Text(required=False) #horatmax
    min_temp_hour       = columns.Text(required=False) #horatmin
    max_temp            = columns.Decimal(required=False,index=True) #tmax
    med_temp            = columns.Decimal(required=False) #tmed
    min_temp            = columns.Decimal(required=False,index=True) #tmin
    max_press_hour      = columns.Text(required=False) #horaPresMax
    min_press_hour      = columns.Text(required=False) #horaPresMin
    max_pressure        = columns.Decimal(required=False,index=True) #presMax
    min_pressure        = columns.Decimal(required=False,index=True) #presMin
    precip              = columns.Decimal(required=False,index=True) #prec
    wind_med_vel        = columns.Decimal(required=False,index=True) #velmedia
    wind_dir            = columns.Text(required=False) #dir
    wind_streak         = columns.Decimal(required=False,index=True) #racha
    wind_streak_hour    = columns.Text(required=False) #horaracha
    insolation          = columns.Decimal(required=False,index=True) #sol


class Station_limits(Model):
    station_id          = columns.Text(primary_key=True,required=True) #indicativo
    maxMaxTemp     = columns.Decimal(required=False,index=True)
    avgMaxTemp     = columns.Decimal(required=False,index=True)
    minMaxTemp     = columns.Decimal(required=False,index=True)
    maxMaxPressure     = columns.Decimal(required=False,index=True)
    avgMaxPressure     = columns.Decimal(required=False,index=True)
    minMaxPressure     = columns.Decimal(required=False,index=True)
    maxMedTemp     = columns.Decimal(required=False,index=True)
    avgMedTemp     = columns.Decimal(required=False,index=True)
    minMedTemp     = columns.Decimal(required=False,index=True)
    maxMinTemp     = columns.Decimal(required=False,index=True)
    avgMinTemp     = columns.Decimal(required=False,index=True)
    minMinTemp     = columns.Decimal(required=False,index=True)
    maxPrecip     = columns.Decimal(required=False,index=True)
    avgPrecip     = columns.Decimal(required=False,index=True)
    minPrecip     = columns.Decimal(required=False,index=True)
    maxWindMedVel     = columns.Decimal(required=False,index=True)
    avgWindMedVel     = columns.Decimal(required=False,index=True)
    minWindMedVel     = columns.Decimal(required=False,index=True)
    maxWindStreak     = columns.Decimal(required=False,index=True)
    avgWindStreak     = columns.Decimal(required=False,index=True)
    minWindStreak     = columns.Decimal(required=False,index=True)

class Station_Regression_Prediction(Model):
    station_id          = columns.Text(primary_key=True,required=True) #indicativo
    max_temp            = columns.Decimal(required=False,index=True) #tmax
    max_temp_pred       = columns.Decimal(required=False,index=True) #tmax
    med_temp            = columns.Decimal(required=False,index=True) #tmed
    med_temp_pred       = columns.Decimal(required=False,index=True) #tmed
    min_temp            = columns.Decimal(required=False,index=True) #tmin
    min_temp_pred       = columns.Decimal(required=False,index=True) #tmin
    max_pressure        = columns.Decimal(required=False,index=True) #presMax
    max_pressure_pred   = columns.Decimal(required=False,index=True) #presMax
    min_pressure        = columns.Decimal(required=False,index=True) #presMin
    min_pressure_pred   = columns.Decimal(required=False,index=True) #presMin
    precip              = columns.Decimal(required=False,index=True) #prec
    precip_pred         = columns.Decimal(required=False,index=True) #prec
    insolation          = columns.Decimal(required=False,index=True) #sol
    insolation_pred     = columns.Decimal(required=False,index=True) #sol


class Station_NaiveBayes_Prediction(Model):
    station_id          = columns.Text(primary_key=True,required=True) #indicativo
    stationIndex        = columns.Decimal(required=False,index=True)
    prediction          = columns.Decimal(required=False,index=True)
    province			= columns.Text(required=False,index=True)


#Reservoir
class Reservoir(Model):
    reservoir_name      = columns.Text(primary_key=True,required=True) #
    measure_date        = columns.Text(primary_key=True,required=True) #
    reservoir_type      = columns.Integer(primary_key=True,required=True) # 0:Water, 1:Energy
    latitude            = columns.Text(required=True)
    longitude           = columns.Text(required=True)
    capacity            = columns.Decimal(required=False) #
    actual_reservoir    = columns.Decimal(required=False) #
    last_year_reservoir = columns.Decimal(required=False) #
    five_years_med      = columns.Decimal(required=False) #
    ten_years_med       = columns.Decimal(required=False) #


#Earthquake
class Earthquake(Model):
    eventId             = columns.Text(primary_key=True,required=True)
    place               = columns.Text(required=True,index=True) #
    time                = columns.Text(required=True,index=True) #
    fecha               = columns.DateTime(required=True,index=True) #
    magnitude           = columns.Decimal(required=True)
    depth               = columns.Decimal(required=True)
    longitude           = columns.Decimal(required=True,index=True)
    latitude            = columns.Decimal(required=True,index=True)
    geojson             = columns.Text(required=True) #

#LinearModel
class LinearModel(Model):
    #uid             = columns.UUID(primary_key=True,required=True)
    name            = columns.Text(primary_key=True,required=True) #
    model           = columns.Blob(required=True) #


# next, setup the connection to your cassandra server(s)...
# see http://datastax.github.io/python-driver/api/cassandra/cluster.html for options
# the list of hosts will be passed to create a Cluster() instance
connection.setup(['127.0.0.1','192.168.246.236'], "dev", protocol_version=3)

#Create CQL tables
#sync_table(Station)
#sync_table(Monthly_Measurement)
#sync_table(Daily_Measurement)
sync_table(Earthquake)
#sync_table(Station_limits)
#sync_table(Clean_Daily_Measurement)
#sync_table(Station_Regression_Prediction)
#sync_table(Station_NaiveBayes_Prediction)
#sync_table(LinearModel)
