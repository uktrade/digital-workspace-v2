import inspect
import logging
from typing import List, Optional

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import RelatedField
from wagtail.search.index import BaseField, RelatedFields

from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


class WagtailBaseField(BaseField):
    """
    Overrides from https://github.com/wagtail/wagtail/pull/11118/files
    """

    def __init__(self, field_name, model_field_name=None, **kwargs):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, **kwargs)

    def get_field(self, cls):
        if self.model_field_name:
            return cls._meta.get_field(self.model_field_name)
        return cls._meta.get_field(self.field_name)

    def get_attname(self, cls):
        if self.model_field_name and self.model_field_name != self.field_name:
            return self.field_name
        try:
            field = self.get_field(cls)
            return field.attname
        except FieldDoesNotExist:
            return self.field_name

    def get_definition_model(self, cls):
        try:
            field = self.get_field(cls)
            return field.model
        except FieldDoesNotExist:
            model_field_name = self.model_field_name
            if model_field_name:
                name_parts = model_field_name.split(".")
                if len(name_parts) > 1:
                    model_field_name = name_parts[0]

            # Find where it was defined by walking the inheritance tree
            for base_cls in inspect.getmro(cls):
                if (
                    self.field_name in base_cls.__dict__
                    or model_field_name in base_cls.__dict__
                ):
                    return base_cls

    def get_value(self, obj):
        from taggit.managers import TaggableManager

        try:
            field = self.get_field(obj.__class__)
            value = field.value_from_object(obj)
            if hasattr(field, "get_searchable_content"):
                value = field.get_searchable_content(value)
            elif isinstance(field, TaggableManager):
                # As of django-taggit 1.0, value_from_object returns a list of Tag objects,
                # which matches what we want
                pass
            elif isinstance(field, RelatedField):
                # The type of the ForeignKey may have a get_searchable_content method that we should
                # call. Firstly we need to find the field its referencing but it may be referencing
                # another RelatedField (eg an FK to page_ptr_id) so we need to run this in a while
                # loop to find the actual remote field.
                remote_field = field
                while isinstance(remote_field, RelatedField):
                    remote_field = remote_field.target_field
                if hasattr(remote_field, "get_searchable_content"):
                    value = remote_field.get_searchable_content(value)
            return value
        except FieldDoesNotExist:
            value = getattr(obj, self.field_name, None)
            if value is None:
                value = getattr(obj, self.model_field_name, None)
            if hasattr(value, "__call__"):
                value = value()
            return value


class WagtailIndexedField(WagtailBaseField):
    """
    Overrides from https://github.com/wagtail/wagtail/pull/11118/files
    """

    def __init__(
        self,
        *args,
        boost: Optional[float] = None,
        search: bool = False,
        search_kwargs: Optional[dict] = None,
        autocomplete: bool = False,
        autocomplete_kwargs: Optional[dict] = None,
        filter: bool = False,
        filter_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not search_kwargs:
            search_kwargs = {}
        if not autocomplete_kwargs:
            autocomplete_kwargs = {}
        if not filter_kwargs:
            filter_kwargs = {}

        self.boost = self.kwargs["boost"] = boost
        self.search = self.kwargs["search"] = search
        self.search_kwargs = self.kwargs["search_kwargs"] = search_kwargs
        self.autocomplete = self.kwargs["autocomplete"] = autocomplete
        self.autocomplete_kwargs = self.kwargs[
            "autocomplete_kwargs"
        ] = autocomplete_kwargs
        self.filter = self.kwargs["filter"] = filter
        self.filter_kwargs = self.kwargs["filter_kwargs"] = filter_kwargs

    def generate_fields(self, parent_field: BaseField = None) -> List[BaseField]:
        generated_fields = []
        field_name = self.model_field_name
        if parent_field:
            field_name = f"{parent_field.model_field_name}.{field_name}"

        if self.search:
            generated_fields.append(self.generate_search_field(field_name))
        if self.autocomplete:
            generated_fields.append(self.generate_autocomplete_field(field_name))
        if self.filter:
            generated_fields.append(self.generate_filter_field(field_name))

        return generated_fields

    def generate_search_field(self, field_name: str):
        from extended_search.index import SearchField

        return SearchField(
            field_name,
            model_field_name=self.model_field_name,
            **self.search_kwargs,
        )

    def generate_autocomplete_field(self, field_name: str):
        from extended_search.index import AutocompleteField

        return AutocompleteField(
            field_name,
            model_field_name=self.model_field_name,
            **self.autocomplete_kwargs,
        )

    def generate_filter_field(self, field_name: str):
        from extended_search.index import FilterField

        return FilterField(
            field_name,
            model_field_name=self.model_field_name,
            **self.filter_kwargs,
        )


class WagtailRelatedFields(RelatedFields):
    def __init__(self, field_name, fields, model_field_name=None, *args, **kwargs):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, fields, *args, **kwargs)


