import logging
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.db import models
from wagtail.search import index
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, MATCH_NONE

from search_extended.backends.query import OnlyFields
from search_extended.settings import search_extended_settings
from search_extended.types import AnalysisType, SearchQueryType

from typing import Any, Collection, Dict

logger = logging.getLogger(__name__)


class MetaIndexed(type(models.Model)):

    def _get_inner_searchquery_for_querytype(
        self,
        query_str: str,
        query_type: SearchQueryType,
    ):
        match query_type:
            case SearchQueryType.PHRASE:
                query = Phrase(query_str)
            case SearchQueryType.QUERY_AND:
                query = PlainText(query_str, operator="and")
            case SearchQueryType.QUERY_OR:
                query = PlainText(query_str, operator="or")
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")
        return query

    def _get_boost_for_field_querytype_analysistype(
        self,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        match query_type:
            case SearchQueryType.PHRASE:
                query_type_boost = "SEARCH_PHRASE"
            case SearchQueryType.QUERY_AND:
                query_type_boost = "SEARCH_QUERY_AND"
            case SearchQueryType.QUERY_OR:
                query_type_boost = "SEARCH_QUERY_OR"
            case SearchQueryType.FUZZY:
                query_type_boost = "SEARCH_FUZZY"
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")

        match analysis_type:
            case AnalysisType.EXPLICIT:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.TOKENIZED:
                analysis_type_boost = "ANALYZER_TOKENIZED"
            case AnalysisType.KEYWORD:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.PROXIMITY:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case AnalysisType.FILTER:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case _:
                raise ValueError(f"{analysis_type} must be a valid AnalysisType")

        content_type = ContentType.objects.get_for_model(self)
        field_boost_key = f"{content_type.app_label}.{content_type.model}.{base_field_name}"

        return (
            search_extended_settings.get_boost_value(query_type_boost) *
            search_extended_settings.get_boost_value(analysis_type_boost) *
            search_extended_settings.get_boost_value(field_boost_key)
        )

    def _get_searchquery_for_query_field_querytype_analysistype(
        self,
        query_str: str,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        query = self._get_inner_searchquery_for_querytype(
            query_str,
            query_type,
        )

        boost = self._get_boost_for_field_querytype_analysistype(base_field_name, query_type, analysis_type)

        field_name = base_field_name
        return OnlyFields(Boost(query, boost), fields=[field_name])

    def search_query(cls, query_str, *args, **kwargs):
        """
        Uses the search_field_mapping to derive the full nested SearchQuery
        """
        query = None
        analyzer_settings = search_extended_settings.ANALYZERS
        for field_name, field_mapping in cls.search_field_mapping.items():
            if field_mapping is None or len(field_mapping) == 0:
                # Default to a single tokenized field, which is the standard approach
                field_mapping = { "search": [AnalysisType.TOKENIZED, ] }

            for field_type in field_mapping["search"]:
                if field_type in (AnalysisType.FILTER, AnalysisType.PROXIMITY,):
                    continue
                else:
                    field_analyzer_settings = analyzer_settings[field_type.value]
                    field_name_suffix = field_analyzer_settings['index_fieldname_suffix'] or ""

                    for query_type in field_analyzer_settings["query_types"]:
                        query_part = cls._get_searchquery_for_query_field_querytype_analysistype(
                            query_str,
                            f"{field_name}{field_name_suffix}",
                            SearchQueryType(query_type),
                            field_type,
                        )

                        if query is None:
                            query = query_part
                        else:
                            query = query | query_part

        logger.debug(query)
        return query

    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        # errors.extend(cls._check_search_fields(**kwargs))
        errors.append(checks.Error("Oy vey!"))
        return errors

    def _check_search_fields(cls, **kwargs):
        errors = []
        for field in cls.get_search_fields():
            message = "{model}.search_fields contains non-existent field '{name}'"
            if not cls._has_field(field.field_name):
                errors.append(
                    checks.Warning(
                        message.format(model=cls.__name__, name=field.model_field_name),
                        obj=cls,
                        id="extendedsearch.W004",
                    )
                )
        return errors

    @property
    def search_fields(cls):
        index_fields = []
        for field_name, field_mapping in cls.search_field_mapping.items():
            if field_mapping is None or len(field_mapping) == 0:
                index_fields += [SearchField(field_name)]
            for field_type in field_mapping["search"]:
                if field_type == AnalysisType.FILTER:
                    index_fields += [index.FilterField(field_name)]
                else:
                    analyzer_settings = search_extended_settings.ANALYZERS[field_type.value]
                    field_name_suffix = analyzer_settings['index_fieldname_suffix'] or ""

                    index_fields += [
                        SearchField(
                            f"{field_name}{field_name_suffix}",
                            model_field_name = field_name,
                            es_extra={
                                "search_analyzer": analyzer_settings['es_analyzer'],
                            },
                        )
                    ]

        return index_fields


class Indexed(index.Indexed, metaclass=MetaIndexed):
    def __init__(self, *args, search_field_mapping=None, **kwargs):
        if search_field_mapping is None:
            search_field_mapping = {}

        self.search_field_mapping = search_field_mapping
        return super().__init__(*args, **kwargs)


class SearchField(index.SearchField):
    def __init__(
        self,
        field_name,
        boost=None,
        partial_match=False,
        model_field_name=None,
        **kwargs
    ):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, boost=boost, partial_match=partial_match, **kwargs)

    def get_field(self, cls):
        return cls._meta.get_field(self.model_field_name)


class AutocompleteField(index.AutocompleteField):
    def __init__(
        self,
        field_name,
        model_field_name=None,
        **kwargs
    ):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, **kwargs)


class FilterField(index.FilterField):
    def __init__(
        self,
        field_name,
        model_field_name=None,
        **kwargs
    ):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, **kwargs)


class RelatedFields(index.RelatedFields):
    def __init__(
        self,
        field_name,
        model_field_name=None,
        **kwargs
    ):
        self.model_field_name = model_field_name or field_name
        super().__init__(field_name, **kwargs)
