from django.urls import path, include
from rest_framework.routers import DefaultRouter
from job.views import JobViewSet, CategoryViewSet

router = DefaultRouter()
router.register('jobs', JobViewSet)
router.register('categories', CategoryViewSet)

urlpatterns = router.urls

# urlpatterns = [
#     path('', include('router.urls')),
#     path('contact/'),
# ]