from django.urls import path
from content.views import NewsCategoryFormView

urlpatterns = [
    path("news-category/", NewsCategoryFormView.as_view(), name="news-categories"),
]
