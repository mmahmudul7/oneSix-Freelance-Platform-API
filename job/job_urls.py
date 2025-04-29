from django.urls import path
from job import views


urlpatterns = [
    path('', views.view_jobs, name='job-list'),
    path('<int:id>/', views.view_specific_job, name='job-list'),
]