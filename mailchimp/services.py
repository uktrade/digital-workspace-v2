import hashlib
import json
import logging

from datetime import datetime, timedelta

from time import sleep

from typing import Tuple

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q

from mailchimp.utils import create_member_info, create_person_tags, create_tags

import mailchimp_marketing as MailchimpMarketing  # noqa N812
from mailchimp_marketing.api_client import ApiClientError

from peoplefinder.models import Building, Person


logger = logging.getLogger(__name__)

MAX_CONTACTS_NUMBER = 1000


class MailchimpBulkUpdateError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


class MailchimpUpdatePersonError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


class MailchimpDeletePersonError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


class MailchimpApiResponseError(Exception):
    pass


class MailchimpTimeOutError(Exception):
    pass


class MailchimpProcessingError(Exception):
    pass


def get_subscriber_hash(email):
    return hashlib.md5(email.encode("utf-8")).hexdigest()  # noqa S303


def get_mailchimp_client_and_list() -> Tuple[MailchimpMarketing.Client, str]:
    mailchimp = MailchimpMarketing.Client()
    mailchimp.set_config(
        {
            "api_key": settings.MAILCHIMP_API_KEY,
        }
    )
    list_id = settings.MAILCHIMP_LIST_ID
    return mailchimp, list_id


def mailchimp_get_current_subscribers() -> list:
    client, list_id = get_mailchimp_client_and_list()
    # find howmnay contacts there are on MailChimp.
    response = client.lists.get_list(
        list_id, include_total_contacts=True, fields=["stats.member_count"]
    )
    # The response format is {'stats': {'member_count': <contact_numbers>}}
    member_count = response["stats"]["member_count"]

    # There is a maximum number of contact that can be return in one call
    # So do N calls, until all the contacts have been returned, and merge
    # the lists in one list.
    offset = 0
    total_read = 0
    # No error if you ask to read more contacts than the contacts in the list
    howmany = MAX_CONTACTS_NUMBER
    email_list = []
    while True:
        # # The response format is
        # {'members': [{'email_address': 'email1'},
        # {'email_address': 'email2'},
        # {'email_address': 'email3'}]}
        try:
            response = client.lists.get_list_members_info(
                list_id, fields=["members.email_address"], count=howmany, offset=offset
            )
        except ApiClientError as api_error:
            raise MailchimpApiResponseError from api_error
        address_dict = response["members"]
        # Transform the list of dictionaries to a list of email addresses
        temp_list = [v for d in address_dict for v in d.values()]

        email_list = [*email_list, *temp_list]
        offset += howmany
        total_read += howmany
        if total_read >= member_count:
            break

    return email_list


def mailchimp_delete_person(email: str):
    mailchimp, list_id = get_mailchimp_client_and_list()
    subscriber_hash = get_subscriber_hash(email)
    try:
        # Don't use delete_list_member_permanently.
        # It prevents the same email to be added again in the future
        response = mailchimp.lists.delete_list_member(list_id, subscriber_hash)

        if response.status_code != 204:
            raise MailchimpDeletePersonError(
                "Error from Mailchimp delete", response=response
            )

    except ApiClientError as api_error:
        raise MailchimpApiResponseError(
            f"API error from Mailchimp delete: {api_error.text}"
        )


def mailchimp_handle_person(person: Person):
    # There are two sets of information in a contact:
    # the mail merge fields
    # and the tags.
    # The two sets are updated using different api.
    mailchimp, list_id = get_mailchimp_client_and_list()
    subscriber_hash = get_subscriber_hash(person.email)
    try:
        member_info = create_member_info(person)
        response = mailchimp.lists.set_list_member(
            list_id, subscriber_hash, member_info
        )
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response from Mailchimp "
                f"update list member: f{person.email}",
                response=response,
            )

    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error

    try:
        tags = create_person_tags(person)
        response = mailchimp.lists.update_list_member_tags(
            list_id, subscriber_hash, {"tags": tags}
        )
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response "
                f"from Mailchimp update tags: f{person.email}",
                response=response,
            )

        raise MailchimpUpdatePersonError
    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error


