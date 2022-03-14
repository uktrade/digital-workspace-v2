import hashlib
import json

from time import sleep

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q

import mailchimp_marketing as MailchimpMarketing


from peoplefinder.models import Building, Person
from mailchimp_marketing.api_client import ApiClientError

from mailchimp.utils import create_tags, create_person_tags, create_member_info


MAX_CONTACTS_NUMBER = 1000


class MailchimpBulkUpdateError(Exception):
    def __init__(self, message, response):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.response = response


class MailchimpUpdatePersonError(Exception):
    def __init__(self, message, response):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.response = response


class MailchimpDeletePersonError(Exception):
    def __init__(self, message, response):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.response = response


class MailchimpApiResponseError(Exception):
    pass


def get_subscriber_hash(email):
    return hashlib.md5(email.encode("utf-8")).hexdigest()


def get_mail_chimp_client_list():
    mailChimp = MailchimpMarketing.Client()
    mailChimp.set_config(
        {
            "api_key": settings.MAILCHIMP_API_KEY,
        }
    )
    list_id = settings.MAILCHIMP_LIST_ID
    return mailChimp, list_id


def mailChimp_get_current_subscribers() -> list:
    client, list_id = get_mail_chimp_client_list
    # find howmnay contacts there are.
    # There is a maximum number of contact that can be return in one call
    response = client.lists.get_list(
        list, include_total_contacts=True, fields=["stats.member_count"]
    )

    # The response format is {'stats': {'member_count': 2}}
    member_count = response["stats"]["member_count"]
    offset = 0
    total_read = 0
    howmany = MAX_CONTACTS_NUMBER
    email_list = []
    while True:
        # # The response format is
        # {'members': [{'email_address': 'email1'},
        # {'email_address': 'email2'},
        # {'email_address': 'email3'}]}
        response = client.lists.get_list_members_info(
            list_id, fields=["members.email_address"], count=howmany, offset=offset
        )

        address_dict = response["members"]
        # Transform the list of dictionaries to a list of email addresses
        temp_list = {v for d in address_dict for v in d.values()}
        email_list.append(temp_list)
        offset += howmany
        total_read += howmany
        if total_read >= member_count:
            break

    return email_list


def mailChimp_delete_person(email: str):
    mailChimp, list_id = get_mail_chimp_client_list()
    subscriber_hash = MailchimpMarketing.get_subscriber_hash(email)
    try:
        response = mailChimp.lists.delete_list_member_permanent(
            list_id, subscriber_hash
        )
        if response.status != 200:
            raise MailchimpDeletePersonError(
                "Error non 200 response from Mailchimp update tags", response=response
            )

    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error


def mailchimp_handle_person(person: Person):
    mailChimp, list_id = get_mail_chimp_client_list()
    subscriber_hash = get_subscriber_hash(person.email)
    try:
        member_info = create_member_info(person)
        response = mailChimp.lists.set_list_member(
            list_id, subscriber_hash, member_info
        )
        # Check status codes
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response from Mailchimp update list member: f{person.contact_email}",
                response=response,
            )

    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error

    try:
        tags = create_person_tags(person)
        response = mailChimp.lists.update_list_member_tags(
            list_id, subscriber_hash, {"tags": tags}
        )
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response from Mailchimp update tags: f{person.contact_email}",
                response=response,
            )

        raise MailchimpUpdatePersonError
    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error


def delete_subscribers_missing_locally(mailChimp_list):
    people_finder_list = Person.objects.values_list("contact_email", flat=True)
    for person_email in mailChimp_list:
        if person_email not in people_finder_list:
            mailChimp_delete_person(person_email)


def run_batch_operation(mailChimp, payload: dict, operation_type: str):
    try:
        response = mailChimp.batches.start(payload)
        batch_id = response["id"]
    except ApiClientError as api_error:
        raise MailchimpBulkUpdateError(
            f"Error perfroming {operation_type}",
            response=response,
        ) from api_error

    while True:
        sleep(0.05)
        response = mailChimp.batches.status(batch_id)
        status = response["status"]
        if status == "finished":
            break

    if response["errored_operations"]:
        # Read the failed list, and send an email
        response_body_url = response["response_body_url"]
        errors = find_errors(response_body_url)

    return response, errors


def find_errors(response_body_url):
    import urllib.request

    response_body_url = "RESPONSE_BODY_URL_FROM_PREVIOUS_STEPS"
    data = ""
    with urllib.request.urlopen(response_body_url) as response:
        data = response.read()

    # get data from gzipped archive, return as JSON array
    # results = process_batch_archive(data)
    # for result in results:
    #     user = fakeDB.findUser(result["operation_id"])
    #     fakeDB.updateUser(user, {
    #         "mailchimp_web_id": result["response"]["web_id"]
    #     }
    #


def create_or_update_subscriber_for_all_people():
    mailChimp, list_id = get_mail_chimp_client_list()
    persons = (
        Person.objects.all()
        .select_related("country")
        .annotate(
            building_list=ArrayAgg(
                "buildings__name",
                filter=Q(buildings__name__isnull=False),
                distinct=True,
            )
        )
        .only("email", "first_name", "last_name", "country__code")
    )
    operations = []
    tag_operations = []
    full_building_list = Building.objects.all().values_list("code", flat=True)

    for person in persons:
        subscriber_hash = get_subscriber_hash(person.email)
        operation = {
            "method": "PUT",
            "path": f"/lists/{list_id}/members/{subscriber_hash}",
            "operation_id": person.user_id,
            "body": json.dumps(create_member_info(person)),
        }
        operations.append(operation)
        # Create the tag operation at thewsame time, to avoid looping aroud the twice
        tag_operation = {}
        tag_operations = {
            "method": "POST",
            "path": f"/lists/{list_id}/members/{subscriber_hash}/tags",
            "operation_id": person.user_id,
            "body": json.dumps(
                {"tags": create_tags(person, full_building_list, person.building_list)}
            ),
        }
        tag_operations.append(tag_operation)

    payload = {"operations": operations}
    response, message = run_batch_operation(mailChimp, payload, "Update contacts")
    payload = {"operations": tag_operations}
    response,  message = run_batch_operation(mailChimp, payload, "Update tags")
