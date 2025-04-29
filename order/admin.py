from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


# Inline for CartItem inside Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__first_name", "user__email")
    inlines = [CartItemInline]
    ordering = ["-created_at"]


# Inline for OrderItem inside Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("total_price",)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__first_name", "user__email")
    inlines = [OrderItemInline]
    ordering = ["-created_at"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "job", "freelancer", "price", "total_price")
    search_fields = ("order__id", "job__name", "freelancer__first_name")
    list_filter = ("freelancer",)
    readonly_fields = ("total_price",)
