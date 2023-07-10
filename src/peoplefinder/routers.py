from peoplefinder.legacy_models import LegacyPeopleFinderModel


class LegacyPeopleFinderRouter:
    def db_for_read(self, model, **hints):
        if issubclass(model, LegacyPeopleFinderModel):
            return "legacy_peoplefinder"

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "legacy_peoplefinder":
            return False

        return None


class IngestedModelsRouter:
    databases = ["uk_staff_locations"]

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db in self.databases:
            return False

        return None
