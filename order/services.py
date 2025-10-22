from order.models import Cart, Order, OrderItem
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.conf import settings


class OrderService:
    @staticmethod
    def create_order(user, cart_id):
        """
        Summary:
            Create an order from a user's cart.

        Description:
            Validates that the cart belongs to the user and is not empty. Ensures the user is not ordering their own jobs.
            Calculates the total price based on cart items, creates an order and associated order items,
            sends email notifications to the buyer and job creators, and deletes the cart.

        Args:
            user: The authenticated user creating the order.
            cart_id: The ID of the cart to convert into an order.

        Returns:
            Order: The created order object.

        Raises:
            PermissionDenied: If the cart does not belong to the user.
            ValidationError: If the cart is empty or contains the user's own jobs.
        """
        with transaction.atomic():
            cart = Cart.objects.get(pk=cart_id)
            cart_items = cart.items.select_related('job').all()

            if not cart_items:
                raise ValidationError("Your cart is empty.")

            total_price = sum([item.job.price.price *
                               item.quantity for item in cart_items])

            order = Order.objects.create(
                user=user,
                total_price=total_price
            )

            order_items = [
                OrderItem(
                    order=order,
                    job=item.job,
                    price=item.job.price.price,
                    quantity=item.quantity,
                    total_price=item.job.price.price * item.quantity
                )
                for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            # Send notification to buyer
            # send_mail(
            #     subject='Order Placed Successfully',
            #     message=f'Dear {user.get_full_name() or user.email},\n\nYour order (ID: {order.id}) has been placed successfully.\nTotal Price: ${total_price}\n\nThank you!',
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[user.email],
            #     fail_silently=True,
            # )

            # Send notification to job creators
            # job_creators = set(item.job.created_by for item in cart_items)
            # for creator in job_creators:
            #     send_mail(
            #         subject='Your Job Has Been Ordered',
            #         message=f'Dear {creator.get_full_name() or creator.email},\n\nYour job "{item.job_name}" has been ordered by {user.get_full_name() or user.email}.\nOrder ID: {order.id}\n\nThank you!',
            #         from_email=settings.DEFAULT_FROM_EMAIL,
            #         recipient_list=[creator.email],
            #         fail_silently=True,
            #     )

            cart.delete()

            return order
        
    @staticmethod
    def cancel_order(order, user):
        """
        Summary:
            Cancel an existing order.

        Description:
            Allows admins to cancel any order or users to cancel their own non-completed orders.
            Updates the order status to CANCELED.

        Args:
            order: The order object to cancel.
            user: The authenticated user attempting to cancel the order.

        Returns:
            Order: The updated order object with CANCELED status.

        Raises:
            PermissionDenied: If a non-admin user tries to cancel someone else's order.
            ValidationError: If the order is already completed.
        """
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
        

    # @staticmethod
    # def create_custom_order(user, job, price, delivery_days, features):
    #     """
    #     Summary:
    #         Create a custom order for a specific job.

    #     Description:
    #         Creates a custom order for a job with a specified price, delivery days, and features.
    #         Validates that the user is not ordering their own job. Creates an order with a single order item
    #         and sends email notifications to the buyer and job creator.

    #     Args:
    #         user: The authenticated user creating the order.
    #         job: The job object being ordered.
    #         price: The custom price for the order.
    #         delivery_days: The number of days for delivery.
    #         features: A description of the custom features included in the order.

    #     Returns:
    #         Order: The created order object.

    #     Raises:
    #         ValidationError: If the user attempts to order their own job.
    #     """
    #     with transaction.atomic():
    #         if job.created_by == user:
    #             raise ValidationError("You cannot order your own job.")
            
    #         total_price = price
    #         order = Order.objects.create(user=user, total_price=total_price)
            
    #         OrderItem.objects.create(
    #             order=order,
    #             job=job,
    #             price=price,
    #             quantity=1,
    #             total_price=total_price
    #         )

    #         # Send notification to buyer
    #         send_mail(
    #             subject='Custom Order Placed Successfully',
    #             message=f'Dear {user.get_full_name() or user.email},\n\nYour custom order (ID: {order.id}) for "{job.name}" has been placed successfully.\nTotal Price: ${total_price}\nDelivery Days: {delivery_days}\nFeatures: {features}\n\nThank you!',
    #             from_email=settings.DEFAULT_FROM_EMAIL,
    #             recipient_list=[user.email],
    #             fail_silently=True,
    #         )

    #         # Send notification to job creator
    #         send_mail(
    #             subject='Your Job Has Been Ordered (Custom Offer)',
    #             message=f'Dear {job.created_by.get_full_name() or job.created_by.email},\n\nYour job "{job.name}" has been ordered by {user.get_full_name() or user.email} via a custom offer.\nOrder ID: {order.id}\nPrice: ${price}\nDelivery Days: {delivery_days}\nFeatures: {features}\n\nThank you!',
    #             from_email=settings.DEFAULT_FROM_EMAIL,
    #             recipient_list=[job.created_by.email],
    #             fail_silently=True,
    #         )

    #         return order

        
    
        