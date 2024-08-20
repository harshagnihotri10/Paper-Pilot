import pytest
import os
import sys
sys.path.append("C:/Users/harsh/Projects/Paper-Pilot/backend")

from app import app

def test_login_and_summarize(client):
    # Register a new user
    response = client.post('/register', json={
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "password123"
    })
    
    # Check the registration response
    if response.status_code == 409:
        print("User already exists, proceeding with login.")
    else:
        assert response.status_code == 201, "User registration failed, check the response data."
    
    # Log in the user to get the JWT token
    response = client.post('/login', json={
        "email": "test1@example.com",
        "password": "password123"
    })
    
    # Print the response for debugging
    print(response.data)
    print(response.status_code)

    # Ensure the login was successful
    assert response.status_code == 200, "Login failed, check the response data."

    # Check if the JSON response has the 'token' key
    assert response.is_json, "Response is not in JSON format."
    json_data = response.get_json()
    assert "token" in json_data, "Token not found in the login response."

    token = json_data['token']

    # Use the token to access the summarize endpoint
    response = client.post('/summarize', headers={"Authorization": f"Bearer {token}"}, json={
        "article_id": 9
    })
    assert response.status_code == 200, "Summarization failed, check the response data."

    # Checking the structure of the summary response
    json_data = response.get_json()
    assert "summary" in json_data, "Summary not found in the summarize response."
    assert isinstance(json_data["summary"], str), "Summary is not a string."
