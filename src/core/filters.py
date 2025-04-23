import django_filters

class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        print("----------", self.form.cleaned_data)
        return any(self.form.cleaned_data.values())
