from django.urls import path
from job import views


urlpatterns = [
    path('', views.ViewJobs.as_view(), name='job-list'),
    path('<int:id>/', views.ViewSpecificJob.as_view(), name='job-list'),
]