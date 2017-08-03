# Install Guide
## Common Steps
1. Clone this repository
    
   ```
   git clone https://github.com/navijo/FlOYBD.git
   ```
2. Go inside the newly created folder
   
   ```
   cd FlOYBD
   ```
3. Create virtualenv with python3
    
   ```
   virtualenv -p python3 <"VIRTUALENV FOLDER">
   ```
4. Install system requirements with apt
   
   ```
   sudo apt install python-numpy python3-dev
   ```
## For Django Web Application
1. Activate Virtual Env
   
   ``` 
   source <"VIRTUALENV FOLDER">/bin/activate
   ```
2. Install requirements

   ```
   pip3 install -r <"VIRTUALENV FOLDER">/requirementsDjango.txt
   ```
   * Wait (it could take some time compiling the sources)

3. Do Django migration
   * Edit Django/mysite/floybd/urls.py and comment these lines (the last ones from the file):
   
   ```
   startup_clean()
   createDefaultSettingsObjects()
   sendLogos()
   ```  
   * Go to Django/mysite and execute:
   
   ```
   python manage.py makemigrations
   python manage.py migrate
   python manage.py migrate --run-syncdb
   ```
   
    * Edit Django/mysite/floybd/urls.py and uncomment the previously commented lines
4. Run Django
   * Go to project root and execute:
   ```
   bash startDjango.sh (optionally pass the LG IP)
   ```
   * Go to http://YOUR_IP:8000
5. Crontab Jobs
    * In order to generate automatic KMLs for demo purposes, add the following cronjob to cron to generate every monday at  00:00 a weather KML,a KML of the latest week earthquakes, another one with the heatmap of the latest week earthquakes and a GTFS demo KML.
    ```
     0 0 * * 1 cd ~/FlOYBD; bash cronDjangoTask.sh
    ```
   
## For Flask Server
1. Activate Virtual Env
   
   ``` 
   source <"VIRTUALENV FOLDER">/bin/activate
   ```
2. Install requirements

   ```
   pip3 install -r <"VIRTUALENV FOLDER">/requirementsFlask.txt
   ```
   
## For Data Mining Environment
1. Activate Virtual Env
   
   ``` 
   source <"VIRTUALENV FOLDER">/bin/activate
   ```
2. Install requirements
  
   ```
   pip3 install -r <"VIRTUALENV FOLDER">/requirementsDataMining.txt
   ```
   
3. Add Cronjobs to fetch new data automatically
    Add the following cronjobs to crontab
    * To get weekly the past week weather info:
    
    ```
    0 1 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash gather.sh
    ```
    * To clean the past week weather info:
    
    ```
    0 2 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash clean.sh
    ```
    * To calculate new stats with the past week weather info:
    
    ```
    30 4 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash weatherFunctions.sh
    ```
    * To fetch daily the new earthquakes data:
    
    ```
    30 5 * * * cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash launchEarthquakes.sh
    ```
    * To retrain weekly the Linear Regression models with the new weather data:
    
    ```
    0 6 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash launchPredictions.sh
    ```
    
    
##  More Coming Soon...
