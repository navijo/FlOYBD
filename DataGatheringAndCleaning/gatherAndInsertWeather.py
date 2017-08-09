import requests
import time
import re
import sys
import getopt
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timedelta
from time import gmtime, strftime
from cassandra.cluster import Cluster

debug = False
min_stations = 2

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'S' or direction == 'W':
        dd *= -1
    return dd


def parse_dms(dms):
    patternDigits = '[\d]+'
    patternDirections = '[A-Za-z]'
    digits = re.findall(patternDigits, dms)
    directions = re.findall(patternDirections, dms)
    lat = dms2dd(digits[0][:2], digits[0][2:4], digits[0][4:6], directions[0])
    lng = dms2dd(digits[1][:2], digits[1][2:4], digits[1][4:6], directions[1])
    return (lat, lng)


def getStationDataFromJson(jsonData, stationId):
    stationData = []
    for item in jsonData:
        if (item["indicativo"] == stationId):
            stationData.append(item)
    return stationData


def printLog(msg):
    print(strftime("%d-%m-%Y %H:%M:%S", gmtime()), "->", msg)


def getData(url):
    """	Make the request to the api	"""
    try:
        response = requests.request(
            "GET", base_url + url, headers=headers, params=querystring, verify=False)
        if response:
            jsonResponse = response.json()
            if jsonResponse.get('estado') == 200:
                link = jsonResponse.get('datos')
                data = requests.request("GET", link, verify=False)
                if (data.status_code == 200):
                    return data.json()
            elif jsonResponse.get('estado') == 429:
                # Sleep until next minute
                printLog("####Sleeping")
                time.sleep(60)
                printLog("####Waked up!!")
                return getData(url)
    except requests.exceptions.ConnectionError:
        printLog("####ERROR!! => Sleeping")
        time.sleep(120)
        printLog("####Waked up!!")
        return getData(url)


