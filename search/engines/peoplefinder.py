from dataclasses import dataclass

import core.services.peoplefinder as peoplefinder


@dataclass(frozen=True)
class PfSearchResult:
    """An individual search result from People Finder"""
    name: str
    role_and_group: str
    email: str
    phone: str
    key_skills: str
    languages: str
    profile_url: str
    image_url: str

    @classmethod
    def from_peoplefinder(cls, pf_data):
        return cls(
            name=pf_data["name"],
            role_and_group=pf_data["role_and_group"],
            email=pf_data["email"],
            phone=pf_data["phone"],
            key_skills=pf_data["key_skills"],
            languages=pf_data["languages"],
            profile_url=pf_data["profile_url"],
            image_url=pf_data["image_url"]
        )


def search(query):
    try:
        results = peoplefinder.request("/search/people", {"query": query}) or []
    except peoplefinder.PeoplefinderException:
        results = []

    return [PfSearchResult.from_peoplefinder(r) for r in results]
