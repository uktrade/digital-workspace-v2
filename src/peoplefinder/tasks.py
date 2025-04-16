from config.celery import celery_app


@celery_app.task(bind=True)
def notify_user_about_profile_changes(self, person_pk, personalisation, countdown=None):
    from peoplefinder.services.person import PersonService

    print(
        "Running: notify_user_about_profile_changes\n"
        f" - person_pk: {person_pk}\n"
        f" - countdown: {countdown}\n"
    )

    PersonService().notify_about_changes_debounce(
        person_pk=person_pk,
        personalisation=personalisation,
        countdown=countdown,
    )
