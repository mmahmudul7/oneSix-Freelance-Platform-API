from django.urls import path, include
from rest_framework_nested import routers
from job.views import JobViewSet, CategoryViewSet, ReviewViewSet, JobImageViewSet, JobPriceViewSet
from order.views import CartViewSet, CartItemViewSet, OrderDeliveryViewSet, OrderViewSet, initiate_payment, payment_success, payment_fail, payment_cancel
from users.views import UserProfileViewSet, PortfolioViewSet
from messaging.views import MessageViewSet, CustomOfferViewSet
# from djoser.views import UserViewSet


# Main router
router = routers.DefaultRouter()
# router.register('users', UserViewSet, basename='users')
router.register('categories', CategoryViewSet, basename='categories')
router.register('jobs', JobViewSet, basename='jobs')
router.register('job-price', JobPriceViewSet, basename='job-price')
router.register('carts', CartViewSet, basename='carts')
router.register('orders', OrderViewSet, basename='orders')
router.register('profiles', UserProfileViewSet, basename='profiles')
router.register('portfolio', PortfolioViewSet, basename='portfolio')
router.register('message', MessageViewSet, basename='message')
router.register('custom-offers', CustomOfferViewSet, basename='custom-offers')
router.register('deliveries', OrderDeliveryViewSet, basename='deliveries')

# nested router
job_router = routers.NestedDefaultRouter(router, 'jobs', lookup='job')
job_router.register('reviews', ReviewViewSet, basename='job-review')
job_router.register('images', JobImageViewSet, basename='job-images')

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', CartItemViewSet, basename='cart-item')


# urlpatterns = router.urls
# Final URLs
urlpatterns = [
    # Main API root
    path('', include(router.urls)),
    path('', include(job_router.urls)),
    path('', include(cart_router.urls)),

    # path('auth/', include(router.urls)),
    # Djoser auth routes
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('users.urls')),
    path('payment/initiate/', initiate_payment, name='initiate_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/fail/', payment_fail, name='payment-fail'),
    path('payment/cancel/', payment_cancel, name='payment-cancel'),
]