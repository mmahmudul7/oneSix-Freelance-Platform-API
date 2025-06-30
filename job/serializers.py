from rest_framework import serializers
from decimal import Decimal
from job.models import Category, Job, Review, JobImage
from django.contrib.auth import get_user_model


class CategorySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'job_count']

    def validate_name(self, value):
        # Ensure category name is unique
        if Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class JobImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobImage
        fields = ['id', 'image']


class JobSerializer(serializers.ModelSerializer):
    cart_price = serializers.SerializerMethodField(method_name='calculate_cart')
    images = JobImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 day.")
        return value
    
    class Meta:
        model = Job
        fields = ['id', 'name', 'description', 'price', 'category', 'cart_price', 'images', 'created_by', 'duration_days', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'cart_price']

    def calculate_cart(self, job):
        return round(job.price * Decimal(1.16), 2)
    
    def validate_price(self, price):
        if price < 0:
            raise serializers.ValidationError('Price could not be negative')
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

    class Meta:
        model = Review
        fields = ['id', 'user', 'job', 'ratings', 'comment']
        read_only_fields = ['user', 'job']

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data

    def create(self, validated_data):
        job_id = self.context['job_id']
        return Review.objects.create(job_id=job_id, **validated_data)
    
