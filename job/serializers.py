from rest_framework import serializers
from decimal import Decimal
from job.models import Category, Job, Review, JobImage, JobPrice
from django.contrib.auth import get_user_model


class CategorySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'job_count']

    def validate_name(self, value):
        if Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class JobImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobImage
        fields = ['id', 'image']


class JobPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPrice
        fields = ['id', 'price']


class JobSerializer(serializers.ModelSerializer):
    cart_price = serializers.SerializerMethodField(method_name='calculate_cart')
    images = JobImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=True)
    price = serializers.PrimaryKeyRelatedField(queryset=JobPrice.objects.all(), required=True)
    average_rating = serializers.ReadOnlyField()
    total_orders = serializers.ReadOnlyField()

    def validate(self, data):
        # All required fields are provided
        required_fields = ['name', 'description', 'price', 'category', 'duration_days']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise serializers.ValidationError({field: f"{field} is required."})
        return data

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 day.")
        return value
    
    class Meta:
        model = Job
        fields = ['id', 'name', 'description', 'price', 'category', 'cart_price', 'images', 'created_by', 'duration_days', 'average_rating', 'total_orders', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'cart_price', 'average_rating', 'total_orders']

    def calculate_cart(self, job):
        return round(job.price.price * Decimal(1.16), 2)
    
    def validate_price(self, price):
        if not JobPrice.objects.filter(pk=price.id).exists():
            raise serializers.ValidationError("Invalid price selected")
        return price


class SimpleUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(method_name='get_current_user_name')

    class Meta:
        model = get_user_model()
        fields = ['id', 'name']

    def get_current_user_name(self, obj):
        return obj.get_full_name()


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(method_name='get_user')
    reviewer_role = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'job', 'ratings', 'comment', 'reviewer_role']
        read_only_fields = ['user', 'job', 'reviewer_role']

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data
    
    def get_reviewer_role(self, obj):
        order = obj.job.order_items.filter(buyer=obj.user, is_completed=True).first()
        return 'buyer' if order else 'seller'

    def create(self, validated_data):
        job_id = self.context['job_id']
        return Review.objects.create(job_id=job_id, **validated_data)
    

class JobSearchSerializer(serializers.Serializer):  # job search
    keyword = serializers.CharField(required=False, allow_blank=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    min_rating = serializers.FloatField(required=False)
    max_duration_days = serializers.IntegerField(required=False)
    creator_email = serializers.CharField(required=False, allow_blank=True)
    sort_by = serializers.ChoiceField(
        choices=['price_asc', 'price_desc', 'rating_desc', 'orders_desc'],
        required=False
    )
