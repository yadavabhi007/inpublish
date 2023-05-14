#!/bin/bash

cd /app
echo "--> INSTALLO I REQUISITI:"
pip3 install -r requirements.txt
sleep 20
echo "--> MIGRATION:"
python manage.py makemigrations
python manage.py migrate
echo "--> FILE STATIC:"
python manage.py collectstatic --noinput
echo "--> AVVIO IL SERVER:"
gunicorn inpublish.wsgi:application --bind 0.0.0.0:80 --timeout 300