# Install Guide
## Common Steps
1. Create virtualenv with python3
    
   ```
   virtualenv -p python3 <"VIRTUALENV FOLDER">
   ```
2. Install system requirements with apt
   
   ```
   sudo apt install python-numpy python3-dev
   ```
## For Django Web Application
1. Install requirements

   ```
   pip3 install -r virtualenv/requirementsDjango.txt
   ```
   * Wait (it could take some time compiling the sources)
2. Activate Virtual Env
   
   ``` 
   virtualenv/bin/activate
   ```
3. Do Django migration
   * Go to Django/mysite and execute:
   ```
   python manage.py migrate
   ```
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
1. Install requirements

   ```
   pip3 install -r virtualenv/requirementsFlask.txt
   ```
   
## For Data Mining Environment
1. Install requirements
  
   ```
   pip3 install -r virtualenv/requirementsDataMining.txt
   ```
   
2. Add Cronjobs to fetch new data automatically
    Add the following cronjobs to crontab
    * To get weekly the past week weather info:
    
    ```
    0 1 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash gather.sh
    ```
    * To clean the past week weather info:
    
    ```
    0 2 * * 1 cd ~/GSOC17/FlOYBD/ScriptsLaunchers && bash clean.sh
    ```
    
    
##  More Coming Soon...
