#/bin/sh

sudo docker stop iotfrontend

sudo docker container rm iotfrontend

sudo docker image rm iotfrontend

sudo docker build -t iotfrontend .

sudo docker run -d --publish 8808:80 --name iotfrontend iotfrontend
