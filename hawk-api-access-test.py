import json

import requests
from mohawk import Sender


# URL = "http://localhost:8000/peoplefinder/api/activity-stream/"
URL = "http://localhost:8000/peoplefinder/api/person-api/"

ID = "xxx"
SECRET = "xxx"

content_type = "application/json"
content = ""

sender = Sender(
    {
        "id": ID,
        "key": SECRET,
        "algorithm": "sha256",
    },
    URL,
    "GET",
    content=content,
    content_type=content_type,
)

# print(sender.request_header)

response = requests.get(
    URL,
    data=content,
    headers={"Authorization": sender.request_header, "Content-Type": content_type},
)

print(json.dumps(response.json()))
