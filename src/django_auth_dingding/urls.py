from django.urls import path
from django.utils.module_loading import import_string

DEFAULT_CALLBACK_CLASS = "django_auth_dingding.views.DingdingAuthenticationCallbackView"
DingdingCallbackClass = import_string(DEFAULT_CALLBACK_CLASS)

DEFAULT_AUTHENTICATE_CLASS = "django_auth_dingding.views.DingdingAuthenticationRequestView"
DingdingAuthenticateClass = import_string(DEFAULT_AUTHENTICATE_CLASS)

urlpatterns = [
    path("callback/", DingdingCallbackClass.as_view(), name="dingding_authentication_callback"),
    path("authenticate/", DingdingAuthenticateClass.as_view(), name="dingding_authentication_init"),
]
