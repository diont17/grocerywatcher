# syntax=docker/dockerfile:1
FROM python:latest

WORKDIR /home/app

ADD https://github.com/diont17/grocerywatcher.git /home/app

# ADD ./requirements.txt /home/app/requirements.txt
RUN pip install --no-cache-dir -r /home/app/requirements.txt

EXPOSE 8000
VOLUME /home/app/data

CMD gunicorn -b 0.0.0.0:8000 -w 2 app:app