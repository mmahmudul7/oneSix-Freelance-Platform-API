from django.db import models
from django.contrib.auth.models import AbstractUser
from users.managers import CustomUserManager


class Role(models.Model):
    FREELANCER = 'freelancer'
    CLIENT = 'client'
    ROLE_CHOICES = [
        (FREELANCER, 'Freelancer'),
        (CLIENT, 'Client'),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    roles = models.ManyToManyField(Role, related_name='users')

    USERNAME_FIELD = 'email' # Use email instead of username
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def has_role(self, role_name):
        return self.roles.filter(name=role_name).exists()