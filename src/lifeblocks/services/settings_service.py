from lifeblocks.models.settings import Settings


class SettingsService:
    def __init__(self, session):
        self.session = session

    def get_setting(self, key, default=None):
        setting = self.session.query(Settings).filter_by(key=key).first()
        return setting.value if setting else default

    def set_setting(self, key, value):
        setting = self.session.query(Settings).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            self.session.add(setting)
        self.session.commit()
