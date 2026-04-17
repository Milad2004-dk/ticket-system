#!/bin/bash
cd /home/site/wwwroot
pip install -r requirements.txt
gunicorn --bind=0.0.0.0 --timeout 600 TicketApi:app
