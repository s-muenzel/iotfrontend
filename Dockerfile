FROM alpine

LABEL maintainer=s.a.muenzel@gmail.com

RUN apk add python3 
RUN pip3 install Flask 
RUN pip3 install mysql-connector-python
RUN pip3 install paho-mqtt
RUN pip3 install pyyaml

COPY app.py .
COPY db.cnf .
COPY mq.cnf .

COPY templates/top.htm /templates/top.htm
COPY templates/devices.htm /templates/devices.htm
COPY templates/actions.htm /templates/actions.htm
COPY templates/action.htm /templates/action.htm
COPY templates/editentry.htm /templates/editentry.htm
COPY templates/addentry.htm /templates/addentry.htm
COPY templates/addaction.htm /templates/addaction.htm

EXPOSE 80/tcp

##run_cmd_arg## --publish 8808:80
CMD ["python3","app.py"]
