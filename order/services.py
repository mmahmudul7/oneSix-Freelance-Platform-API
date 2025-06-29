from order.models import Cart, Order, OrderItem
from django.db import transaction


class OrderService:
    @staticmethod
    def create_order(user_id, cart_id):
        with transaction.atomic():
            cart = Cart.objects.get(pk=cart_id)
            cart_items = cart.items.select_related('job').all()

            total_price = sum([item.job.price * item.quantity for item in cart_items])

            order = Order.objects.create(user_id=user_id, total_price=total_price)

            order_items = [
                OrderItem(
                    order = order,
                    job = item.job,
                    # freelancer = item.freelancer,
                    price = item.job.price,
                    quantity = item.quantity,
                    total_price = item.job.price * item.quantity
                )
                for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            cart.delete()

            return order