from django.apps import AppConfig

class DjangoHistoryAppConfig(AppConfig):
    name = 'djangohistory'
    def ready(self):
        from djangohistory import signals


