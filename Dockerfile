# pull the official base image
FROM python:3.9-slim-buster

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
COPY . /app

# install dependencies 
RUN mkdir -p ~/.config/pquisby &&\
    cp credentials.json ~/.config/pquisby &&\
    pip install --upgrade pip &&\
    pip install -r requirements.txt

EXPOSE 8000
CMD python manage.py runserver 0.0.0.0:8000
