import django_filters


class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        return any(self.form.cleaned_data.values())
