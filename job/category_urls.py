from django.urls import path
from job import views


urlpatterns = [
    path('', views.CategoriesList.as_view(), name='category-list'),
    path('<int:pk>/', views.CategoryDetails.as_view(), name='view-specific-category'),
]