import pytest
import os
import sys
sys.path.append("C:/Users/harsh/Projects/Paper-Pilot/backend")

from app import app

def test_register_user(client):
    response = client.post('/register', json={
    "username": "uniqueuser123",
    "email": "unique@example.com",
    "password": "password123"
})
    if response.status_code == 409:
        print("User already exists.")
    else:
        assert response.status_code == 201