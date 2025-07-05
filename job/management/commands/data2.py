from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User, Portfolio
from job.models import Category, JobPrice, Job, JobImage, Review
from django.core.files.base import ContentFile
import random
import io
from PIL import Image
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Populate database with real-life sample users and jobs like Fiverr gigs'

    def create_fake_image(self, text='Job'):
        image = Image.new('RGB', (200, 200), color=(random.randint(100,255), random.randint(100,255), random.randint(100,255)))
        byte_io = io.BytesIO()
        image.save(byte_io, 'PNG')
        return ContentFile(byte_io.getvalue(), f"{text.lower()}_image.png")

    def handle(self, *args, **kwargs):
        # Create Categories
        categories_data = [
            {"name": "Web Development", "description": "Building websites and web apps using modern technologies."},
            {"name": "Graphic Design", "description": "Creating visual content to communicate messages."},
            {"name": "Digital Marketing", "description": "Promoting products/services through digital channels."},
            {"name": "Content Writing", "description": "Writing compelling and informative content for various niches."},
            {"name": "Video Editing", "description": "Editing and producing professional videos for YouTube, ads, and more."},
        ]
        categories = []
        for cat in categories_data:
            category, created = Category.objects.get_or_create(name=cat['name'], defaults={"description": cat['description']})
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {cat['name']}"))

        # Create Users
        users = []
        for i in range(1, 11):
            email = f"user{i}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create(
                    email=email,
                    password=make_password("Test@123"),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    address=fake.address(),
                    phone_number=f"+8801{random.randint(100000000, 999999999)}",
                    bio=fake.paragraph(nb_sentences=5),
                    skills=random.sample(["Python", "Django", "React", "Photoshop", "SEO", "Final Cut Pro", "Copywriting"], 3),
                    location=fake.city()
                )
                users.append(user)
                Portfolio.objects.create(
                    user=user,
                    title=f"{user.first_name}'s Portfolio",
                    description=fake.text(),
                    link=f"https://portfolio{user.id}.example.com"
                )
                self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))
            else:
                users.append(User.objects.get(email=email))

        # Create Jobs
        job_titles = [
            "Build a responsive portfolio website",
            "Design a modern company logo",
            "Write SEO optimized blog posts",
            "Edit cinematic wedding videos",
            "Create Facebook ad campaigns",
            "Develop a Django REST API",
            "Design eye-catching Instagram posts",
            "Translate documents from English to Spanish",
            "Write professional business emails",
            "Fix bugs in your Django application",
            "Design a UI/UX mockup for mobile app",
            "Create motion graphics for explainer video",
            "Optimize WordPress website speed",
            "Develop a MERN stack web application",
            "Create YouTube thumbnails and banners",
            "Edit podcasts with noise reduction",
            "Write product descriptions for e-commerce",
            "Redesign landing page for higher conversion",
            "Develop custom contact forms in Django",
            "Conduct keyword research for niche blogs"
        ]

        prices = [16, 32, 64, 128]

        for i in range(20):
            job_price = JobPrice.objects.create(price=random.choice(prices))
            job = Job.objects.create(
                name=job_titles[i],
                description=fake.paragraph(nb_sentences=15),
                price=job_price,
                category=random.choice(categories),
                created_by=random.choice(users),
                duration_days=random.randint(1, 14)
            )

            # Add 1-3 Images
            for _ in range(random.randint(1, 3)):
                image = self.create_fake_image(job.name)
                JobImage.objects.create(job=job, image=image)

            # Add 1-5 Reviews
            for _ in range(random.randint(1, 5)):
                Review.objects.create(
                    job=job,
                    user=random.choice(users),
                    ratings=random.randint(3, 5),
                    comment=fake.sentence(nb_words=12)
                )

            self.stdout.write(self.style.SUCCESS(f"Created job: {job.name}"))

        self.stdout.write(self.style.SUCCESS("✅ Done populating users, portfolios, jobs, images, and reviews."))
