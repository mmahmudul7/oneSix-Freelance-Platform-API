from django.contrib import admin
from .models import Job, Category, JobImage, Review


class JobImageInline(admin.TabularInline):
    model = JobImage
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("name",)
    inlines = [JobImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # list_display = ("job", "user", "ratings", "created_at")
    list_display = ("job", "user", "created_at")
    # list_filter = ("ratings",)
    search_fields = ("job__name", "user__first_name")
