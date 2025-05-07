from django.urls import path, include
from job.views import JobViewSet, CategoryViewSet, ReviewViewSet
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register('jobs', JobViewSet, basename='jobs')
router.register('categories', CategoryViewSet)

job_router = routers.NestedDefaultRouter(router, 'jobs', lookup='job')
job_router.register('reviews', ReviewViewSet, basename='job-review')

# urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),
    path('', include(job_router.urls)),
]