def insertClimaticMonthlyData(row, data, anual, year):
    """	Insert one row into monthly_measurement table"""
    if anual:
        fecha = str(year)
        fechaStr = fecha + "-01-01T00:00:00UTC"
    else:
        fecha = data.get('fecha')
        fechaStr = fecha + "-02T00:00:00UTC"

    breakDate = datetime.strptime(
        fechaStr, '%Y-%m-%dT%H:%M:%SUTC').strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    steam_press = float(str(data.get('e')).replace(",", ".")) if not (data.get('e') is None) else None
    evap = float(str(data.get('evap')).replace(",", ".")) if not (data.get('evap') is None) else None
    relative_humidity = float(str(data.get('hr')).replace(",", ".")) if not (data.get('hr') is None) else None
    insolation_hours = float(str(data.get('inso')).replace(",", ".")) if not (data.get('inso') is None) else None

    covered_days = float(str(data.get('n_cub')).replace(",", ".")) if not (data.get('n_cub') is None) else None
    clear_days = float(str(data.get('n_des')).replace(",", ".")) if not (data.get('n_des') is None) else None
    foggy_days = float(str(data.get('n_fog')).replace(",", ".")) if not (data.get('n_fog') is None) else None
    hail_days = float(str(data.get('n_gra')).replace(",", ".")) if not (data.get('n_gra') is None) else None
    rain_days = float(str(data.get('n_llu')).replace(",", ".")) if not (data.get('n_llu') is None) else None
    snow_days = float(str(data.get('n_nie')).replace(",", ".")) if not (data.get('n_nie') is None) else None
    cloud_days = float(str(data.get('n_nub')).replace(",", ".")) if not (data.get('n_nub') is None) else None
    storm_days = float(str(data.get('n_tor')).replace(",", ".")) if not (data.get('n_tor') is None) else None

    rain_over_01mm = float(str(data.get('np_001')).replace(",", ".")) if not (data.get('np_001') is None) else None
    rain_over_1mm = float(str(data.get('np_010')).replace(",", ".")) if not (data.get('np_010') is None) else None
    rain_over_10mm = float(str(data.get('np_100')).replace(",", ".")) if not (data.get('np_100') is None) else None
    rain_over_30mm = float(str(data.get('np_300')).replace(",", ".")) if not (data.get('np_300') is None) else None

    temp_under_0 = float(str(data.get('nt_00')).replace(",", ".")) if not (data.get('nt_00') is None) else None
    temp_over_30 = float(str(data.get('nt_30')).replace(",", ".")) if not (data.get('nt_30') is None) else None

    visibility_under_50m = float(str(data.get('nv_0050')).replace(",", ".")) if not (
        data.get('nv_0050') is None) else None
    visibility_under_100m = float(str(data.get('nv_0100')).replace(",", ".")) if not (
        data.get('nv_0100') is None) else None
    visibility_under_1000m = float(str(data.get('nv_01000')).replace(",", ".")) if not (
        data.get('nv_01000') is None) else None

    wind_over_55km = float(str(data.get('nw_55')).replace(",", ".")) if not (data.get('nw_55') is None) else None
    wind_over_91km = float(str(data.get('nw_91')).replace(",", ".")) if not (data.get('nw_91') is None) else None

    lower_max_temperature = float(str(data.get('ti_max')).replace(",", ".")) if not (
        data.get('ti_max') is None) else None
    med_max_temperature = float(str(data.get('tm_max')).replace(",", ".")) if not (data.get('tm_max') is None) else None
    med_temperature = float(str(data.get('tm_mes')).replace(",", ".")) if not (data.get('tm_mes') is None) else None
    med_min_temperature = float(str(data.get('tm_min')).replace(",", ".")) if not (data.get('tm_min') is None) else None
    high_min_temperature = float(str(data.get('ts_min')).replace(",", ".")) if not (
        data.get('ts_min') is None) else None
    wind_med_velocity = float(str(data.get('w_med')).replace(",", ".")) if not (data.get('w_med') is None) else None

    session.execute("INSERT INTO Monthly_Measurement (station_id,steam_press,measure_date,evap,relative_humidity,\
					insolation_hours,covered_days,clear_days,foggy_days,hail_days,rain_days,snow_days,cloud_days,storm_days,\
					rain_over_01mm,rain_over_1mm,rain_over_10mm,rain_over_30mm,temp_under_0,temp_over_30,visibility_under_50m,\
					visibility_under_100m,visibility_under_1000m,wind_over_55km,wind_over_91km,max_daily_rain,total_monthly_rain,\
					month_percent_insol,sea_lvl_pressure_med,max_abs_pressure,med_abs_pressure,min_abs_pressure,max_abs_temperature,\
					min_abs_temperature,lower_max_temperature,med_max_temperature,med_temperature,med_min_temperature,high_min_temperature,\
					wind_med_velocity,high_gust_dir_vel_date) \
					VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" \
                    , [str(row[0]), steam_press, breakDate, evap, relative_humidity,
                       insolation_hours, covered_days, clear_days, foggy_days, hail_days, rain_days, snow_days,
                       cloud_days,
                       storm_days, rain_over_01mm, rain_over_1mm, rain_over_10mm, rain_over_30mm,
                       temp_under_0, temp_over_30,
                       visibility_under_50m, visibility_under_100m, visibility_under_1000m,
                       wind_over_55km, wind_over_91km,
                       data.get('p_max'), data.get('p_mes'), data.get('p_sol'), data.get('q_mar'),
                       data.get('q_max'), data.get('q_med'), data.get('q_min'), data.get('ta_max'),
                       data.get('ta_min'), lower_max_temperature, med_max_temperature, med_temperature,
                       med_min_temperature, high_min_temperature, wind_med_velocity, data.get('w_racha')])


