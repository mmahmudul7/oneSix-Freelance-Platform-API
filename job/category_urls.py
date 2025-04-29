from django.urls import path
from job import views


urlpatterns = [
    path('', views.ViewCategories.as_view(), name='category-list'),
    path('<int:pk>/', views.ViewSpecificCategory.as_view(), name='view-specific-category'),
]