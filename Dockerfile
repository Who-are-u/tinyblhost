FROM python:3.8

WORKDIR ./docker_demo
 
ADD . .

RUN pip install -r requirements.txt
