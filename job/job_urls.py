from django.urls import path
from job import views


urlpatterns = [
    path('', views.JobList.as_view(), name='job-list'),
    path('<int:pk>/', views.JobDetails.as_view(), name='job-list'),
]