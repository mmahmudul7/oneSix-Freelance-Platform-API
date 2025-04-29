from django.urls import path, include


urlpatterns = [
    path('jobs/', include('job.job_urls')),
    path('categories/', include('job.category_urls'))
]