def insertClimaticDailyData(row, data):
    """	Insert one row into daily_measurement table	"""
    tMax = float(str(data.get('tmax')).replace(",", ".")) if not (data.get('tmax') is None) else None
    tMed = float(str(data.get('tmed')).replace(",", ".")) if not (data.get('tmed') is None) else None
    tMin = float(str(data.get('tmin')).replace(",", ".")) if not (data.get('tmin') is None) else None
    presMax = float(str(data.get('presMax')).replace(",", ".")) if not (data.get('presMax') is None) else None
    presMin = float(str(data.get('presMin')).replace(",", ".")) if not (data.get('presMin') is None) else None
    try:
        prec = float(str(data.get('prec')).replace(",", ".")) if not (data.get('prec') is None) else None
    except (ValueError):
        prec = None
    velmedia = float(str(data.get('velmedia')).replace(",", ".")) if not (data.get('velmedia') is None) else None
    racha = float(str(data.get('racha')).replace(",", ".")) if not (data.get('racha') is None) else None
    sol = float(str(data.get('sol')).replace(",", ".")) if not (data.get('sol') is None) else None

    session.execute("INSERT INTO Daily_Measurement (station_id,measure_date,max_temp_hour,min_temp_hour,max_temp,\
					med_temp,min_temp,max_press_hour,min_press_hour,max_pressure,min_pressure,precip,wind_med_vel,wind_dir,\
					wind_streak,wind_streak_hour,insolation) \
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    , [str(row[0]), data.get('fecha'), data.get('horatmax'), data.get('horatmin'),
                       tMax, tMed, tMin, data.get('horaPresMax'), data.get('horaPresMin'), presMax, presMin,
                       prec, velmedia, data.get('dir'), racha, data.get('horaracha'), sol])


def getDatosTodasEstaciones():
    """	Gets data from all stations	"""
    allStations = getData(
        "/valores/climatologicos/inventarioestaciones/todasestaciones")
    for station in allStations:
        dd = parse_dms(station.get('latitud') + station.get('longitud'))
        lat = dd[0]
        lon = dd[1]
        session.execute("INSERT INTO Station (station_id,name,latitude,longitude,altitude,indsinop,province) \
						VALUES (%s,%s,%s,%s,%s,%s,%s)", [station.get('indicativo'), station.get('nombre')
            , str(lat), str(lon), int(station.get('altitud')), station.get('indsinop'), station.get('provincia')])


def getMonthlyValue(fromYear):
    """	Gets monthly values for one year"""
    year = int(fromYear)

    while year <= 2017:
        stationNumber = 0
        rows = session.execute('SELECT station_id FROM Station')

        for row in rows:

            stationNumber += 1

            if debug and stationNumber > min_stations:
                break

            printLog("Processing station:" + str(row[0]) + " year: " + str(year))
            stationClimatics = getData(
                "/valores/climatologicos/mensualesanuales/datos/anioini/" + str(year) + "/aniofin/" + str(
                    year) + "/estacion/" + str(row[0]))

            if ((type(stationClimatics) is not list) or (
                        (stationClimatics is None) and stationClimatics.get("estado") == 404)):
                continue
            for month in range(0, len(stationClimatics) - 1):
                monthlyClimatic = stationClimatics[month]
                insertClimaticMonthlyData(row, monthlyClimatic, False, year)
                print("Processing month ", month + 1, " for station ", str(row[0]))

            anualClimatic = stationClimatics[12]

            printLog("Processing anual for station " + str(row[0]))

            insertClimaticMonthlyData(row, anualClimatic, True, year)

            printLog("Stations Processed for year:" + str(year) + "->" + str(stationNumber))

        year += 1


def getClimatologicalDaily(yearFrom, monthFrom, dayFrom, yearTo, monthTo, dayTo):
    """	Get climatological daily values making a unique requests for a 10 days interval	"""
    fechaIni = yearFrom + "-" + monthFrom + "-" + dayFrom + "T00:00:00UTC"
    fechaFin = yearTo + "-" + monthTo + "-" + dayTo + "T00:00:00UTC"
    stationNumber = 0
    rows = session.execute('SELECT station_id FROM Station')

    for row in rows:
        printLog("Processing station:" + str(row[0]))

        dailyClimatics = getData(
            "/valores/climatologicos/diarios/datos/fechaini/" + fechaIni + "/fechafin/" + fechaFin + "/estacion/" + str(
                row[0]))

        if (type(dailyClimatics) is not list) or ((dailyClimatics is None) and dailyClimatics.get("estado") == 404):
            continue

        for day in range(0, len(dailyClimatics)):
            dailyClimatic = dailyClimatics[day]
            insertClimaticDailyData(row, dailyClimatic)
            printLog("Processing day "+str(day)+" for station " + str(row[0]))

        stationNumber += 1

        printLog("Stations Processed->" + str(stationNumber))


