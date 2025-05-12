import django_filters


class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        return any(self.form.changed_data)

    def get_applied_filters(self):
        return self.form.changed_data
