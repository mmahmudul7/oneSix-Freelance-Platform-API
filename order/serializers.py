from rest_framework import serializers
from order.models import Cart, CartItem, Order, OrderItem, OrderDelivery
from job.models import Job
from job.serializers import JobSerializer
from order.services import OrderService
from users.serializers import UserSerializer
from django.core.validators import FileExtensionValidator
from decimal import Decimal


class EmptySerializer(serializers.Serializer):
    pass


class SimpleJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'name', 'price', 'duration_days']


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
        job = Job.objects.get(pk=value)
        user = self.context['request'].user
        if job.created_by == user:
            raise serializers.ValidationError("You cannot add your own job to the cart")
        return value


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

        
class CartItemSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    total_price = serializers.SerializerMethodField(method_name='get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'job', 'quantity', 'total_price']

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.job.price.price


class CartItemDetailSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'job', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return round(obj.quantity * obj.job.price.price * Decimal(1.16), 2)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemDetailSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    def get_total_price(self, cart):
        total = Decimal(0) 
        for item in cart.items.all():
            price = item.job.price.price * Decimal(1.16)
            total += item.quantity * price
        return round(total, 2)


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart found with this id')
        
        if not CartItem.objects.filter(cart_id=cart_id).exists():
            raise serializers.ValidationError('Cart is empty')
        
        return cart_id
    
    def create(self, validated_data):
        user_id = self.context['user_id']
        cart_id = validated_data['cart_id']

        try:
            order = OrderService.create_order(user_id=user_id, cart_id=cart_id)
            return order
        except ValueError as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class OrderItemSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    job_name = serializers.SerializerMethodField() 

    class Meta:
        model = OrderItem
        fields = ['id', 'job', 'job_name', 'price', 'quantity', 'total_price']

    def get_job_name(self, obj):
        return obj.job.name


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'deadline']
        read_only_fields = ['user', 'total_price', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'status', 'deadline', 'created_at', 'updated_at', 'items']
        read_only_fields = ['user', 'created_at', 'updated_at']


class OrderDeliverySerializer(serializers.ModelSerializer):
    delivered_by = UserSerializer(read_only=True)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = OrderDelivery
        fields = ['id', 'order', 'file', 'description', 'delivered_by', 'delivered_at']
        read_only_fields = ['delivered_by', 'delivered_at']
        validators = [
            FileExtensionValidator(allowed_extensions=['pdf', 'zip', 'jpg', 'png'])
        ]

    def validate(self, data):
        order = data['order']
        job_creator = order.items.first().job.created_by
        if self.context['request'].user != job_creator:
            raise serializers.ValidationError("Only the job creator can deliver this order.")
        if order.status != Order.IN_PROGRESS:
            raise serializers.ValidationError("Order must be in progress to deliver.")
        return data
    

class CreateCustomOrderSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = serializers.IntegerField(min_value=1)
    features = serializers.CharField(max_length=1000)