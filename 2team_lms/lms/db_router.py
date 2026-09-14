"""Preserve Core ownership and the existing LMS migration labels."""
class LmsDatabaseRouter:
    LMS_APPS = {"core", "tutor", "github_sync"}
    READ_ONLY_APPS = {"accounts_client", "lms_client"}

    def db_for_read(self, model, **hints):
        label = model._meta.app_label
        if label == "accounts_client":
            return "default"
        if label in self.LMS_APPS or label == "lms_client":
            return "assignment_lms"
        return None

    def db_for_write(self, model, **hints):
        label = model._meta.app_label
        if label in self.READ_ONLY_APPS:
            raise RuntimeError("Read-only integration models cannot write data")
        if label in self.LMS_APPS:
            return "assignment_lms"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if labels & self.LMS_APPS:
            return labels <= self.LMS_APPS
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.READ_ONLY_APPS or app_label == "lms":
            return False
        if db == "assignment_lms":
            return app_label in self.LMS_APPS
        if app_label in self.LMS_APPS:
            return False
        return None
