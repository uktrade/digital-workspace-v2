from extended_search.index import ModelFieldNameMixin


class Base:
    def __init__(self, *args, **kwargs) -> None:
        ...

    def get_value(self, obj) -> None:
        ...

    def get_definition_model(self, cls) -> None:
        ...


class MixedIn(ModelFieldNameMixin, Base):
    ...
