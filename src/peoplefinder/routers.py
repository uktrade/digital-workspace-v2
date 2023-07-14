class IngestedModelsRouter:
    databases = ["uk_staff_locations"]

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db in self.databases:
            return False

        return None
