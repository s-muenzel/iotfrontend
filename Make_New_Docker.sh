#/bin/sh


LOGS_CMD=echo

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -l|--log)
	LOGS_CMD="sudo docker logs --follow"
    shift # past value
    ;;
	*)
	echo "Unknown option"
	shift
	;;
esac
done

DOCKER_NAME=`pwd | awk -F/ '{print $NF}'`

RUN_CMD_ARGS=`awk '/##run_cmd_arg##/{$1=""; print $0}' Dockerfile`

sudo docker stop $DOCKER_NAME

sudo docker container rm $DOCKER_NAME

sudo docker image rm $DOCKER_NAME

sudo docker build -t $DOCKER_NAME .

CONTAINER=`sudo docker run -d $RUN_CMD_ARGS --name $DOCKER_NAME $DOCKER_NAME`

$LOGS_CMD $CONTAINER

