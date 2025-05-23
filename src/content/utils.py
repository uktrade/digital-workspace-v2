from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags
from django.utils.text import Truncator
from wagtail import blocks
from wagtail.blocks.struct_block import StructValue

from content import blocks as content_blocks
from peoplefinder.models import TeamMember


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

    SearchKeywordOrPhrase.objects.exclude(
        pk__in=exclude_look_up_ids,
    ).exclude(
        pk__in=pin_look_up_ids,
    ).delete()


def manage_pinned(obj, pinned_phrases_string):
    from content.models import SearchKeywordOrPhrase, SearchPinPageLookUp

    # Delete existing pins for this page
    SearchPinPageLookUp.objects.filter(
        object_id=obj.pk,
        content_type=ContentType.objects.get_for_model(obj),
    ).delete()

    if not pinned_phrases_string:
        return

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


def truncate_on_newline(text):
    newline_replace_chars = ["\n"]

    # Find the last newline character.
    newline_index = {}
    for newline_char in newline_replace_chars:
        newline_index[newline_char] = text.find(newline_char)

    last_newline_index = max(newline_index.values())

    if last_newline_index < 0:
        return text

    # Set everything before the last newline character (excluding the
    # character itself)
    return text[:last_newline_index]


def truncate_words_and_chars(
    text,
    words=40,
    chars=700,
    truncate=None,
    html=False,
):
    """
    Truncates the given text to the _minimum_ value of both words and chars,
    at a word ending
    """
    chars_result = Truncator(text).chars(num=chars, truncate="", html=html)
    newline_result = truncate_on_newline(chars_result)
    words_result = Truncator(newline_result).words(
        num=words, truncate=truncate, html=html
    )
    return words_result


def get_search_content_for_block(
    block: blocks.Block, value: StructValue
) -> tuple[list[str], list[str]]:
    search_headings = []
    search_content = []

    if isinstance(block, content_blocks.HeadingBlock):
        search_headings.append(
            strip_tags(" ".join(block.get_searchable_content(value)))
        )

    elif isinstance(block, blocks.StructBlock):
        block_headings = ""
        if hasattr(block, "get_searchable_heading"):
            block_headings = block.get_searchable_heading(value)

        for child_block in block.child_blocks.values():
            child_value = value[child_block.name]
            child_headings, child_content = get_search_content_for_block(
                child_block, child_value
            )
            search_content += child_content

            if not block_headings:
                block_headings = " ".join(child_headings)

        search_headings.append(block_headings)

    else:
        if hasattr(block, "get_searchable_content"):
            search_content.append(
                strip_tags(" ".join(block.get_searchable_content(value)))
            )
        else:
            search_content.append(strip_tags(str(block.value)))

    return search_headings, search_content
