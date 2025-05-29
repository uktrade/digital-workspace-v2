import django_filters


class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        return any(self.form.changed_data)

    def applied_filters(self) -> dict[str, list[str]]:
        try:
            k_v_pairs = self.form.data.lists()
        except AttributeError:
            k_v_pairs = self.form.data.items()

        output = {}
        for key, values in k_v_pairs:
            if key in self.form.fields.keys() and values not in [[], [""]]:
                output[key] = values
        return output
