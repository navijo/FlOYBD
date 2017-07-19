import transitfeed


schedule = transitfeed.Schedule()
schedule.AddAgency("US Agency", "http://iflyagency.com", "Europe/Madrid", "US_Agency")

service_period = schedule.GetDefaultServicePeriod()
service_period.SetStartDate("20070101")
service_period.SetEndDate("20190101")
service_period.SetWeekdayService(True)
service_period.SetDateHasService('20070704', False)

seattle = schedule.AddStop(lng=-122.332071, lat=47.606209, name="Seattle", stop_id="Seattle")
portland = schedule.AddStop(lng=-122.676482, lat=45.523062, name="Portland", stop_id="Portland")
sanFrancisco = schedule.AddStop(lng=-122.419416, lat=37.774929, name="San Francisco", stop_id="San_Francisco")
losAngeles = schedule.AddStop(lng=-118.243685, lat=34.052234, name="Los Angeles", stop_id="Los_Angeles")
sanDiego = schedule.AddStop(lng=-117.161084, lat=32.715738, name="San Diego", stop_id="San_Diego")
lasVegas = schedule.AddStop(lng=-115.139830, lat=36.169941, name="Las Vegas", stop_id="Las_Vegas")
phoenix = schedule.AddStop(lng=-112.074037, lat=33.448377, name="Phoenix", stop_id="Phoenix")
saltLake = schedule.AddStop(lng=-111.891047, lat=40.760779, name="Salt Lake", stop_id="Salt_Lake")
denver = schedule.AddStop(lng=-104.990251, lat=39.739236, name="Denver", stop_id="Denver")
chicago = schedule.AddStop(lng=-87.629798, lat=41.878114, name="Chicago", stop_id="Chicago")
dallas = schedule.AddStop(lng=-96.796988, lat=32.776664, name="Dallas", stop_id="Dallas")
sanAntonio = schedule.AddStop(lng=-98.493628, lat=29.424122, name="San Antonio", stop_id="San_Antonio")
houston = schedule.AddStop(lng=-95.369803, lat=29.760427, name="Houston", stop_id="Houston")
newOrleans = schedule.AddStop(lng=-90.071532, lat=29.951066, name="New Orleans", stop_id="New_Orleans")
atlanta = schedule.AddStop(lng=-84.387982, lat=33.748995, name="Atlanta", stop_id="Atlanta")
miami = schedule.AddStop(lng=-80.191790, lat=25.761680, name="Miami", stop_id="Miami")
washingtonDC = schedule.AddStop(lng=-77.036871, lat=38.907192, name="Washington DC", stop_id="Washington_DC")
newYork = schedule.AddStop(lng=-74.005941, lat=40.712784, name="New York", stop_id="New_York")
boston = schedule.AddStop(lng=-71.058880, lat=42.360082, name="Boston", stop_id="Boston")

route_seattle_LA = schedule.AddRoute(short_name="1", long_name="Route Seattle-Los Angeles", route_type="Bus", route_id="route_seattle_LA")
route_LA_Vegas = schedule.AddRoute(short_name="2", long_name="Route Los Angeles-Las Vegas", route_type="Bus", route_id="route_LA_Vegas")
route_Vegas_Washington = schedule.AddRoute(short_name="3", long_name="Route Las Vegas-Washington", route_type="Bus", route_id="route_Vegas_Washington")
route_LA_SanDiego = schedule.AddRoute(short_name="4", long_name="Route Los Angeles-San Diego", route_type="Bus", route_id="route_LA_SanDiego")
route_Vegas_Saltlake = schedule.AddRoute(short_name="5", long_name="Route Las Vegas-Salt Lake", route_type="Bus", route_id="route_Vegas_Saltlake")
route_Vegas_Dallas = schedule.AddRoute(short_name="6", long_name="Route Las Vegas-Dallas", route_type="Bus", route_id="route_Vegas_Dallas")
route_Dallas_SanAntonio = schedule.AddRoute(short_name="7", long_name="Route Dallas-San Antonio", route_type="Bus", route_id="route_Dallas_SanAntonio")
route_Dallas_Houston = schedule.AddRoute(short_name="8", long_name="Route Dallas-Houston", route_type="Bus", route_id="route_Dallas_Houston")
route_Dallas_Atlanta = schedule.AddRoute(short_name="9", long_name="Route Dallas-Atlanta", route_type="Bus", route_id="route_Dallas_Atlanta")
route_Atlanta_Miami = schedule.AddRoute(short_name="10", long_name="Route Atlanta-Miami", route_type="Bus", route_id="route_Atlanta_Miami")
route_Atlanta_Washington = schedule.AddRoute(short_name="11", long_name="Route Atlanta-Washington", route_type="Bus", route_id="route_Atlanta_Washington")
route_Washington_Boston = schedule.AddRoute(short_name="12", long_name="Route Washington-Boston", route_type="Bus", route_id="route_Washington_Boston")

