#!/usr/bin/env python3

import os
import time

import jwt
import requests

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:5000/api/pqrs")
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")


def generate_token(permisos):
    payload = {"permisos": permisos}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def test_access(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_GATEWAY_URL, headers=headers)
    return response.status_code, response.json()


def main():
    total_attempts = 10
    blocked_attempts = 0

    for i in range(total_attempts):
        print(f"Attempt {i + 1}:")

        # Generate a token without the required permissions
        token = generate_token(permisos=["GET /other_resource"])

        status_code, response_json = test_access(token)
        if status_code in [401, 403]:
            print(f"Access blocked as expected. Status code: {status_code}")
            blocked_attempts += 1
        else:
            print(f"Access allowed unexpectedly. Status code: {status_code}")
        time.sleep(1)

    print(f"\nTotal attempts: {total_attempts}, Blocked attempts: {blocked_attempts}")
    if blocked_attempts == total_attempts:
        print("Unauthorized access was blocked 100% of the time.")
    else:
        print("Unauthorized access was not blocked 100% of the time.")


if __name__ == "__main__":
    main()
