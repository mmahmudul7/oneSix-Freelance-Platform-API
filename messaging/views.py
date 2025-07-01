from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Message, CustomOffer
from .serializers import MessageSerializer, CustomOfferSerializer
from django.core.mail import send_mail
from django.conf import settings
from order.services import OrderService
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction


class MessageViewSet(ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        # Users can only see messages they sent or received
        return Message.objects.filter(
            models.Q(sender=self.request.user) | models.Q(receiver=self.request.user)
        ).select_related('sender', 'receiver', 'job')

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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def inbox(self, request):
        # Get messages grouped by conversation (sender/receiver pair)
        messages = self.get_queryset().order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class CustomOfferViewSet(ModelViewSet):
    serializer_class = CustomOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CustomOffer.objects.none()
        # Users can only see offers they sent or received
        return CustomOffer.objects.filter(
            models.Q(sender=self.request.user) | models.Q(receiver=self.request.user)
        ).select_related('job', 'sender', 'receiver')

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
    