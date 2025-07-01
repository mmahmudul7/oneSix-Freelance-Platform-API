from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from order.models import Cart, CartItem, Order, OrderDelivery
from order import serializers as orderSz
from order.services import OrderService
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db import models



class CartViewSet(ModelViewSet):
    serializer_class = orderSz.CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.prefetch_related('items__job').filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return orderSz.AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return orderSz.UpdateCartItemSerializer
        return orderSz.CartItemSerializer
    
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk'], 'request': self.request}

    def get_queryset(self):
        return CartItem.objects.select_related('job').filter(cart_id=self.kwargs['cart_pk'])


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'patch', 'head', 'options']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__job').all()
        return Order.objects.prefetch_related('items__job').filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'cancel':
            return orderSz.EmptySerializer
        if self.action == 'create':
            return orderSz.CreateOrderSerializer
        elif self.action in ['start_progress', 'complete', 'update_status']:
            return orderSz.UpdateOrderSerializer
        return orderSz.OrderSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id, 'user': self.request.user}

    def perform_create(self, serializer):
        cart_id = self.request.data.get('cart_id')
        order = OrderService.create_order(self.request.user, cart_id)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order = OrderService.cancel_order(order, request.user)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start_progress(self, request, pk=None):
        order = self.get_object()
        job_creator = order.items.first().job.created_by
        if request.user != job_creator:
            raise PermissionDenied("Only the job creator can start progress on this order.")
        if order.status != Order.PENDING:
            raise ValidationError("Order must be in pending status to start progress.")
        
        order.status = Order.IN_PROGRESS
        order.save()
        
        send_mail(
            subject=f'Order {order.id} In Progress',
            message=f'Dear {order.user.get_full_name() or order.user.email},\n\nYour order (ID: {order.id}) is now in progress.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
        
        return Response({'status': 'Order is now in progress'})

    @action(detail=True, methods=['post'])  # Added to allow buyer to complete order
    def complete(self, request, pk=None):
        order = self.get_object()
        if request.user != order.user:
            raise PermissionDenied("Only the buyer can complete this order.")
        if order.status != Order.DELIVERED:
            raise ValidationError("Order must be delivered to complete.")
        
        order.status = Order.COMPLETED
        order.save()
        
        job_creator = order.items.first().job.created_by
        send_mail(
            subject=f'Order {order.id} Completed',
            message=f'Dear {job_creator.get_full_name() or job_creator.email},\n\nThe order (ID: {order.id}) has been marked as completed by {order.user.get_full_name() or order.user.email}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[job_creator.email],
            fail_silently=True,
        )
        
        return Response({'status': 'Order completed'})

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = orderSz.UpdateOrderSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': f'Order status updated to {order.status}'})

    def get_permissions(self):
        if self.action in ['update_status', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class OrderDeliveryViewSet(ModelViewSet):
    serializer_class = orderSz.OrderDeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return OrderDelivery.objects.filter(
            models.Q(order__user=user) | models.Q(delivered_by=user)
        ).select_related('order', 'delivered_by')

    def perform_create(self, serializer):
        with transaction.atomic():
            delivery = serializer.save(delivered_by=self.request.user)
            order = delivery.order
            order.status = Order.DELIVERED
            order.save()
            
            send_mail(
                subject=f'Order {order.id} Delivered',
                message=f'Dear {order.user.get_full_name() or order.user.email},\n\nYour order (ID: {order.id}) has been delivered by {self.request.user.get_full_name() or self.request.user.email}.\nDescription: {delivery.description}\nFile: {delivery.file.url if delivery.file else "No file"}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )