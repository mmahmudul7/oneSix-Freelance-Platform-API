from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from messaging.models import Message, CustomOffer
from messaging.serializers import MessageSerializer, CustomOfferSerializer
from django.core.mail import send_mail
from django.conf import settings
from order.services import OrderService
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema


class MessageViewSet(ModelViewSet):
    """
    ViewSet for managing messages.
    Allows authenticated users to send and view messages they sent or received.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return messages sent or received by the authenticated user.
        """
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        # Users can only see messages they sent or received
        user = self.request.user
        if not user.is_authenticated:
            return Message.objects.none()
        return Message.objects.filter(
            models.Q(sender=self.request.user) | models.Q(receiver=self.request.user)
        ).select_related('sender', 'receiver', 'job')
    
    @swagger_auto_schema(
        operation_summary="Create a new message",
        operation_description=(
            "Creates a new message with optional job reference and file attachment. "
            "Validates that the sender is authenticated and not sending to themselves. "
            "Supports file uploads (JPEG, PNG, PDF, max 1GB). "
            "Sends an email notification to the receiver with message content and optional file details. "
            "Email failures are logged silently."
        ),
        request_body=MessageSerializer,
        responses={
            201: MessageSerializer,
            400: "Bad Request: Invalid receiver, file size exceeds 1GB, or unsupported file type (allowed: JPEG, PNG, PDF).",
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        # Send email notification to receiver
        file_info = f"\nAttachment: {message.file.url}" if message.file else ""
        send_mail(
            subject=f'New Message from {self.request.user.get_full_name() or self.request.user.email}',
            message=f'You have received a new message regarding "{message.job.name if message.job else "General"}":\n\n{message.content}{file_info}\n\nPlease check your inbox.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[message.receiver.email],
            fail_silently=True,
        )

    @swagger_auto_schema(
        operation_summary="Get user inbox",
        operation_description=(
            "Retrieves all messages sent or received by the authenticated user, ordered by creation date (newest first). "
            "Messages are grouped by conversation (sender/receiver pair) and include sender, receiver, and job details."
        ),
        responses={
            200: MessageSerializer(many=True),
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def inbox(self, request):
        # Get messages grouped by conversation (sender/receiver pair)
        messages = self.get_queryset().order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class CustomOfferViewSet(ModelViewSet):
    """
    ViewSet for managing custom offers.
    Allows authenticated users to create, view, accept, or reject custom offers for jobs they created or received.
    """
    serializer_class = CustomOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return custom offers sent or received by the authenticated user.
        """
        if getattr(self, 'swagger_fake_view', False):
            return CustomOffer.objects.none()
        # Users can only see offers they sent or received
        user = self.request.user
        if not user.is_authenticated:
            return CustomOffer.objects.none()
        return CustomOffer.objects.filter(
            models.Q(sender=self.request.user) | models.Q(receiver=self.request.user)
        ).select_related('job', 'sender', 'receiver')

    @swagger_auto_schema(
        operation_summary="Create a custom offer",
        operation_description=(
            "Creates a custom offer for a specific job. "
            "Validates that the sender is the job creator and not sending to themselves. "
            "Includes price, delivery days, and optional features (e.g., {'revisions': 2, 'source_file': true}). "
            "Sends an email notification to the receiver with offer details. "
            "Email failures are logged silently."
        ),
        request_body=CustomOfferSerializer,
        responses={
            201: CustomOfferSerializer,
            400: "Bad Request: Sender is not the job creator or sending to themselves.",
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def perform_create(self, serializer):
        offer = serializer.save(sender=self.request.user)
        # Send email notification to receiver
        send_mail(
            subject=f'New Custom Offer for {offer.job.name}',
            message=f'Dear {offer.receiver.get_full_name() or offer.receiver.email},\n\nYou have received a custom offer from {self.request.user.get_full_name() or self.request.user.email} for "{offer.job.name}".\nPrice: ${offer.price}\nDelivery: {offer.delivery_days} days\nFeatures: {offer.features}\n\nPlease review the offer.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[offer.receiver.email],
            fail_silently=True,
        )

    @swagger_auto_schema(
        operation_summary="Accept a custom offer",
        operation_description=(
            "Accepts a custom offer, creating an order via OrderService.create_custom_order. "
            "Validates that the user is the offer receiver and the offer is in PENDING status. "
            "Creates an order with the offer's price, delivery days, and features within a database transaction. "
            "Updates the offer status to ACCEPTED and sends an email notification to the sender. "
            "Email failures are logged silently."
        ),
        request_body=None,
        responses={
            200: "Offer accepted with order details",
            400: "Bad Request: Offer is not in PENDING status.",
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only the offer receiver can accept this offer."
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.receiver != request.user:
            raise PermissionDenied("You can only accept offers sent to you.")
        if offer.status != 'PENDING':
            raise ValidationError("This offer has already been processed.")
        
        # Create an order from the custom offer
        with transaction.atomic():
            order = OrderService.create_custom_order(
                user=offer.receiver,
                job=offer.job,
                price=offer.price,
                delivery_days=offer.delivery_days,
                features=offer.features
            )
            offer.status = 'ACCEPTED'
            offer.save()

            # Send email notification to sender
            send_mail(
                subject=f'Your Custom Offer for {offer.job.name} Accepted',
                message=f'Dear {offer.sender.get_full_name() or offer.sender.email},\n\nYour custom offer for "{offer.job.name}" has been accepted by {offer.receiver.get_full_name() or offer.receiver.email}.\nOrder ID: {order.id}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[offer.sender.email],
                fail_silently=True,
            )
        
        return Response({'status': 'Offer accepted', 'order_id': order.id})

    @swagger_auto_schema(
        operation_summary="Reject a custom offer",
        operation_description=(
            "Rejects a custom offer. "
            "Validates that the user is the offer receiver and the offer is in PENDING status. "
            "Updates the offer status to REJECTED and sends an email notification to the sender. "
            "Email failures are logged silently."
        ),
        request_body=None,
        responses={
            200: "Offer rejected",
            400: "Bad Request: Offer is not in PENDING status.",
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only the offer receiver can reject this offer."
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        offer = self.get_object()
        if offer.receiver != request.user:
            raise PermissionDenied("You can only reject offers sent to you.")
        if offer.status != 'PENDING':
            raise ValidationError("This offer has already been processed.")
        
        offer.status = 'REJECTED'
        offer.save()

        # Send email notification to sender
        send_mail(
            subject=f'Your Custom Offer for {offer.job.name} Rejected',
            message=f'Dear {offer.sender.get_full_name() or offer.sender.email},\n\nYour custom offer for "{offer.job.name}" has been rejected by {offer.receiver.get_full_name() or offer.receiver.email}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[offer.sender.email],
            fail_silently=True,
        )
        
        return Response({'status': 'Offer rejected'})
    