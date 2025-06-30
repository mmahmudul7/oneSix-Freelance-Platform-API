from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from job.models import Job
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.first_name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [['cart', 'job']]

    def __str__(self):
        return f"{self.quantity} x {self.job.name}"


class Order(models.Model):
    NOT_PAID = 'Not Paid'
    ACCEPTED = 'Accepted'
    IN_PROGRESS = 'In Progress'
    SUBMITTED = 'Submitted'
    COMPLETED = 'Completed'
    CANCELED = 'Canceled'

    STATUS_CHOICES = [
        (NOT_PAID, 'Not Paid'),       # Created, waiting to be accepted
        (ACCEPTED, 'Accepted'),       # Freelancer accepted job
        (IN_PROGRESS, 'In Progress'), # Work started
        (SUBMITTED, 'Submitted'),     # Submitted for approval
        (COMPLETED, 'Completed'),     # Client approved
        (CANCELED, 'Canceled'),       # Canceled any time
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_PAID)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.deadline and self.items.exists():
            # Calculate deadline based on the maximum duration_days of jobs in order
            max_duration = max(item.job.duration_days for item in self.items.all())
            self.deadline = timezone.now().date() + timedelta(days=max_duration)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} by {self.user.first_name} - {self.status}"


# Esach item may be assigned to different freelancers
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_jobs")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.job.name} for Order {self.order.id}"