def delete_subscribers_missing_locally(mailchimp_list: list):
    # Checks the list of contacts returned from mailchimp against the list
    # of persons in Peoplefinder.
    # Anyone in Mailchimp but not in peoplefinder gets deleted.
    # The contacts are deleted one by one. If there is an error,
    # the deletion continues, but add a note to the log.
    # It could be better to do the delete as a batch job, but as there are not
    # many people deleted every day, it should be ok to do delete them individually.
    people_finder_list = Person.objects.values_list("email", flat=True)
    deleted_counter = 0
    deletion_errors = 0

    for person_email in mailchimp_list:
        if person_email not in people_finder_list:
            try:
                mailchimp_delete_person(person_email)
                deleted_counter += 1
            except (MailchimpDeletePersonError, MailchimpApiResponseError):
                deletion_errors += 1
                logger.error(f"Bulk delete: {person_email} failed to delete.")

    return f"{deleted_counter} contacts deleted. {deletion_errors} errors."


valid_statuses = ["pending", "preprocessing", "started", "finalizing", "finished"]


def wait_for_completion(
    mailchimp: MailchimpMarketing.Client, batch_id: str, operation_type: str
):
    # This routine is called after starting a batch job,
    # and keep checking the status of the job until finished or
    # until there is a timeout.
    # Used to make sure the batch job is completed before starting the next operation.
    start_time = datetime.now()
    timeout_at = start_time + timedelta(minutes=settings.MAILCHIMP_TIMEOUT)
    while True:
        try:
            sleep(settings.MAILCHIMP_SLEEP_INTERVAL)
            response = mailchimp.batches.status(batch_id)
            status_returned = response["status"]
            if status_returned == "finished":
                break
            if status_returned not in valid_statuses:
                msg = (
                    f"Not valid status returned: "
                    f" '{status_returned}' "
                    f"while performing {operation_type}."
                )
                logger.error(msg)
                raise MailchimpBulkUpdateError(msg, response)

            if datetime.now() > timeout_at:
                msg = f"Timeout error from {operation_type}."
                logger.error(msg)
                raise MailchimpTimeOutError(msg)

        except ApiClientError as api_error:
            raise MailchimpBulkUpdateError(
                f"Error performing {operation_type}",
                response=response,
            ) from api_error

    elapsed_time = (datetime.now() - start_time).total_seconds()
    return elapsed_time, response


def run_batch_operation(
    mailchimp: MailchimpMarketing.Client, payload: dict, operation_type: str
):
    # This run a batch job. The payload contains the correct set of data
    # for the operation, and the operation type is used for messages.
    response = ""
    try:
        response = mailchimp.batches.start(payload)
        batch_id = response["id"]
    except ApiClientError as api_error:
        raise MailchimpBulkUpdateError(
            f"Error performing {operation_type}",
            response=response,
        ) from api_error

    elapsed_time, response = wait_for_completion(mailchimp, batch_id, operation_type)

    total_operation = response["total_operations"]
    error_count = response["errored_operations"]

    msg = f"{operation_type} processed {total_operation} in {elapsed_time}"
    if error_count:
        msg = f"{msg} with {error_count} errors. response = {response}"
    else:
        msg = f"{msg} with no errors."
    return msg, error_count


def create_or_update_subscriber_for_all_people():
    # full update of mailchimp, using the person data in peoplefinder.
    mailchimp, list_id = get_mailchimp_client_and_list()
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
    # The tags used in mailchimp are related to the buildings.
    # Create the full list of buildings in the system, so the tags can be updated
    full_building_list = Building.objects.all().values_list("code", flat=True)

    for person in persons:
        subscriber_hash = get_subscriber_hash(person.email)
        operation = {
            "method": "PUT",
            "path": f"/lists/{list_id}/members/{subscriber_hash}",
            "operation_id": f"fields{person.user_id}",
            "body": json.dumps(create_member_info(person)),
        }
        operations.append(operation)
        # Create the tag operation at the same time, to avoid looping twice
        tag_operation = {
            "method": "POST",
            "path": f"/lists/{list_id}/members/{subscriber_hash}/tags",
            "operation_id": f"tags{person.user_id}",
            "body": json.dumps(
                {"tags": create_tags(person, full_building_list, person.building_list)}
            ),
        }
        tag_operations.append(tag_operation)

    payload = {"operations": operations}

    # Wait for the update contact operation to complete,
    # before running the update tags operation.
    # This is to avoid creating tags for a non yet existing contact
    completion_message, error_count = run_batch_operation(
        mailchimp, payload, "Update contacts"
    )
    completion_message_tags = ""
    error_count_tags = 0
    # payload = {"operations": tag_operations}
    # completion_message_tags, error_count_tags = run_batch_operation(
    #     mailchimp, payload, "Update tags"
    # )
    message = f"{completion_message}{completion_message_tags}"
    if error_count or error_count_tags:
        raise MailchimpProcessingError(message)
    else:
        return message
