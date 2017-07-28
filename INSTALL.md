# Install Guide
## Common Steps
1. Create virtualenv with python3

   * virtualenv -p python3 <"VIRTUALENV FOLDER">
2. Install system requirements with apt

   * sudo apt install python-numpy python3-dev
## For Django Web Application
1. Install requirements

   * pip3 install -r virtualenv/requirementsDjango.txt
   * Wait (it could take some time compiling the sources)
2. Activate Virtual Env
   * virtualenv/bin/activate
3. Do Django migration
   * Go to Django/mysite
   * Execute python manage.py migrate
4. Run Django
   * Go to project root
   * Execute bash startDjango.sh (optionally pass the LG IP)
   * Go to http://YOUR_IP:8000
   
## For Flask Server
1. Install requirements

   * pip3 install -r virtualenv/requirementsFlask.txt
   
## For Data Mining Environment
1. Install requirements

   * pip3 install -r virtualenv/requirementsDataMining.txt


##  More Coming Soon...
