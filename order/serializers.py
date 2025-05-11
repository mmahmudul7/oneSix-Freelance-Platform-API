from rest_framework import serializers
from order.models import Cart, CartItem
from job.models import Job


class SimpleJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'name', 'price']


class CartItemSerializer(serializers.ModelSerializer):
    job = SimpleJobSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'job', 'quantity', 'job', 'total_price']

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.job.price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']

    def get_total_price(self, cart: Cart):
        return sum([item.job.price * item.quantity for item in cart.items.all()])