def getClimatologicalDailyAllYear(yearFrom, yearTo):
    """	Get climatological daily values making requests for every 10 days between the years interval"""
    now = datetime.now()
    yearFrom = int(yearFrom)

    breakDate = str(yearTo + 1) + "-01-01T00:00:00UTC"
    breakDate = datetime.strptime(breakDate, '%Y-%m-%dT%H:%M:%SUTC')

    printLog("Calculating from " + str(yearFrom) + " to " + str(yearTo) + " with break date: " + str(breakDate))

    while yearFrom <= yearTo:
        printLog("Calculating for year " + str(yearFrom))
        fechaIni = str(yearFrom) + "-01-01T00:00:00UTC"

        dayOfTheYear = 1

        while dayOfTheYear <= 365:
            printLog("##############Day of the year " + str(dayOfTheYear))
            fromDate = datetime.strptime(fechaIni, '%Y-%m-%dT%H:%M:%SUTC')
            toDate = fromDate + timedelta(days=10)

            if toDate > breakDate:
                toDate = str(yearTo) + "-12-31T00:00:00UTC"
                toDate = datetime.strptime(toDate, '%Y-%m-%dT%H:%M:%SUTC')
                dayOfTheYear = 365

            fechaFin = toDate.strftime('%Y-%m-%dT%H:%M:%SUTC')

            if fromDate > now:
                break

            stationNumber = 0
            # print ("eagerly sleeping...")
            # time.sleep(60)
            # print ("wake up..")
            dailyClimatics = getData(
                "/valores/climatologicos/diarios/datos/fechaini/" + fechaIni + "/fechafin/" + fechaFin + "/todasestaciones")

            rows = session.execute('SELECT station_id FROM Station')

            for row in rows:
                stationNumber += 1

                if debug and stationNumber > min_stations:
                    break

                printLog("Processing station:" + str(row[0]))

                if ((type(dailyClimatics) is not list) or (
                            (dailyClimatics is None) and dailyClimatics.get("estado") == 404)):
                    printLog("No Data for the requested interval from: " + str(fechaIni) + " to " + str(fechaFin))
                    continue

                stationClimatics = getStationDataFromJson(dailyClimatics, str(row[0]))
                for day in range(0, len(stationClimatics)):
                    dailyClimatic = stationClimatics[day]
                    actualDate = datetime.strptime(dailyClimatic.get('fecha'), '%Y-%m-%d')
                    printLog("Processing " + actualDate.strftime('%d-%m-%Y') + " for station " + str(row[0]))
                    insertClimaticDailyData(row, dailyClimatic)

                printLog("Stations Processed->" + str(stationNumber))

            fechaIni = toDate.strftime('%Y-%m-%dT%H:%M:%SUTC')
            dayOfTheYear += 10

        yearFrom += 1


def getApiKey():
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")
    rows = session.execute('SELECT * FROM api_key')
    apiKey = ''
    for row in rows:
        apiKey = row[1]
    return apiKey


def usage():
    print('Usage=> gatherAndInsert.py -t <stations/month/day> -y <year>')


# Main Function #####


def main(argv):
    year = ''
    typeS = ''
    try:
        opts, args = getopt.getopt(argv, "ht:y:", ["help", "type=", "year="])
        if not opts or len(opts) < 2:
            usage()
            sys.exit(2)
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-t", "--type"):
            typeS = arg
        elif opt in ("-y", "--year"):
            year = arg
    print('Type ', typeS)
    print('Year ', year)

    if typeS == 'stations':
        getDatosTodasEstaciones()
    elif typeS == 'month':
        print("Month")
        getMonthlyValue(int(year))
    elif typeS == 'day':
        print("Day")
        now = datetime.now()
        currentYear = now.year
        getClimatologicalDailyAllYear(int(year), currentYear)


if __name__ == "__main__":
    global api_key, querystring, headers, base_url
    api_key = getApiKey()
    querystring = {"api_key": api_key}
    headers = {'cache-control': "no-cache"}
    base_url = "https://opendata.aemet.es/opendata/api"

    start_time = time.time()
    cluster = Cluster(['192.168.246.236'])
    session = cluster.connect("dev")

    main(sys.argv[1:])
    printLog("END => " + str(time.time() - start_time))
