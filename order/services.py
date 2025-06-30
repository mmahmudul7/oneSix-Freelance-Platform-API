from order.models import Cart, Order, OrderItem
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError


class OrderService:
    @staticmethod
    def create_order(user, cart_id):
        with transaction.atomic():
            cart = Cart.objects.get(pk=cart_id)
            if cart.user != user:
                raise PermissionDenied("You can only create an order from your own cart")
            
            cart_items = cart.items.select_related('job').all()

            # Validate that user is not buying their own jobs
            for item in cart_items:
                if item.job.created_by_id == user:
                    raise ValidationError(f"You cannot order your own job: {item.job.name}")

            total_price = sum([item.job.price * item.quantity for item in cart_items])

            order = Order.objects.create(user_id=user, total_price=total_price)

            order_items = [
                OrderItem(
                    order = order,
                    job = item.job,
                    price = item.job.price,
                    quantity = item.quantity,
                    total_price = item.job.price * item.quantity
                )
                for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            cart.delete()

            return order
        
    @staticmethod
    def cancel_order(order, user):
        if user.is_staff:
            order.status = Order.CANCELED
            order.save()
            return order
        
        if order.user != user:
            raise PermissionDenied({'detail': 'You can only cancel your own order'})
        
        if order.status == Order.COMPLETED:
            raise ValidationError({'detail': 'You can not cancel an completed order'})
        
        order.status = Order.CANCELED
        order.save()
        return order
        