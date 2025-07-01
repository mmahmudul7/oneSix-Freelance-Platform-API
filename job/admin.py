from django.contrib import admin
from .models import Category, JobPrice, Job, JobImage, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(JobPrice)
class JobPriceAdmin(admin.ModelAdmin):
    list_display = ['price', 'created_at']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'duration_days', 'average_rating', 'total_orders']
    list_filter = ['category', 'created_by']
    search_fields = ['name', 'description']


@admin.register(JobImage)
class JobImageAdmin(admin.ModelAdmin):
    list_display = ['job', 'image']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['job', 'user', 'ratings', 'created_at']
    list_filter = ['job', 'user']