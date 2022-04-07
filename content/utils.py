from django.contrib.contenttypes.models import ContentType


def remove_orphan_keyword_and_phrases():
    from content.models import (
        SearchExclusionPageLookUp,
        SearchKeywordOrPhrase,
        SearchPinPageLookUp,
    )

    # Remove all search exclusions not associated with a page
    exclude_look_up_ids = SearchExclusionPageLookUp.objects.all().values_list(
        "search_keyword_or_phrase__pk",
    )
    pin_look_up_ids = SearchPinPageLookUp.objects.all().values_list(
        "search_keyword_or_phrase__pk",
    )

    SearchKeywordOrPhrase.objects.exclude(pk__in=exclude_look_up_ids,).exclude(
        pk__in=pin_look_up_ids,
    ).delete()


def manage_pinned(obj, pinned_phrases_string):
    if not pinned_phrases_string:
        return

    from content.models import SearchKeywordOrPhrase, SearchPinPageLookUp

    # Delete existing pins for this page
    SearchPinPageLookUp.objects.filter(
        object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj),
    ).delete()

    pinned_phrases = pinned_phrases_string.split(",")

    for key_word_or_phrase_obj in pinned_phrases:
        key_word_or_phrase = (
            key_word_or_phrase_obj.lower().replace("'", "").replace('"', "").strip()
        )

        if key_word_or_phrase == "":
            continue

        search_keyword_or_phrase = SearchKeywordOrPhrase.objects.filter(
            keyword_or_phrase=key_word_or_phrase,
        ).first()

        if not search_keyword_or_phrase:
            search_keyword_or_phrase = SearchKeywordOrPhrase(
                keyword_or_phrase=key_word_or_phrase,
            )
            search_keyword_or_phrase.save()

        pin = SearchPinPageLookUp.objects.filter(
            search_keyword_or_phrase=search_keyword_or_phrase,
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).first()

        if not pin:
            SearchPinPageLookUp.objects.create(
                search_keyword_or_phrase=search_keyword_or_phrase,
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj),
            )

    remove_orphan_keyword_and_phrases()


def manage_excluded(obj, excluded_phrases_string):
    if not excluded_phrases_string:
        return

    from content.models import SearchExclusionPageLookUp, SearchKeywordOrPhrase

    # Delete existing exclusions for this page
    SearchExclusionPageLookUp.objects.filter(
        object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj),
    ).delete()

    excluded_phrases = excluded_phrases_string.split(",")

    for key_word_or_phrase_obj in excluded_phrases:
        key_word_or_phrase = (
            key_word_or_phrase_obj.lower().replace("'", "").replace('"', "").strip()
        )

        if key_word_or_phrase == "":
            continue

        search_keyword_or_phrase = SearchKeywordOrPhrase.objects.filter(
            keyword_or_phrase=key_word_or_phrase,
        ).first()

        if not search_keyword_or_phrase:
            search_keyword_or_phrase = SearchKeywordOrPhrase(
                keyword_or_phrase=key_word_or_phrase,
            )
            search_keyword_or_phrase.save()

        exclusion = SearchExclusionPageLookUp.objects.filter(
            search_keyword_or_phrase=search_keyword_or_phrase,
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).first()

        if not exclusion:
            SearchExclusionPageLookUp.objects.create(
                search_keyword_or_phrase=search_keyword_or_phrase,
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj),
            )

    remove_orphan_keyword_and_phrases()
