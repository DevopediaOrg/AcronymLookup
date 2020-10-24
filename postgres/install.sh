sudo apt-get -y -qq update
sudo apt-get -y -qq install postgresql
sudo service postgresql start
sudo -u postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'pgpwd';"
sudo -u postgres psql -U postgres -c 'DROP DATABASE IF EXISTS acronyms;'
sudo -u postgres psql -U postgres -c 'CREATE DATABASE acronyms;'
sudo -u postgres psql -U postgres -d acronyms -f postgres/setUpDb.sql
