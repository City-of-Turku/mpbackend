# Mobility Profile Backend
This is the backend for the Mobility Profile

## Installation with Docker Compose
First configure development environment settings as stated in `config_dev.env.example`. 

### Running the application
Run application with `docker-compose up`
This will startup and bind local postgres and mobilityprofile backend. 

### Runnig the application in production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

### Importing questions
To import questions run: `docker-compose run mpbackend import_questions`


## Installation without Docker
1.
First, install the necessary Debian packages.
TODO, add packages.

2. Clone the repository.
```
git clone https://github.com/City-of-Turku/mpbackend.git
```
3. Install python 3.10 and  pip requiremends
Be sure to load the **environment** before installing the requirements.
```
pip install pip-tools
pip install -r requirements.txt
```
4. Setup the PostGIS database.

Please note, we recommend PostgreSQL version 13 or higher.
Local setup:

```
sudo su postgres
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
createuser -RSPd mobilityprofile
createdb -O mobilityprofile -T template1 -l fi_FI.UTF-8 -E utf8 mobilityprofile
```

5. Create database tables.
```
./manage.py migrate
```

6. Import questions
```
./manage.py import_questions
```

