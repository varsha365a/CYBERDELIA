# Change your SID to your own one
SID=17058032
NAME=cyberdelia_db

ALL:
	docker build -t $(SID)/$(NAME)_i .

run: params
	docker network create --subnet=203.0.113.0/24 $(SID)/cyberdelia_net
	docker run -d --net $(SID)/cyberdelia_net --ip 203.0.113.201 --hostname thegibson -e POSTGRES_PASSWORD="H4ckTh3Pl4n3t" -e POSTGRES_DB="gibson" --name $(SID)_$(NAME)_c $(SID)/$(NAME)_i -c hba_file=/postgres/pg_hba.conf	
	sleep 15
	docker exec -i $(SID)_$(NAME)_c psql -U postgres -d gibson < sqlconfig/cyberdelia.sql

clean:
	-docker kill $(SID)_$(NAME)_c
	-docker rm $(SID)_$(NAME)_c
	-docker network rm $(SID)/cyberdelia_net

# per-student build parameters (APP_UID / APP_PORT), derived from your SID
include ../params.mk
