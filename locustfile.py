import os
import random
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from locust import HttpUser, TaskSet, between, task

CSRF_TOKEN = os.environ.get("CSRF_TOKEN", None)
SESSION_ID = os.environ.get("SESSION_ID", None)
USER_ID = os.environ.get("USER_ID", None)

sso_headers = {"Cookie": f"csrftoken={CSRF_TOKEN}; sessionid={SESSION_ID}"}  # noqa E501

MENU_PATHS = [
    "news-and-views",
    "working-at-dbt",
    "about-us",
    "teams",
    "tools",
]


def clean_path(path: str) -> str:
    if path.startswith("/"):
        path = path[1:]
    return path


def get_url_path(url: str) -> str:
    path = urlparse(url).path
    return clean_path(path)


class SearchBrowsing(TaskSet):
    @task(20)
    def search_dbt(self):
        self.client.get("search/all/?query=DBT", headers=sso_headers)

    @task(20)
    def search_trade(self):
        self.client.get("search/all/?query=trade", headers=sso_headers)

    @task(20)
    def search_trading_with_dbt(self):
        self.client.get("search/all/?query=trading%20with%20dbt", headers=sso_headers)

    @task(1)
    def submit_search_feedback(self):
        self.client.post(
            f"feedback/submit/search-v2/",
            data={
                "csrfmiddlewaretoken": CSRF_TOKEN,
                "submitter": USER_ID,  # NOTE: THIS ID Will depend on the user for the passed in SESSION_ID
                "search_query": "An example search query",
                "search_data": '{"category":"all","hits":{"all":21,"people":19,"teams":0,"guidance":1,"tools":0,"news":1}}',
                "initial-search_data": '{"category": "all"}',
                "useful": False,
                "not_useful_comment": "Test 1",
                "trying_to_find": "Test 2",
            },
            headers=sso_headers,
        )


class NormalBrowsing(TaskSet):
    @task(100)
    def index(self):
        self.client.get("", headers=sso_headers)

    @task(80)
    def menu_path(self):
        random_path = random.choice(MENU_PATHS)
        self.client.get(random_path, headers=sso_headers)

    @task(20)
    def news_item(self):
        self.client.get(
            "news-and-views/dbt-celebration-month-say-thank-you/",
            headers=sso_headers,
        )

    @task(20)
    def team_ddat(self):
        self.client.get(
            "teams/digital-data-and-technology/people",
            headers=sso_headers,
        )

    @task(20)
    def team_employee_experience(self):
        self.client.get(
            "teams/digital-data-and-technology-employee-experience/",
            headers=sso_headers,
        )


class SitemapBrowsing(TaskSet):
    sitemap_urls: list[str] = []

    def get_random_path_from_sitemap(self):
        if not self.sitemap_urls:
            sitemap_xml = self.client.get(
                "sitemap.xml",
                headers=sso_headers,
            )

            root = ET.fromstring(sitemap_xml.text)
            self.sitemap_urls = [url[0].text for url in root]

        random_index = random.randint(0, len(self.sitemap_urls) - 1)
        random_url = self.sitemap_urls[random_index]
        return get_url_path(random_url)

    @task(80)
    def random_page_from_sitemap(self):
        random_path = self.get_random_path_from_sitemap()
        self.client.get(
            random_path,
            headers=sso_headers,
        )


class User(HttpUser):
    tasks = [
        SearchBrowsing,
        NormalBrowsing,
        # SitemapBrowsing,
    ]
    wait_time = between(4.5, 4.5)
