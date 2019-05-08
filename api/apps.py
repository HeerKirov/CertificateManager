from django.apps import AppConfig
from django.db.models.signals import post_migrate
from . import enums


def check_initial_user():
    from . import models as app_models
    import config
    print('Checking initial user... ', end='')
    if config.INITIAL_ADMIN_USER is not None:
        username = '%s:%s' % (enums.UserType.admin, config.INITIAL_ADMIN_USER['username'])
        if app_models.User.objects.filter(username=username).exists():
            print('Done')
        else:
            print('Not exist. Creating initial user...')
            user = app_models.User(username=username,
                                   is_staff=True, is_superuser=True, first_name=config.INITIAL_ADMIN_USER['name'])
            user.set_password(config.INITIAL_ADMIN_USER['password'])
            user.save()
    else:
        print('Skipped')


def callback(sender, **kwarg):
    check_initial_user()


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        post_migrate.connect(callback, sender=self)
