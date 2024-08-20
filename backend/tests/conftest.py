import psycopg2
import pytest
import sys
import os
sys.path.append("C:/Users/harsh/Projects/Paper-Pilot/backend")

from app import app  

@pytest.fixture(scope="module")
def db_connection():
    connection = psycopg2.connect(
        dbname="paperpilot",
        user="paperpilot_user",
        password="user_paperpilot",
        host="localhost"
    )
    yield connection
    connection.close()

@pytest.fixture(scope="module")
def client():
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client
