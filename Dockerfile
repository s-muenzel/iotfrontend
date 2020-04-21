FROM alpine

LABEL maintainer=s.a.muenzel@gmail.com

RUN apk add python3 ; pip3 install Flask ; pip3 install mysql-connector-python

COPY app.py .
COPY db.cnf .
COPY templates/top.htm /templates/top.htm
COPY templates/devices.htm /templates/devices.htm
COPY templates/actions.htm /templates/actions.htm
COPY templates/action.htm /templates/action.htm
COPY templates/editentry.htm /templates/editentry.htm

EXPOSE 80/tcp

CMD ["python3","app.py"]
