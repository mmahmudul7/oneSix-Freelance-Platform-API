from rest_framework import serializers
from order.models import Cart, CartItem, Order, OrderItem
from job.models import Job


class SimpleJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'name', 'price']


class AddCartItemSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['id', 'job_id', 'quantity']

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        job_id = self.validated_data['job_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, job_id=job_id)
            cart_item.quantity += quantity
            self.instance = cart_item.save()
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)

        return self.instance
    
    def validate_job_id(self, value):
        if not Job.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Job with id {value} does not exists")
        return value


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

        
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
    

class OrderItemSerializer(serializers.ModelSerializer):
    job = SimpleJobSerializer()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'job', 'price', 'quantity', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many = True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total_price', 'created_at', 'items']