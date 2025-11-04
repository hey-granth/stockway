#!/usr/bin/env python
"""Test script to verify URL configuration"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/granth/PycharmProjects/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import resolve, reverse

def test_url():
    url = '/api/shopkeepers/warehouses/nearby/'
    try:
        match = resolve(url)
        print(f"✓ SUCCESS: URL '{url}' is properly configured!")
        print(f"  View Class: {match.func.view_class.__name__ if hasattr(match.func, 'view_class') else 'N/A'}")
        print(f"  URL Name: {match.url_name}")

        # Try reverse lookup
        try:
            reversed_url = reverse('shopkeeper-warehouses-nearby')
            print(f"  Reverse URL: {reversed_url}")
        except Exception as e:
            print(f"  Reverse lookup failed: {e}")

        return True
    except Exception as e:
        print(f"✗ ERROR: URL '{url}' not found!")
        print(f"  Error: {e}")
        return False

if __name__ == '__main__':
    success = test_url()
    sys.exit(0 if success else 1)

