from django.urls import path
from job import views


urlpatterns = [
    path('', views.view_categories, name='category-list'),
    path('<int:pk>/', views.view_specific_category, name='view-specific-category'),
]