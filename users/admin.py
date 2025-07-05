from django.contrib import admin
from users.models import User, Portfolio


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'location', 'average_rating', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'bio', 'location']
    list_filter = ['location', 'is_active']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['user']