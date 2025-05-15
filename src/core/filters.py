import django_filters


class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        return any(self.form.changed_data)

    def applied_filters(self) -> dict[str, list[str]]:
        return {
            field_name: values
            for field_name, values in self.form.data.lists()
            if self.form.data.getlist(field_name) not in [[], [""],]
        }