tripSeattleLA = route_seattle_LA.AddTrip(schedule, headsign="From Seattle to Los Angeles", trip_id="tripSeattleLA")
tripSeattleLA.AddStopTime(seattle, stop_time='09:00:00')
tripSeattleLA.AddStopTime(portland, stop_time='11:00:00')
tripSeattleLA.AddStopTime(sanFrancisco, stop_time='12:00:00')
tripSeattleLA.AddStopTime(losAngeles, stop_time='13:00:00')

tripLASandiego = route_LA_SanDiego.AddTrip(schedule, headsign="From Los Angeles to San Diego", trip_id="tripLASandiego")
tripLASandiego.AddStopTime(losAngeles, stop_time='09:00:00')
tripLASandiego.AddStopTime(sanDiego, stop_time='10:00:00')

tripLA_Vegas = route_LA_Vegas.AddTrip(schedule, headsign="From Los Angeles to Las Vegas", trip_id="tripLA_Vegas")
tripLA_Vegas.AddStopTime(losAngeles, stop_time='09:00:00')
tripLA_Vegas.AddStopTime(lasVegas, stop_time='10:00:00')

tripVegas_Saltlake = route_Vegas_Saltlake.AddTrip(schedule, headsign="From Las Vegas to Salt Lake", trip_id="tripVegas_Saltlake")
tripVegas_Saltlake.AddStopTime(lasVegas, stop_time='09:00:00')
tripVegas_Saltlake.AddStopTime(saltLake, stop_time='10:00:00')

tripVegas_Washington = route_Vegas_Washington.AddTrip(schedule, headsign="From Las Vegas to Washington DC", trip_id="tripVegas_Washington")
tripVegas_Washington.AddStopTime(lasVegas, stop_time='09:00:00')
tripVegas_Washington.AddStopTime(denver, stop_time='10:00:00')
tripVegas_Washington.AddStopTime(chicago, stop_time='11:00:00')
tripVegas_Washington.AddStopTime(washingtonDC, stop_time='12:00:00')

tripVegas_Dallas = route_Vegas_Dallas.AddTrip(schedule, headsign="From Las Vegas to Dallas", trip_id="tripVegas_Dallas")
tripVegas_Dallas.AddStopTime(lasVegas, stop_time='09:00:00')
tripVegas_Dallas.AddStopTime(phoenix, stop_time='10:00:00')
tripVegas_Dallas.AddStopTime(dallas, stop_time='11:00:00')

tripDallas_SanAntonio = route_Dallas_SanAntonio.AddTrip(schedule, headsign="From Dallas to San Antonio", trip_id="tripDallas_SanAntonio")
tripDallas_SanAntonio.AddStopTime(dallas, stop_time='09:00:00')
tripDallas_SanAntonio.AddStopTime(sanAntonio, stop_time='10:00:00')

tripDallas_Houston = route_Dallas_Houston.AddTrip(schedule, headsign="From Dallas to Houston", trip_id="tripDallas_Houston")
tripDallas_Houston.AddStopTime(dallas, stop_time='09:00:00')
tripDallas_Houston.AddStopTime(houston, stop_time='10:00:00')

tripDallas_Atlanta = route_Dallas_Atlanta.AddTrip(schedule, headsign="From Dallas to Atlanta", trip_id="tripDallas_Atlanta")
tripDallas_Atlanta.AddStopTime(dallas, stop_time='09:00:00')
tripDallas_Atlanta.AddStopTime(newOrleans, stop_time='10:00:00')
tripDallas_Atlanta.AddStopTime(atlanta, stop_time='11:00:00')

tripAtlanta_Miami = route_Atlanta_Miami.AddTrip(schedule, headsign="From Atlanta to Miami", trip_id="tripAtlanta_Miami")
tripAtlanta_Miami.AddStopTime(atlanta, stop_time='09:00:00')
tripAtlanta_Miami.AddStopTime(miami, stop_time='10:00:00')

tripAtlanta_Washington = route_Atlanta_Washington.AddTrip(schedule, headsign="From Atlanta to Washington", trip_id="tripAtlanta_Washington")
tripAtlanta_Washington.AddStopTime(atlanta, stop_time='09:00:00')
tripAtlanta_Washington.AddStopTime(washingtonDC, stop_time='10:00:00')


tripWashington_Boston = route_Washington_Boston.AddTrip(schedule, headsign="From Washington to Boston", trip_id="tripWashington_Boston")
tripWashington_Boston.AddStopTime(washingtonDC, stop_time='09:00:00')
tripWashington_Boston.AddStopTime(newYork, stop_time='10:00:00')
tripWashington_Boston.AddStopTime(boston, stop_time='11:00:00')

schedule.Validate()
schedule.WriteGoogleTransitFeed('google_transit_us.zip')