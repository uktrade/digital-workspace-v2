from peoplefinder.models import Building, Person

GROUP_ONE_DIT_DOMAINS = [
                          "trade.gov.uk",
                          "mobile.trade.gov.uk",
                          "digital.trade.gov.uk",
                          "fco.gov.uk",
                          "fcdo.gov.uk",
                          "ukexportfinance.gov.uk",
]


def create_person_tags(person: Person) -> list:
    email = person.email
    tags = [
            {
            "name":"pf_imported",
            "status":"active"
            }
        ]
    one_dit_status = "inactive"
    if email:
        domain = email.split("@")[1]
        if domain in GROUP_ONE_DIT_DOMAINS:
            one_dit_status = "active"
    tags.append({
        "name":"group_onedit",
        "status":one_dit_status})

    # TODO find a way to improve the query
    # TODO don't run the query for the full list of building each time!
    building_tag_list = Building.objects.all().values_list("code", flat=True)
    person_buildings = person.buildings.all().values_list("code", flat=True)

    for building in person_buildings:
        tag = f"pf_building_{building[0]}"
        tags.append({
            "name": tag,
            "status": "active"})

    # We need to list the non active tags to take into account
    # if a person moved from one building to another
    for building in building_tag_list:
        if building not in person_buildings:
            tag = f"pf_building_{building[0]}"
            tags.append({
                "name": tag,
                "status": "inactive"})
    return tags


def create_member_info(person: Person) -> dict:
    member_info = {
        "email_address": person.email,
        "status_if_new": "subscribed",
        "merge_fields": {
          "FNAME": person.full_name,
          "LNAME": person.first_name,
          "PF_COUNTRY": person.country.code
        }
      }
    return member_info

