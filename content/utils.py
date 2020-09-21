from django.contrib.contenttypes.models import ContentType


def remove_orhpan_keyword_and_phrases():
    from content.models import (
        SearchExclusionPageLookUp,
        SearchPinPageLookUp,
        SearchKeywordOrPhrase,
    )

    # Remove all search exclusions not associated with a page
    exclude_look_up_ids = SearchExclusionPageLookUp.objects.all().values_list(
        "search_result_exclusion__pk",
    )
    pin_look_up_ids = SearchPinPageLookUp.objects.all().values_list(
        "search_result_exclusion__pk",
    )

    SearchKeywordOrPhrase.objects.exclude(
        pk__in=exclude_look_up_ids,
    ).exclude(
        pk__in=pin_look_up_ids,
    ).delete()


def manage_pinned(obj, pinned_phrases):
    from content.models import (
        SearchKeywordOrPhrase,
        SearchPinPageLookUp,
    )

    # Delete existing pins for this page
    SearchPinPageLookUp.objects.filter(
        object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj),
    ).delete()

    for key_word_or_phrase in pinned_phrases:
        search_result_exclusion = SearchKeywordOrPhrase.objects.filter(
            keyword_or_phrase=key_word_or_phrase[1],
        ).first()

        if not search_result_exclusion:
            search_result_exclusion = SearchKeywordOrPhrase(
                keyword_or_phrase=key_word_or_phrase[1],
            )
            search_result_exclusion.save()

        pin = SearchPinPageLookUp.objects.filter(
            search_result_exclusion=search_result_exclusion,
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).first()

        if not pin:
            SearchPinPageLookUp.objects.create(
                search_result_exclusion=search_result_exclusion,
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj),
            )

    remove_orhpan_keyword_and_phrases()


def manage_excluded(obj, excluded_phrases):
    from content.models import (
        SearchExclusionPageLookUp,
        SearchKeywordOrPhrase,
    )

    # Delete existing exclusions for this page
    SearchExclusionPageLookUp.objects.filter(
        object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj),
    ).delete()

    for key_word_or_phrase in excluded_phrases:
        search_result_exclusion = SearchKeywordOrPhrase.objects.filter(
            keyword_or_phrase=key_word_or_phrase[1],
        ).first()

        if not search_result_exclusion:
            search_result_exclusion = SearchKeywordOrPhrase(
                keyword_or_phrase=key_word_or_phrase[1],
            )
            search_result_exclusion.save()

        exclusion = SearchExclusionPageLookUp.objects.filter(
            search_result_exclusion=search_result_exclusion,
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        ).first()

        if not exclusion:
            SearchExclusionPageLookUp.objects.create(
                search_result_exclusion=search_result_exclusion,
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj),
            )

    remove_orhpan_keyword_and_phrases()
