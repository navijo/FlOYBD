function loadStatsData(station, dateFrom,dateTo){
 $.ajax({
            url: 'getGraphDataForStats/',
            data: {
              'station': station,
               'dateFrom': dateFrom,
               'dateTo': dateTo
            },
            dataType: 'json',
            success: function (data) {
              if (data.stationData) {
                createTempStatsChart(data.stationData)
                createPressureStatsChart(data.stationData)
                createWindDirStatsChart(data.stationData)
                createPrecipStatsChart(data.stationData)
              }
            }
      });
}

function createTempStatsChart(data){
    var chart = bb.generate({
        "data": {
         "x": "x",
            "json": data,
            keys: {
                x: 'measure_date',
                value: ["max_temp","med_temp","min_temp"]
            },
        "type": "bar",
        "labels": true,
        "colors": {
          "max_temp": "#ff0000",
          "med_temp": "#00ff00",
          "min_temp": "#0000ff"
            }
        },
        "axis": {
            "x": {
              "type": "timeseries",
              "count": data.length,
              "tick": {
                "format": "%Y-%m-%d"
              }
            }
          },
           "grid": {
            "y": {
              "show": true
            }
          },
         "bar": {
            "width": {
            "ratio": 0.3
            }
        },
        "subchart": {
                "show": true
         },
        "bindto": "#tempStatsChart"
    });
}

function createPressureStatsChart(data){
    var chart = bb.generate({
        "data": {
         "x": "x",
            "json": data,
            keys: {
                x: 'measure_date',
                value: ["max_pressure","min_pressure"]
            },
        "type": "spline"
        },
        "axis": {
            "x": {
              "type": "timeseries",
              "count": data.length,
              "tick": {
                "format": "%Y-%m-%d"
              }
            }
          },
          "grid": {
            "y": {
              "show": true
            }
          },
         "bar": {
            "width": {
            "ratio": 0.3
            }
        },
        "subchart": {
                "show": true
        },
        "bindto": "#pressureStatsChart"
    });
}

function createPrecipStatsChart(data){
    var chart = bb.generate({
        "data": {
         "x": "x",
            "json": data,
            keys: {
                x: 'measure_date',
                value: ["precip","insolation"]
            },
        "types": {
            "insolation": "area",
            "precip": "area-spline"
             },
        },
        "axis": {
            "x": {
              "type": "timeseries",
              "count": data.length,
              "tick": {
                "format": "%Y-%m-%d"
              }
            }
          },
          "grid": {
            "y": {
              "show": true
            }
          },
         "bar": {
            "width": {
            "ratio": 0.3
            }
        },
        "subchart": {
                "show": true
        },
        "bindto": "#precipInsoStatsChart"
    });
}

function createWindDirStatsChart(data){
    var chart = bb.generate({
        "data": {
            "x": "x",
            "json": data,
            keys: {
                x: 'measure_date',
                value: ["wind_streak","wind_med_vel"]
            },
            "type": "spline"
        },
        "axis": {
            "x": {
                "type": "timeseries",
                "count": data.length,
                "tick": {
                    "format": "%Y-%m-%d"
                }
            }
        },
        "grid": {
            "y": {
                "show": true
            }
        },
        "bar": {
            "width": {
            "ratio": 0.3
            }
        },
        "subchart": {
                "show": true
        },
        "bindto": "#windStatsChart"
    });
}
