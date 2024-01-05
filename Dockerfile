# syntax=docker/dockerfile:1
FROM python:latest

WORKDIR /home/app

ADD https://github.com/diont17/grocerywatcher.git /home/app

# ADD ./requirements.txt /home/app/requirements.txt
RUN pip install --no-cache-dir -r /home/app/requirements.txt

EXPOSE 9000

CMD gunicorn -p 9000 -w 2