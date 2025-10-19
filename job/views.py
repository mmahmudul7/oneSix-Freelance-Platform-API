from job.models import Job, Category, Review, JobImage, JobPrice
from job.serializers import JobSerializer, CategorySerializer, ReviewSerializer, JobImageSerializer, JobPriceSerializer, JobSearchSerializer
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from job.filters import JobFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from job.paginations import DefaultPagination
from api.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated, AllowAny
from job.permissions import IsReviewAuthorOrReadOnly
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg
from django.db.models.functions import Coalesce
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema


class JobViewSet(ModelViewSet):
    """
    API endpoint for managing jobs in the OneSix freelance platform
     - Allows authenticated users to create, update, and delete their own jobs
     - Allows anyone to browse and filter jobs
     - Supports searching by name, description, and category
     - Supports ordering by price, average rating, and total orders
    """
    # queryset = Job.objects.select_related('category', 'created_by').prefetch_related('images')
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    pagination_class = DefaultPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'average_rating', 'order_count']
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Allow anyone to list and retrieve jobs, authenticated users for other actions
        """
        if self.action in ['list', 'retrieve', 'search']:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Job.objects.none()
        # return Job.objects.select_related('category', 'created_by').prefetch_related('images')
        queryset = Job.objects.all().select_related('price', 'category', 'created_by') \
                        .prefetch_related('images') \
                        .annotate(
                            average_rating_db=Coalesce(Avg('reviews__ratings'), 0.0),
                            order_count=Count('order_items', distinct=True)
                        )
        return queryset
    
    @swagger_auto_schema(
        operation_summary="Retrieve a list of jobs",
        operation_description="Fetches all jobs with optional filtering and sorting, accessible to anyone",
        responses={
            200: JobSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        """Retrieve all jobs available in the platform"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a single job",
        operation_description="Fetches details of a specific job by ID, accessible to anyone",
        responses={
            200: JobSerializer,
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve details of a specific job"""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new job",
        operation_description="Allows an authenticated user to create a job",
        request_body=JobSerializer,
        responses={
            201: JobSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a job by an authenticated user"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a job",
        operation_description="Allows the job creator to update their job",
        request_body=JobSerializer,
        responses={
            200: JobSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def update(self, request, *args, **kwargs):
        """Update a job by its creator"""
        if self.request.user != self.get_object().created_by:
            raise PermissionDenied("You can only update your own job")
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a job",
        operation_description="Allows the job creator to delete their job",
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a job by its creator"""
        if self.request.user != self.get_object().created_by:
            raise PermissionDenied("You can only delete your own job")
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Search jobs with advanced filters",
        operation_description="Search jobs by keyword, category, price range, rating, and duration, with sorting options, accessible to anyone",
        responses={
            200: JobSerializer(many=True),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])  # Search
    def search(self, request):
        """Search jobs with advanced filters and sorting"""
        serializer = JobSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # queryset = Job.objects.select_related('category', 'created_by').prefetch_related('images').annotate(
        #     avg_rating=Avg('reviews__ratings'),
        #     total_orders=Count('order_items')
        # )
        queryset = self.get_queryset()

        # Apply filters
        if data.get('keyword'):
            queryset = queryset.filter(
                Q(name__icontains=data['keyword']) |
                Q(description__icontains=data['keyword']) |
                Q(category__name__icontains=data['keyword']) |
                Q(created_by__email__icontains=data['keyword'])
            )
        if data.get('category'):
            queryset = queryset.filter(category=data['category'])
        if data.get('min_price'):
            queryset = queryset.filter(price__price__gte=data['min_price'])
        if data.get('max_price'):
            queryset = queryset.filter(price__price__lte=data['max_price'])
        if data.get('min_rating'):
            queryset = queryset.annotate(avg_rating=Avg('reviews__ratings')).filter(avg_rating__gte=data['min_rating'])
        if data.get('max_duration_days'):
            queryset = queryset.filter(duration_days__lte=data['max_duration_days'])

        # Apply sorting
        sort_by = data.get('sort_by')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('cart_price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-cart_price')
        elif sort_by == 'rating_desc':
            queryset = queryset.annotate(avg_rating=Avg('reviews__ratings')).order_by('-avg_rating')
        elif sort_by == 'orders_desc':
            queryset = queryset.annotate(total_orders=Count('order_items')).order_by('-total_orders')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        job = serializer.save(created_by=self.request.user)
        # Send notification to job creator
        send_mail(
            subject='Job Created Successfully',
            message=f'Dear {self.request.user.get_full_name() or self.request.user.email},\n\nYour job "{job.name}" has been created successfully.\n\nThank you!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.request.user.email],
            fail_silently=True,
        )

    def perform_update(self, serializer):
        job = serializer.save()
        send_mail(
            subject='Job Updated Successfully',
            message=f'Dear {self.request.user.get_full_name() or self.request.user.email},\n\nYour job "{job.name}" has been updated successfully.\n\nThank you!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.request.user.email],
            fail_silently=True,
        )


