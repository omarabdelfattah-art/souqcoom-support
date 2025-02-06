#!/bin/bash
source env/bin/activate
gunicorn -c gunicorn_config.py api:app
