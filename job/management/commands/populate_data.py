from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User, Portfolio
from job.models import Category, JobPrice, Job
import random

class Command(BaseCommand):
    help = 'Populate database with sample users and jobs'

    def handle(self, *args, **kwargs):
        # Create users
        for i in range(1, 6):  # Create 5 users
            email = f"user{i}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create(
                    email=email,
                    password=make_password("Test@123"),
                    first_name=f"User{i}",
                    last_name="Test",
                    address="123 Test Street",
                    phone_number=f"+88012345678{i}",
                    bio=f"Sample bio for user {i}",
                    skills=["Python", "Django", "JavaScript"],
                    location="Dhaka, Bangladesh"
                )
                Portfolio.objects.create(
                    user=user,
                    title=f"Portfolio {i}",
                    description=f"Sample portfolio for user {i}",
                    link=f"https://portfolio{i}.example.com"
                )
                self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))

        # Create categories
        categories = [
            {"name": "Web Development", "description": "Web application development"},
            {"name": "Graphic Design", "description": "Design services"}
        ]
        for cat in categories:
            if not Category.objects.filter(name=cat["name"]).exists():
                category = Category.objects.create(**cat)
                self.stdout.write(self.style.SUCCESS(f"Created category: {cat['name']}"))

        # Create jobs
        users = User.objects.all()
        categories = Category.objects.all()
        for i in range(1, 11):  # Create 10 jobs
            job_price = JobPrice.objects.create(price=random.uniform(50, 200))
            Job.objects.create(
                name=f"Sample Job {i}",
                description=f"Description for job {i}",
                price=job_price,
                category=random.choice(categories),
                created_by=random.choice(users),
                duration_days=random.randint(1, 14)
            )
            self.stdout.write(self.style.SUCCESS(f"Created job: Sample Job {i}"))