from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from job.models import Job
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from job.validators import delivery_validate_file_size


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Cart of {self.user.first_name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [['cart', 'job']]
        indexes = [
            models.Index(fields=['cart', 'job']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.job.name}"


class Order(models.Model):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    DELIVERED = 'DELIVERED'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (DELIVERED, 'Delivered'),
        (COMPLETED, 'Completed'),
        (CANCELED, 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.deadline and self.items.exists():
            max_duration = max(item.job.duration_days for item in self.items.all())
            self.deadline = timezone.now().date() + timedelta(days=max_duration)
            super().save(update_fields=['deadline']) 
        

    def __str__(self):
        return f"Order {self.id} by {self.user.first_name} - {self.status}"


# Esach item may be assigned to different freelancers
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='order_items')
    freelancer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_jobs")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        indexes = [
            models.Index(fields=['order', 'job', 'freelancer']),
        ]

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job.name} for Order {self.order.id}"
    

class OrderDelivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    file = models.FileField(upload_to='order_deliveries', blank=True, null=True, validators=[delivery_validate_file_size])
    description = models.TextField(blank=True, null=True)
    delivered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delivered_orders')
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['order', 'delivered_by', 'delivered_at']),
        ]

    def __str__(self):
        return f"Delivery for Order {self.order.id} by {self.delivered_by.email}"