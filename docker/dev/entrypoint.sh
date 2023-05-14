#!/bin/bash

cd /app
echo "--> INSTALLO I REQUISITI:"
pip3 install -r requirements.txt
sleep 5
echo "--> MIGRATION:"
python manage.py makemigrations
python manage.py migrate
echo "--> AVVIO IL SERVER:"
python manage.py runserver "0.0.0.0:80"
