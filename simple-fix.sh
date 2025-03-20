#!/bin/bash

# Simple script to fix the AWS app migrations
# Run this in the Docker container

cd /app/daedlaus
python manage.py makemigrations aws
python manage.py migrate aws

echo "AWS app migrations have been created and applied!"