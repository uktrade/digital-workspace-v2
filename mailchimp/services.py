import hashlib

from django.conf import settings

import mailchimp_marketing as MailchimpMarketing


# from mailchimp3.utils import get_subscriber_hash
from peoplefinder.models import Person
from mailchimp_marketing.api_client import ApiClientError

from mailchimp.utils import create_person_tags, create_member_info


class MailchimpBulkUpdateError(Exception):
    pass


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
    return hashlib.md5(email.encode('utf-8')).hexdigest()


def get_mail_chimp_client_list() :
    mailchimp = MailchimpMarketing.Client()
    mailchimp.set_config({
        "api_key": settings.MAILCHIMP_API_KEY,
    })
    list_id = settings.MAILCHIMP_LIST_ID
    return mailchimp, list_id


MAX_CONTACTS_NUMBER = 1000

def mailchimp_get_current_subscribers() -> list:
    client, list_id = get_mail_chimp_client_list
    # find howmnay contacts there are.
    # There is a maximum number of contact that can be return in one call
    response = client.lists.get_list(list, include_total_contacts=True, fields=["stats.member_count"])

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
        response = client.lists.get_list_members_info(list_id,
                                                      fields=["members.email_address"],
                                                      count=howmany,
                                                      offset=offset)

        address_dict = response["members"]
        # Transform the list of dictionaries to a list of email addresses
        temp_list = {v for d in address_dict for v in d.values()}
        email_list.append(temp_list)
        offset += howmany
        total_read += howmany
        if total_read >= member_count:
            break

    return email_list


def mailchimp_delete_person(email:str):
    mailchimp, list_id = get_mail_chimp_client_list()
    subscriber_hash = MailchimpMarketing.get_subscriber_hash(email)
    try:
        response = mailchimp.lists.delete_list_member_permanent(list_id, subscriber_hash)
        if response.status != 200:
            raise MailchimpDeletePersonError(
                "Error non 200 response from Mailchimp update tags",
                response=response)

    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error


def mailchimp_handle_person(person: Person):
    mailchimp, list_id = get_mail_chimp_client_list()
    subscriber_hash = get_subscriber_hash(person.email)
    try:
        member_info = create_member_info(person)
        response = mailchimp.lists.set_list_member(list_id, subscriber_hash, member_info)
        # Check status codes
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response from Mailchimp update list member: f{person.contact_email}",
                response=response)

    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error

    try:
        tags = create_person_tags(person)
        response = mailchimp.lists.update_list_member_tags(list_id, subscriber_hash,
                                                           {"tags": tags} )
        if response.status != 200:
            raise MailchimpUpdatePersonError(
                f"Error non 200 response from Mailchimp update tags: f{person.contact_email}",
                response=response)

        raise MailchimpUpdatePersonError
    except ApiClientError as api_error:
        raise MailchimpApiResponseError from api_error


def delete_subscribers_missing_locally(mailchimp_list):
     people_finder_list = Person.objects.values_list("contact_email", flat=True)
     for person_email in mailchimp_list:
          if person_email not in people_finder_list:
              mailchimp_delete_person(person_email)


def create_or_update_subscriber_for_all_people():
    pass