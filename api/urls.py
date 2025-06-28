from django.urls import path, include
from job.views import JobViewSet, CategoryViewSet, ReviewViewSet
from order.views import CartViewSet, CartItemViewSet
from rest_framework_nested import routers


router = routers.DefaultRouter()
router.register('jobs', JobViewSet, basename='jobs')
router.register('categories', CategoryViewSet)
router.register('carts', CartViewSet, basename='carts')

job_router = routers.NestedDefaultRouter(router, 'jobs', lookup='job')
job_router.register('reviews', ReviewViewSet, basename='job-review')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', CartItemViewSet, basename='cart-item')

# urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),
    path('', include(job_router.urls)),
    path('', include(cart_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]