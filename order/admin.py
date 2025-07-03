from django.contrib import admin
from order.models import Cart, CartItem, Order, OrderItem, OrderDelivery

# Inline for CartItem inside Cart
class CartItemInline(admin.TabularInline):
    """
    Inline admin interface for CartItem model within CartAdmin.
    Displays cart items associated with a cart in a tabular format.
    """
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('job', 'quantity', 'total_price')

    def total_price(self, obj):
        """Calculate total price for a cart item."""
        return obj.quantity * obj.job.price
    total_price.short_description = 'Total Price'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin interface for Cart model.
    Displays and manages user carts with associated items.
    """
    list_display = ('id', 'user', 'created_at', 'total_price')
    search_fields = ('user__first_name', 'user__email')
    inlines = [CartItemInline]
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    def total_price(self, obj):
        """Calculate total price of all items in the cart."""
        return sum(item.quantity * item.job.price for item in obj.items.all())
    total_price.short_description = 'Total Price'

# Inline for OrderItem inside Order
class OrderItemInline(admin.TabularInline):
    """
    Inline admin interface for OrderItem model within OrderAdmin.
    Displays order items associated with an order in a tabular format.
    """
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price', 'freelancer')
    fields = ('job', 'price', 'quantity', 'total_price', 'freelancer')

    def freelancer(self, obj):
        """Display the freelancer (job creator) for the order item."""
        return obj.job.created_by
    freelancer.short_description = 'Freelancer'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    Manages orders with filtering, searching, and inline order items.
    """
    list_display = ('id', 'user', 'status', 'total_price', 'created_at', 'deadline')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__first_name', 'user__email')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_price')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin interface for CartItem model.
    Manages individual cart items with job and quantity details.
    """
    list_display = ('cart', 'job', 'quantity', 'total_price')
    search_fields = ('cart__id', 'job__name')
    readonly_fields = ('total_price',)

    def total_price(self, obj):
        """Calculate total price for the cart item."""
        return obj.quantity * obj.job.price
    total_price.short_description = 'Total Price'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin interface for OrderItem model.
    Manages individual order items with job, freelancer, and price details.
    """
    list_display = ('order', 'job', 'freelancer', 'price', 'quantity', 'total_price')
    search_fields = ('order__id', 'job__name', 'freelancer__first_name', 'freelancer__email')
    list_filter = ('freelancer',)
    readonly_fields = ('total_price',)

    def freelancer(self, obj):
        """Display the freelancer (job creator) for the order item."""
        return obj.job.created_by
    freelancer.short_description = 'Freelancer'

@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    """
    Admin interface for OrderDelivery model.
    Manages order deliveries with order, deliverer, and file details.
    """
    list_display = ('id', 'order', 'delivered_by', 'delivered_at')
    search_fields = ('order__id', 'delivered_by__first_name', 'delivered_by__email')
    list_filter = ('delivered_at',)
    readonly_fields = ('delivered_at',)

# from django.contrib import admin
# from order.models import Cart, CartItem, Order, OrderItem
# # Register your models here.


# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user']


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'status']


# admin.site.register(CartItem)
# admin.site.register(OrderItem)

##########################
# from django.contrib import admin
# from .models import Cart, CartItem, Order, OrderItem


# # Inline for CartItem inside Cart
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 0


# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ("user", "created_at")
#     search_fields = ("user__first_name", "user__email")
#     inlines = [CartItemInline]
#     ordering = ["-created_at"]


# # Inline for OrderItem inside Order
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     readonly_fields = ("total_price",)
#     extra = 0


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "status", "total_price", "created_at")
#     list_filter = ("status", "created_at")
#     search_fields = ("id", "user__first_name", "user__email")
#     inlines = [OrderItemInline]
#     ordering = ["-created_at"]
#     readonly_fields = ("id", "created_at", "updated_at")


# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ("order", "job", "freelancer", "price", "total_price")
#     search_fields = ("order__id", "job__name", "freelancer__first_name")
#     list_filter = ("freelancer",)
#     readonly_fields = ("total_price",)
