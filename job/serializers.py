from rest_framework import serializers
from decimal import Decimal
from job.models import Category, Job


class CategorySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'job_count']


class JobSerializer(serializers.ModelSerializer):
    cart_price = serializers.SerializerMethodField(method_name='calculate_cart')
    
    class Meta:
        model = Job
        fields = ['id', 'name', 'description', 'price', 'category', 'cart_price']

    def calculate_cart(self, job):
        return round(job.price * Decimal(1.16), 2)
    
    def validate_price(self, price):
        if price < 0:
            raise serializers.ValidationError('Price could not be negative')
        return price