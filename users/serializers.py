from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from rest_framework import serializers
from users.models import User, Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'title', 'description', 'image', 'link', 'created_at']
        read_only_fields = ['created_at']


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'address', 'phone_number']


class UserSerializer(BaseUserSerializer):
    portfolio = PortfolioSerializer(many=True, read_only=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'email', 'first_name', 'last_name', 'address', 'phone_number', 'bio', 'profile_picture', 'skills', 'portfolio']
        read_only_fields = ['portfolio']

    def validate_skills(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("You can add up to 10 skills.")
        return value