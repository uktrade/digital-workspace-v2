import json

import requests
from mohawk import Sender
from pprint import pprint


BASE_URL = "http://localhost:8000"
PATH = "/peoplefinder/api/person-api/"

URL = f"{BASE_URL}{PATH}"

ID = "xxx"
SECRET = "xxx"

url = URL

while True:
    sender = Sender(
        {
            "id": ID,
            "key": SECRET,
            "algorithm": "sha256",
        },
        url,
        "GET",
        content="",
        content_type="application/json",
    )

    response = requests.get(
        url,
        headers={
            "Authorization": sender.request_header,
            "Content-Type": "application/json",
        },
    )

    data = response.json()
    pprint(data)

    # uncomment to only run once
    # break

    if data.get("next"):
        url = data.get("next")
    else:
        break
