import http
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django_auth_dingding.utils import import_from_settings
from django.views.generic import View
from urllib.parse import urlencode
import requests


class DingdingAuthenticationCallbackView(View):
    """Dingding client authentication callback HTTP endpoint"""

    http_method_names = ["get"]

    @staticmethod
    def get_settings(attr, *args):
        return import_from_settings(attr, *args)

    @property
    def failure_url(self):
        return self.get_settings("AUTH_DINGDING_LOGIN_REDIRECT_URL_FAILURE", "/")

    @property
    def success_url(self):
        return resolve_url(self.get_settings("AUTH_DINGDING_LOGIN_REDIRECT_URL", "/"))

    def login_failure(self):
        return HttpResponseRedirect(self.failure_url)

    def login_success(self):
        # If the user hasn't changed (because this is a session refresh instead of a
        # normal login), don't call login. This prevents invaliding the user's current CSRF token
        request_user = getattr(self.request, "user", None)
        if (
            not request_user
            or not request_user.is_authenticated
            or request_user != self.user
        ):
            auth.login(self.request, self.user)

        return HttpResponseRedirect(self.success_url)

    def get(self, request):
        """Callback handler for OIDC authorization code flow"""
        code = request.GET.get("authCode")
        if code:
            params = {
                "clientId": self.get_settings("AUTH_DINGDING_APP_KEY"),
                "clientSecret": self.get_settings("AUTH_DINGDING_APP_SECRET"),
                "code": code,
                "grantType": "authorization_code",
            }
            res = requests.post(url=self.get_settings("AUTH_DINGDING_ACCESS_TOKEN_ENDPOINT",
                                                      "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"),
                                json=params)

            # Check if the "accessToken" exists!
            if res.status_code != http.HTTPStatus.OK or "accessToken" not in res.json():
                return self.login_failure()
            access_token = res.json()["accessToken"]

            # get user info
            headers = {"x-acs-dingtalk-access-token": access_token}
            res = requests.get(url=self.get_settings("AUTH_DINGDING_USER_INFO_ENDPOINT",
                                                     "https://api.dingtalk.com/v1.0/contact/users/me"), headers=headers)

            # Check if the "unionId" exists!
            if res.status_code != http.HTTPStatus.OK or "unionId" not in res.json():
                return self.login_failure()
            union_id = res.json()["unionId"]

            # get app access_token
            params = {
                "appkey": self.get_settings("AUTH_DINGDING_APP_KEY"),
                "appsecret": self.get_settings("AUTH_DINGDING_APP_SECRET"),
            }
            res = requests.get(url="https://oapi.dingtalk.com/gettoken?{params}".format(params=urlencode(params)))

            # Check if the "access_token" exists!
            if res.status_code != http.HTTPStatus.OK or "access_token" not in res.json():
                return self.login_failure()
            access_token = res.json()["access_token"]

            # get userid by app's access_token
            res = requests.post(url="https://oapi.dingtalk.com/topapi/user/getbyunionid?access_token={access_token}"
                                .format(access_token=access_token), json={"unionid": union_id})

            if res.status_code != http.HTTPStatus.OK or "result" not in res.json():
                return self.login_failure()
            result = res.json()["result"]

            if not result["userid"]:
                return self.login_failure()

            # get user detail info by app's access_token
            res = requests.post(url=f"https://oapi.dingtalk.com/topapi/v2/user/get?access_token={access_token}"
                                .format(access_token=access_token), json={"userid": result["userid"]})
            if res.status_code != http.HTTPStatus.OK or "result" not in res.json():
                return self.login_failure()

            kwargs = {
                "request": request,
                "auth_dingding_user": res.json()["result"],
            }
            self.user = auth.authenticate(**kwargs)

            if self.user and self.user.is_active:
                return self.login_success()
        return self.login_failure()


class DingdingAuthenticationRequestView(View):
    """Dingding client authentication HTTP endpoint"""

    http_method_names = ["get"]

    def __init__(self, *args, **kwargs):
        super(DingdingAuthenticationRequestView, self).__init__(*args, **kwargs)
        self.AUTH_DINGDING_AUTHORIZATION_ENDPOINT = self.get_settings("AUTH_DINGDING_AUTHORIZATION_ENDPOINT",
                                                                      "https://login.dingtalk.com/oauth2/auth")
        self.AUTH_DINGDING_APP_KEY = self.get_settings("AUTH_DINGDING_APP_KEY")

    @staticmethod
    def get_settings(attr, *args):
        return import_from_settings(attr, *args)

    def get(self, request):
        """Dingding client authentication initialization HTTP endpoint"""
        callback_url = self.get_settings(
            "AUTH_DINGDING_AUTHENTICATION_CALLBACK_URL", "dingding_auth_authentication_callback"
        )

        params = {
            "response_type": "code",
            "scope": "openid",
            "client_id": self.AUTH_DINGDING_APP_KEY,
            "redirect_uri": callback_url,
            "state": "dddd",
            "prompt": "consent"
        }
        query = urlencode(params)
        redirect_url = "{url}?{query}".format(
            url=self.AUTH_DINGDING_AUTHORIZATION_ENDPOINT, query=query
        )
        return HttpResponseRedirect(redirect_url)
