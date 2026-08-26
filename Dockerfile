FROM python:3

LABEL maintainer=s.a.muenzel@gmail.com

RUN pip3 install --break-system-packages --root-user-action ignore matplotlib
RUN pip3 install --break-system-packages --root-user-action ignore Flask 
RUN pip3 install --break-system-packages --root-user-action ignore mysql-connector-python
RUN pip3 install --break-system-packages --root-user-action ignore paho-mqtt
RUN pip3 install --break-system-packages --root-user-action ignore pyyaml
RUN pip3 install --break-system-packages --root-user-action ignore pymodbus

COPY *.py db.cnf mq.cnf ./

COPY templates/*.htm /templates/

COPY static/*.png  static/

EXPOSE 80/tcp

##run_cmd_arg## --publish 8808:80  -v /etc/dhcpd:/tmp/dhcp:ro 
CMD ["python3","app.py"]
