from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from solver import views

urlpatterns = [
    path("startday/", views.SolutionStartDay.as_view()),
    path("addorder/", views.SolutionAddPickup.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
