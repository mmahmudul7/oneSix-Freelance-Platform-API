from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from job.validators import validate_file_size


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class JobPrice(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"${self.price}"


class Job(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.ForeignKey(JobPrice, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="jobs")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_jobs")
    duration_days = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Number of days required to complete the job") 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id',]
        indexes = [
            models.Index(fields=['name', 'description', 'category']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.ratings for review in reviews) / reviews.count()
        return 0

    @property
    def total_orders(self):
        return self.order_items.count()


class JobImage(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="jobs/images/", validators=[validate_file_size])

    def __str__(self):
        return f"Image for {self.job.name}"


class Review(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ratings = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['job', 'created_at']),
        ]

    def __str__(self):
        return f"Review for {self.job.name} by {self.user}"
