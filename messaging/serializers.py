from rest_framework import serializers
from messaging.models import Message, CustomOffer
from users.serializers import UserSerializer
from users.models import User
from job.models import Job


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), required=False)
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'job', 'content', 'file', 'created_at']
        read_only_fields = ['sender', 'created_at']

    def validate_receiver(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError("You cannot send a message to yourself.")
        return value

    def validate_file(self, value):
        if value:
            # Limit file size to 1024MB
            max_size = 1024 * 1024 * 1024  # 1 GB
            if value.size > max_size:
                raise serializers.ValidationError("File size cannot exceed 1GB.")
            # Optional: Validate file types (e.g., images, PDFs)
            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("File type not allowed. Allowed types: JPEG, PNG, PDF.")
        return value


class CustomOfferSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())

    class Meta:
        model = CustomOffer
        fields = ['id', 'job', 'sender', 'receiver', 'price', 'delivery_days', 'features', 'status', 'created_at']
        read_only_fields = ['sender', 'status', 'created_at']

    def validate(self, data):
        request = self.context['request']
        if data['job'].created_by != request.user:
            raise serializers.ValidationError("You can only create custom offers for your own jobs.")
        if data['receiver'] == request.user:
            raise serializers.ValidationError("You cannot send a custom offer to yourself.")
        return data