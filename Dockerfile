# syntax=docker/dockerfile:1
FROM python:latest

WORKDIR /home/app

ADD https://github.com/diont17/grocerywatcher.git /home/app

RUN pip install --no-cache-dir -r /home/app/requirements.txt

EXPOSE 9000

CMD flask run -h 0.0.0.0 -p 9000
