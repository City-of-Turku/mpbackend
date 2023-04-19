# Mobility Profile Backend
This is the backend for the Mobility Profile

## Installation without Docker
1.
First, install the necessary Debian packages.
TODO, add packages.

2. Clone the repository.
git clone https://github.com/City-of-Turku/mpbackend.git

3. Install pip requiremends
Be sure to load the environment before installing the requirements.
```
pip-install pip-tools
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

