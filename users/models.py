from django.db import models
from django.contrib.auth.models import AbstractUser
from users.managers import CustomUserManager
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    profile_picture = CloudinaryField('image')
    skills = models.JSONField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)  # location-based search

    USERNAME_FIELD = 'email' # Use email instead of username
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the user's full name for email notifications.
        """
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def average_rating(self):  # ranking by average review rating
        reviews = self.created_jobs.values('reviews__ratings').aggregate(avg_rating=models.Avg('reviews__ratings'))
        return reviews['avg_rating'] or 0

    @property
    def total_orders(self):  # ranking by number of orders
        return self.created_jobs.annotate(order_count=models.Count('order_items')).aggregate(total=models.Sum('order_count'))['total'] or 0 
    

class Portfolio(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='portfolio')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    # image = models.ImageField(upload_to='portfolio_images', blank=True, null=True)
    image =  CloudinaryField('image')
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user}"