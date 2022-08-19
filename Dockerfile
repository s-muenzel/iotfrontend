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
COPY templates/addaction.htm /templates/addaction.htm
COPY templates/action.htm /templates/action.htm

RUN mkdir static
COPY static/shutter-0.png  static/shutter-0.png
COPY static/shutter-10.png  static/shutter-10.png
COPY static/shutter-20.png  static/shutter-20.png
COPY static/shutter-30.png  static/shutter-30.png
COPY static/shutter-40.png  static/shutter-40.png
COPY static/shutter-50.png  static/shutter-50.png
COPY static/shutter-60.png  static/shutter-60.png
COPY static/shutter-70.png  static/shutter-70.png
COPY static/shutter-80.png  static/shutter-80.png
COPY static/shutter-90.png  static/shutter-90.png
COPY static/shutter-100.png  static/shutter-100.png
COPY static/offen.png static/offen.png
COPY static/zu.png static/zu.png
COPY static/unklar.png static/unklar.png

EXPOSE 80/tcp

##run_cmd_arg## --publish 8808:80
CMD ["python3","app.py"]
