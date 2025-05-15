import django_filters


class FilterSet(django_filters.FilterSet):
    def has_filters_applied(self) -> bool:
        return any(self.form.changed_data)

    def applied_filters(self):
        return {self.form.fields[field_name].label: self.form.data.getlist(field_name) for field_name in self.form.data.keys() if self.form.data.getlist(field_name) not in [[], [""],]}
        # output = {}
        # print("\\\\\\\\\\\\\\\\\\", self.form.data)
        # for field_name, values in self.form.data.items():
        #     print ("!!!!!!!!", field_name, values)
        #     if values not in [[], "", [""],]:
        #         print(">>>>>", values)
        #         output[self.form.fields[field_name].label] = values
        # return output
