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
import logging
from drf_yasg.utils import swagger_auto_schema

# Setup logging
logger = logging.getLogger(__name__)

class CartViewSet(ModelViewSet):
    serializer_class = orderSz.CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return Cart.objects.prefetch_related('items__job').filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="List all carts",
        operation_description="Retrieve a list of carts for the authenticated user.",
        responses={
            200: orderSz.CartSerializer(many=True),
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new cart",
        operation_description="Create a new cart for the authenticated user.",
        request_body=orderSz.CartSerializer,
        responses={
            201: orderSz.CartSerializer,
            400: "Bad Request: Invalid data",
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Retrieve a cart",
        operation_description="Retrieve a specific cart by ID.",
        responses={
            200: orderSz.CartSerializer,
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a cart",
        operation_description="Partially update a cart.",
        request_body=orderSz.CartSerializer,
        responses={
            200: orderSz.CartSerializer,
            400: "Bad Request: Invalid data",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart not found."
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a cart",
        operation_description="Delete a cart.",
        responses={
            204: "No Content",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart not found."
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return orderSz.AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return orderSz.UpdateCartItemSerializer
        return orderSz.CartItemSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if getattr(self, 'swagger_fake_view', False):
            return context
        return {'cart_id': self.kwargs.get('cart_pk'), 'request': self.request}

    def get_queryset(self):
        return CartItem.objects.select_related('job').filter(cart_id=self.kwargs.get('cart_pk'))

    @swagger_auto_schema(
        operation_summary="List cart items",
        operation_description="Retrieve a list of items in a specific cart.",
        responses={
            200: orderSz.CartItemSerializer(many=True),
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart not found."
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Add a cart item",
        operation_description="Add an item to a specific cart.",
        request_body=orderSz.AddCartItemSerializer,
        responses={
            201: orderSz.AddCartItemSerializer,
            400: "Bad Request: Invalid job ID or quantity.",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart or job not found."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a cart item",
        operation_description="Retrieve a specific cart item.",
        responses={
            200: orderSz.CartItemSerializer,
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart item not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a cart item",
        operation_description="Update the quantity of a cart item.",
        request_body=orderSz.UpdateCartItemSerializer,
        responses={
            200: orderSz.UpdateCartItemSerializer,
            400: "Bad Request: Invalid quantity.",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart item not found."
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a cart item",
        operation_description="Delete a cart item.",
        responses={
            204: "No Content",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Cart item not found."
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'patch', 'head', 'options']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
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
        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer_context()
        return {'user_id': self.request.user.id, 'user': self.request.user}

    @swagger_auto_schema(
        operation_summary="List all orders",
        operation_description="Retrieve a list of orders (all for staff, user-specific for others).",
        responses={
            200: orderSz.OrderSerializer(many=True),
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create an order",
        operation_description="Create a new order from a cart.",
        request_body=orderSz.CreateOrderSerializer,
        responses={
            201: orderSz.OrderSerializer,
            400: "Bad Request: Invalid cart ID or empty cart.",
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        cart_id = self.request.data.get('cart_id')
        order = OrderService.create_order(self.request.user, cart_id)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Retrieve an order",
        operation_description="Retrieve a specific order.",
        responses={
            200: orderSz.OrderSerializer,
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Order not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an order",
        operation_description="Partially update an order (admin only).",
        request_body=orderSz.UpdateOrderSerializer,
        responses={
            200: orderSz.OrderSerializer,
            400: "Bad Request: Invalid status.",
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only admin can update orders.",
            404: "Not Found: Order not found."
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an order",
        operation_description="Delete an order (admin only).",
        responses={
            204: "No Content",
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only admin can delete orders.",
            404: "Not Found: Order not found."
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Cancel an order",
        operation_description="Cancel an order.",
        request_body=orderSz.EmptySerializer,
        responses={
            200: orderSz.OrderSerializer,
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Order not found."
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order = OrderService.cancel_order(order, request.user)
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Start order progress",
        operation_description="Start progress on an order (job creator only).",
        request_body=orderSz.UpdateOrderSerializer,
        responses={
            200: '{"status": "Order is now in progress"}',
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only the job creator can start progress on this order.",
            404: "Not Found: Order not found.",
            400: "Bad Request: Order must be in pending status to start progress."
        }
    )
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
        
        try:
            send_mail(
                subject=f'Order {order.id} In Progress',
                message=f'Dear {order.user.get_full_name() or order.user.email},\n\nYour order (ID: {order.id}) is now in progress.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email for order {order.id} start_progress: {str(e)}")
        
        return Response({'status': 'Order is now in progress'})

    @swagger_auto_schema(
        operation_summary="Complete an order",
        operation_description="Complete an order (buyer only).",
        request_body=orderSz.UpdateOrderSerializer,
        responses={
            200: '{"status": "Order completed"}',
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only the buyer can complete this order.",
            404: "Not Found: Order not found.",
            400: "Bad Request: Order must be delivered to complete."
        }
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if request.user != order.user:
            raise PermissionDenied("Only the buyer can complete this order.")
        if order.status != Order.DELIVERED:
            raise ValidationError("Order must be delivered to complete.")
        
        order.status = Order.COMPLETED
        order.save()
        
        job_creator = order.items.first().job.created_by
        try:
            send_mail(
                subject=f'Order {order.id} Completed',
                message=f'Dear {job_creator.get_full_name() or job_creator.email},\n\nThe order (ID: {order.id}) has been marked as completed by {order.user.get_full_name() or order.user.email}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[job_creator.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email for order {order.id} completion: {str(e)}")
        
        return Response({'status': 'Order completed'})

    @swagger_auto_schema(
        operation_summary="Update order status",
        operation_description="Update the status of an order (admin only).",
        request_body=orderSz.UpdateOrderSerializer,
        responses={
            200: '{"status": "Order status updated to <status>"}',
            400: "Bad Request: Invalid status.",
            401: "Unauthorized: Authentication credentials were not provided.",
            403: "Forbidden: Only admin can update order status.",
            404: "Not Found: Order not found."
        }
    )
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
        if getattr(self, 'swagger_fake_view', False):
            return OrderDelivery.objects.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return OrderDelivery.objects.none()
        return OrderDelivery.objects.filter(
            models.Q(order__user=user) | models.Q(delivered_by=user)
        ).select_related('order', 'delivered_by')

    @swagger_auto_schema(
        operation_summary="List all deliveries",
        operation_description="Retrieve a list of deliveries for the authenticated user (as buyer or deliverer).",
        responses={
            200: orderSz.OrderDeliverySerializer(many=True),
            401: "Unauthorized: Authentication credentials were not provided."
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a delivery",
        operation_description="Create a delivery for an order (job creator only).",
        request_body=orderSz.OrderDeliverySerializer,
        responses={
            201: orderSz.OrderDeliverySerializer,
            400: "Bad Request: Invalid order or delivery data.",
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Order not found."
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        with transaction.atomic():
            delivery = serializer.save(delivered_by=self.request.user)
            order = delivery.order
            order.status = Order.DELIVERED
            order.save()
            
            try:
                send_mail(
                    subject=f'Order {order.id} Delivered',
                    message=f'Dear {order.user.get_full_name() or order.user.email},\n\nYour order (ID: {order.id}) has been delivered by {self.request.user.get_full_name() or self.request.user.email}.\nDescription: {delivery.description}\nFile: {delivery.file.url if delivery.file else "No file"}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email for order {order.id} delivery: {str(e)}")

    @swagger_auto_schema(
        operation_summary="Retrieve a delivery",
        operation_description="Retrieve a specific delivery.",
        responses={
            200: orderSz.OrderDeliverySerializer,
            401: "Unauthorized: Authentication credentials were not provided.",
            404: "Not Found: Delivery not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)