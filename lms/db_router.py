class LmsDatabaseRouter:
    """2조 LMS 모델을 assignment_lms DB로 라우팅한다.

    settings.py에 DATABASE_ROUTERS와 assignment_lms alias를 추가하기 전까지는
    실제 라우팅이 활성화되지 않는다. 신규 파일로 먼저 확보한다.
    """

    LMS_APP_LABEL = "lms"
    LMS_DB_ALIAS = "assignment_lms"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.LMS_APP_LABEL:
            return self.LMS_DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.LMS_APP_LABEL:
            return self.LMS_DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == self.LMS_APP_LABEL or obj2._meta.app_label == self.LMS_APP_LABEL:
            return obj1._state.db == obj2._state.db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.LMS_APP_LABEL:
            return False
        return None