####################
# Extended Search
####################


class RelatedIndexedFields(WagtailRelatedFields):
    def _get_related_mapping_object(self):
        fields = []
        for field in self.fields:
            field_mapping = field.get_mapping()
            field_mapping["parent_model_field"] = self.model_field_name
            fields += [field_mapping]
        return {
            "related_fields": fields,
        }

    def get_mapping(self):
        mapping = super().get_mapping()
        return mapping | self._get_related_mapping_object()


# class AbstractBaseField:
#     def __init__(self, name, model_field_name=None, boost=1.0, **kwargs):
#         self.name = kwargs["name"] = name
#         self.model_field_name = kwargs["model_field_name"] = model_field_name or name
#         self.boost = kwargs["boost"] = boost
#         self.kwargs = kwargs

#     def _get_base_mapping_object(self):
#         return {
#             "name": self.name,
#             "model_field_name": self.model_field_name,
#             "boost": self.boost,
#             "parent_model_field": None,  # when is not None, field is Related
#         }

#     def get_mapping(self):
#         return self._get_base_mapping_object()

#     @property
#     def mapping(self):
#         return self.get_mapping()


class BaseIndexedField(WagtailIndexedField):
    def __init__(
        self,
        *args,
        fuzzy: bool = False,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.fuzzy = self.kwargs["fuzzy"] = fuzzy
        if self.fuzzy:
            self.search = True

    def _get_search_mapping_object(self):
        if not self.search:
            return {}

        mapping = {"search": []}

        if self.fuzzy:
            mapping["search"] = [
                AnalysisType.TOKENIZED,
            ]
            mapping["fuzzy"] = []

        return mapping

    def _get_autocomplete_mapping_object(self):
        if not self.autocomplete:
            return {}

        return {"autocomplete": []}

    def _get_filter_mapping_object(self):
        if not self.filter:
            return {}

        return {"filter": []}

    def get_mapping(self):
        mapping = super().get_mapping()
        if self.search:
            mapping = mapping | self._get_search_mapping_object()
        if self.autocomplete:
            mapping = mapping | self._get_autocomplete_mapping_object()
        if self.filter:
            mapping = mapping | self._get_filter_mapping_object()
        return mapping


class IndexedField(BaseIndexedField):
    def __init__(
        self,
        *args,
        tokenized=False,
        explicit=False,
        keyword=False,
        proximity=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tokenized = self.kwargs["tokenized"] = tokenized
        self.explicit = self.kwargs["explicit"] = explicit
        self.keyword = self.kwargs["keyword"] = keyword
        self.proximity = self.kwargs["proximity"] = proximity

        if tokenized or explicit or keyword:
            self.search = True

        if proximity:
            self.filter = True

    def _get_search_mapping_object(self):
        mapping = super()._get_search_mapping_object()
        if self.tokenized and AnalysisType.TOKENIZED not in mapping["search"]:
            mapping["search"] += [AnalysisType.TOKENIZED]
        if self.explicit:
            mapping["search"] += [AnalysisType.EXPLICIT]
        if self.keyword:
            mapping["search"] += [AnalysisType.KEYWORD]
        return mapping

    def _get_filter_mapping_object(self):
        mapping = super()._get_filter_mapping_object()
        if self.proximity and AnalysisType.PROXIMITY not in mapping["filter"]:
            mapping["filter"] += [
                AnalysisType.PROXIMITY
            ]  # @TODO is this the right way to index proximity
        return mapping
