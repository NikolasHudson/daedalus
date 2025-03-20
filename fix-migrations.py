#!/usr/bin/env python
"""
Script to fix database migrations for AWS app.
"""
import os
import sys
import django
from django.core.management import call_command

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daedlaus.settings')
django.setup()

def run_migrations():
    """Create and apply migrations for AWS app."""
    print("Creating migrations for AWS app...")
    call_command('makemigrations', 'aws')
    
    print("Applying migrations...")
    call_command('migrate', 'aws')
    
    print("Done! AWS migrations have been created and applied.")

if __name__ == "__main__":
    run_migrations()