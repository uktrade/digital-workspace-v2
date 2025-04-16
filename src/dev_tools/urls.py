from django.urls import path

from dev_tools.views import change_user_view, login_view


app_name = "dev_tools"

urlpatterns = [
    path("login", login_view, name="login"),
    path("change-user", change_user_view, name="change-user"),
]