class JobImageViewSet(ModelViewSet):
    serializer_class = JobImageSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Allow anyone to list and retrieve job images; authenticated users for other actions
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary="Retrieve job images",
        operation_description="Fetches all images associated with a specific job, accessible to authenticated users",
        responses={
            200: JobImageSerializer(many=True),
            404: "Not Found"
        }
    )
    def list(self, request, *args, **kwargs):
        """Retrieve all images for a job"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Upload a job image",
        operation_description="Allows the job creator to upload an image for their job",
        request_body=JobImageSerializer,
        responses={
            201: JobImageSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def create(self, request, *args, **kwargs):
        """Upload an image for a job"""
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        return JobImage.objects.filter(job_id=self.kwargs.get('job_pk'))
    
    def perform_create(self, serializer):
        job = Job.objects.get(pk=self.kwargs['job_pk'])
        if self.request.user != job.created_by:
            raise PermissionDenied("You can only upload images for your own job")
        serializer.save(job_id=self.kwargs.get('job_pk'))


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer

    @swagger_auto_schema(
        operation_summary="Retrieve a list of categories",
        operation_description="Fetches all categories with job counts, accessible to anyone",
        responses={
            200: CategorySerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        """Retrieve all categories"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a category",
        operation_description="Allows admins to create a new category",
        request_body=CategorySerializer,
        responses={
            201: CategorySerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a category by admin"""
        return super().create(request, *args, **kwargs)


class JobPriceViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = JobPrice.objects.all()
    serializer_class = JobPriceSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve a list of job prices",
        operation_description="Fetches all job prices, accessible to anyone",
        responses={
            200: JobPriceSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        """Retrieve all job prices"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a job price",
        operation_description="Allows admins to create a new job price",
        request_body=JobPriceSerializer,
        responses={
            201: JobPriceSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a job price by admin"""
        return super().create(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadOnly]

    @swagger_auto_schema(
        operation_summary="Retrieve job reviews",
        operation_description="Fetches all reviews for a specific job, accessible to anyone",
        responses={
            200: ReviewSerializer(many=True),
            404: "Not Found"
        }
    )
    def list(self, request, *args, **kwargs):
        """Retrieve all reviews for a job"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a job review",
        operation_description="Allows buyers or sellers to create a review for a job after order completion",
        request_body=ReviewSerializer,
        responses={
            201: ReviewSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a review for a job by buyer or seller after order completion"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        job = Job.objects.get(pk=self.kwargs['job_pk'])
        user = self.request.user

        # Check if user is either buyer or seller of a completed order for this job
        order_item = job.order_items.filter(
            Q(order__is_completed=True) &
            (Q(order__user=user) | Q(freelancer=user))
        ).first()

        if not order_item:
            raise ValidationError("Only buyers or sellers of a completed order can review this job")

        serializer.save(user=user, job=job)

    def perform_update(self, serializer):
        review = self.get_object()
        if (timezone.now() - review.created_at).days > 16:
            raise ValidationError("Reviews cannot be updated after 16 days")
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Review.objects.filter(job_id=self.kwargs.get('job_pk'))

    def get_serializer_context(self):
        return {'job_id': self.kwargs.get('job_pk')}
