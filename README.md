### Dingo-Auth-Dingding

a dingding app auth django app. you should have follow this [section](https://open.dingtalk.com/document/orgapp/tutorial-obtaining-user-personal-information) to configure dingding app.

#### Quick start

1. Add "polls" to your INSTALLED_APPS setting like this::

```python
 INSTALLED_APPS = [
 ...
 'django_auth_dingding',
 ]
```

2. Include the polls URLconf in your project urls.py like this::

```python
path('dingding/', include("django_auth_dingding.urls")),
```

3. Add ding_user_id field to User Model like this::

```python
from django.contrib.auth.models import AbstractUser

class Users(AbstractUser):
    ...
    ding_user_id = models.CharField("钉钉UserID", max_length=64, blank=True)
```

4. Setting config in your django's settings.py like this::

```python
INSTALLED_APPS += ("django_auth_dingding",)
AUTHENTICATION_BACKENDS = (
    "django_auth_dingding.auth.DingdingAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)
DINGDING_AUTH_AUTHENTICATION_CALLBACK_URL = env("DINGDING_AUTH_AUTHENTICATION_CALLBACK_URL")
DINGDING_AUTH_APP_KEY = env("DINGDING_AUTH_APP_KEY")
DINGDING_AUTH_APP_SECRET = env("DINGDING_AUTH_APP_SECRET")
```

5. Run `python manage.py migrate` to Modify the User models.

6. Browser visit `http://{host}:{port}/dingding/authenticate/` will redirect to dingding auth page