from order.models import Cart, Order, OrderItem
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.conf import settings


class OrderService:
    @staticmethod
    def create_order(user, cart_id):
        with transaction.atomic():
            cart = Cart.objects.get(pk=cart_id)
            if cart.user != user:
                raise PermissionDenied("You can only create an order from your own cart")
            
            cart_items = cart.items.select_related('job').all()
            if not cart_items:
                raise ValidationError("Cart is empty")

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

            # Send notification to buyer
            send_mail(
                subject='Order Placed Successfully',
                message=f'Dear {user.get_full_name() or user.email},\n\nYour order (ID: {order.id}) has been placed successfully.\nTotal Price: ${total_price}\n\nThank you!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

            # Send notification to job creators
            job_creators = set(item.job.created_by for item in cart_items)
            for creator in job_creators:
                send_mail(
                    subject='Your Job Has Been Ordered',
                    message=f'Dear {creator.get_full_name() or creator.email},\n\nYour job "{item.job.name}" has been ordered by {user.get_full_name() or user.email}.\nOrder ID: {order.id}\n\nThank you!',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[creator.email],
                    fail_silently=True,
                )

            cart.delete()

            return order
        

    @staticmethod
    def create_custom_order(user, job, price, delivery_days, features):
        with transaction.atomic():
            if job.created_by == user:
                raise ValidationError("You cannot order your own job.")
            
            total_price = price
            order = Order.objects.create(user=user, total_price=total_price)
            
            OrderItem.objects.create(
                order=order,
                job=job,
                price=price,
                quantity=1,
                total_price=total_price
            )

            # Send notification to buyer
            send_mail(
                subject='Custom Order Placed Successfully',
                message=f'Dear {user.get_full_name() or user.email},\n\nYour custom order (ID: {order.id}) for "{job.name}" has been placed successfully.\nTotal Price: ${total_price}\nDelivery Days: {delivery_days}\nFeatures: {features}\n\nThank you!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

            # Send notification to job creator
            send_mail(
                subject='Your Job Has Been Ordered (Custom Offer)',
                message=f'Dear {job.created_by.get_full_name() or job.created_by.email},\n\nYour job "{job.name}" has been ordered by {user.get_full_name() or user.email} via a custom offer.\nOrder ID: {order.id}\nPrice: ${price}\nDelivery Days: {delivery_days}\nFeatures: {features}\n\nThank you!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[job.created_by.email],
                fail_silently=True,
            )

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
        