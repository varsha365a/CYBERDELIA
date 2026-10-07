# Change your SID to your own one
SID=17058032
NAME=cyberdelia_web

ALL:
	docker build --build-arg APP_UID=$(APP_UID) -t $(SID)/$(NAME)_i .

run: params
	docker run -d --net $(SID)/cyberdelia_net --ip 203.0.113.200 --hostname cyberdelia --add-host thegibson:203.0.113.201 -p 80:$(APP_PORT) --name $(SID)_$(NAME)_c $(SID)/$(NAME)_i
	# browse to http://localhost/ to hit the wall

clean:
	-docker kill $(SID)_$(NAME)_c
	-docker rm $(SID)_$(NAME)_c

# per-student build parameters (APP_UID / APP_PORT), derived from your SID
include ../params.mk
