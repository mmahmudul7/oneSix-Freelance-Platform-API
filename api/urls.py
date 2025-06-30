from django.urls import path, include
from rest_framework_nested import routers
from job.views import JobViewSet, CategoryViewSet, ReviewViewSet, JobImageViewSet, JobPriceViewSet
from order.views import CartViewSet, CartItemViewSet, OrderViewset
from users.views import UserProfileViewSet, PortfolioViewSet
from messaging.views import MessageViewSet, CustomOfferViewSet


router = routers.DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('jobs', JobViewSet, basename='jobs')
router.register('job-price', JobPriceViewSet, basename='job-price')
router.register('carts', CartViewSet, basename='carts')
router.register('orders', OrderViewset, basename='orders')
router.register('profiles', UserProfileViewSet, basename='profiles')
router.register('portfolio', PortfolioViewSet, basename='portfolio')
router.register('message', MessageViewSet, basename='message')
router.register('custom-offers', CustomOfferViewSet, basename='custom-offers')

job_router = routers.NestedDefaultRouter(router, 'jobs', lookup='job')
job_router.register('reviews', ReviewViewSet, basename='job-review')
job_router.register('images', JobImageViewSet, basename='job-images')

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