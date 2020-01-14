import datetime
from dataclasses import dataclass

from core.services.legacy_wordpress import wp_custom_request
from django.conf import settings
from django.utils.dateparse import parse_datetime


@dataclass(frozen=True)
class WpResult:
    """An individual search result from Wordpress"""

    content_type: str
    url: str
    title: str
    excerpt: str
    last_updated: datetime.datetime

    @classmethod
    def from_wp(cls, wp_data):
        return cls(
            content_type=wp_data["type"],
            url=f"{settings.LEGACY_WORDPRESS_FRONTEND_URL}{wp_data['mapped_path']}",
            title=wp_data["title"],
            excerpt=wp_data["excerpt"],
            last_updated=parse_datetime(wp_data["modified"])
        )


class WpResultSet:
    """A specific set (page) of results from Wordpress.

    It only contains one specific page of results, but acts as a proxy
    for the set of results as a whole in order to play well with
    Django's ``Paginator``.
    """
    def __init__(self, page, per_page, total_count, wp_results):
        self.page = page
        self.per_page = per_page
        self.min_index = (page - 1) * per_page
        self.max_index = self.min_index + per_page
        self.total_count = total_count
        self.results = [WpResult.from_wp(r) for r in wp_results]

    def count(self):
        return self.total_count

    def __len__(self):
        return self.total_count

    def __getitem__(self, key):
        """ Adjusts indices to account for offsets"""
        if isinstance(key, slice):
            if key.start < self.min_index or key.stop > self.max_index:
                raise IndexError(
                    "WpResultSet only contains results from index "
                    f"{self.min_index} to {self.max_index}"
                    f"([{key.start}:{key.stop}] out of bounds)"
                )

            new_start = key.start - self.min_index
            new_stop = key.stop - self.min_index
            return self.results[new_start:new_stop:key.step]

    def __iter__(self):
        yield from self.results


def search(query, page=1, per_page=10):
    page = int(page)
    per_page = int(per_page)

    params = {
        "s": query,
        "page": page,
        "per_page": per_page
    }

    wp_response = wp_custom_request("/search", params)

    if wp_response:
        (headers, results) = wp_response
        result_count = int(headers["X-Wp-Total"])
        return WpResultSet(page, per_page, result_count, results)

    return []
