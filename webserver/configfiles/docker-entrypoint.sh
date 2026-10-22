#!/bin/bash

# removed remote access
#/usr/sbin/sshd

# web tier
nginx

# app tier (dev server - who has time to configure gunicorn)
python /app/app.py
