from django.core.exceptions import ValidationError


def validate_description_word_count(value):
    word_count_description = len(value.split())

    if word_count_description > 30:
        raise ValidationError(
            "Description cannot be more than 30 words",
        )
