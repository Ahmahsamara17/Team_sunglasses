#!/usr/bin/env python3
import subprocess
import requests
import atexit
import time
import os

FLAG = os.environ["FLAG"]

proc = subprocess.Popen(['/challenge/server'])
atexit.register(lambda: (proc.terminate(), proc.wait()))
time.sleep(1)  # Give it time to start

response = requests.get("http://challenge.localhost/")
assert response.status_code == 200
assert "Welcome to the login service" in response.text

response = requests.post("http://challenge.localhost/", data={
    "username": "guest",
    "password": "password"
}, allow_redirects=False)
assert response.status_code == 302
assert "session_user=guest" in response.headers.get('Set-Cookie', '')

response = requests.get("http://challenge.localhost/", cookies={"session_user": "guest"})
assert response.status_code == 200
assert "Hello, guest!" in response.text
assert FLAG not in response.text

response = requests.post("http://challenge.localhost/", data={
    "username": "admin",
    "password": "wrong"
})
assert response.status_code == 403
assert "Invalid username or password" in response.text

print("Public tests passed!")