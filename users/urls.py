from django.urls import path
from users.views import UserProfileViewSet, PortfolioViewSet

urlpatterns = [
    path('users/search/', UserProfileViewSet.as_view({'get': 'search'}), name='user-search'),
    path('portfolios/my/', PortfolioViewSet.as_view({'get': 'my_portfolio'}), name='portfolio-my'),
    path('portfolios/<int:pk>/', PortfolioViewSet.as_view({'get': 'retrieve'}), name='portfolio-detail'),
]