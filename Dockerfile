FROM python:3-slim

LABEL maintainer=s.a.muenzel@gmail.com

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py db.cnf mq.cnf ./

COPY templates/*.htm ./templates/
COPY templates/partials/*.htm ./templates/partials/
COPY static/*.png static/*.js static/*.ico ./static/

EXPOSE 80/tcp

##run_cmd_arg## --publish 8808:80  -v /etc/dhcpd:/tmp/dhcp:ro  -v /volume1/@appstore/DNSServer/named/etc/zone/master:/tmp/dns:ro 
CMD ["python", "app.py"]
