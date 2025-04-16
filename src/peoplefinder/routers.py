from django.conf import settings


class IngestedModelsRouter:
    databases = settings.INGESTED_MODELS_DATABASES

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db in self.databases:
            return False

        return None
