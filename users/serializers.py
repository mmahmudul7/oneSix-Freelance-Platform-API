from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from rest_framework import serializers
from users.models import Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'title', 'description', 'image', 'link', 'created_at']
        read_only_fields = ['created_at']


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'address', 'phone_number']


class PublicUserSerializer(BaseUserSerializer):
    """
    Serializer for public user profile, excluding sensitive fields like email, phone_number, and address.
    """
    portfolio = PortfolioSerializer(many=True, read_only=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    average_rating = serializers.ReadOnlyField()
    total_orders = serializers.ReadOnlyField()
    location = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'first_name', 'last_name', 'total_orders', 'average_rating', 'location', 'bio', 'profile_picture', 'skills', 'portfolio']
        read_only_fields = ['portfolio']
        ref_name = 'PublicUser'

    def validate_skills(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("You can add up to 10 skills.")
        return value
    
    def get_average_rating(self, obj):
        return getattr(obj, 'average_rating', 0)

    def get_total_orders(self, obj):
        return getattr(obj, 'total_orders', 0)


class UserSerializer(BaseUserSerializer):
    portfolio = PortfolioSerializer(many=True, read_only=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    average_rating = serializers.ReadOnlyField()
    total_orders = serializers.ReadOnlyField()
    location = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name', 'total_orders', 'average_rating', 'location', 'phone_number', 'bio', 'profile_picture', 'skills', 'portfolio', 'is_staff']
        read_only_fields = ['is_staff', 'portfolio']
        ref_name = 'CustomUser'

    def get_average_rating(self, obj):
        return getattr(obj, 'average_rating', 0)

    def get_total_orders(self, obj):
        return getattr(obj, 'total_orders', 0)


    def validate_skills(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("You can add up to 10 skills.")
        return value
    

class FreelancerSearchSerializer(serializers.Serializer):  # Freelancer search
    keyword = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    location = serializers.CharField(required=False, allow_blank=True)
    min_rating = serializers.FloatField(required=False)
    sort_by = serializers.ChoiceField(
        choices=['rating_desc', 'orders_desc', 'created_at_desc'],
        required=False
    )