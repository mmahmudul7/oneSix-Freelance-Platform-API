from job.models import Job, Category, Review, JobImage, JobPrice
from job.serializers import JobSerializer, CategorySerializer, ReviewSerializer, JobImageSerializer, JobPriceSerializer
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from job.filters import JobFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from job.paginations import DefaultPagination
from api.permissions import IsAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated
from job.permissions import IsReviewAuthorOrReadOnly
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg
# from drf_yasg.utils import swagger_auto_schema


class JobViewSet(ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.select_related('category', 'created_by').prefetch_related('images')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    pagination_class = DefaultPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'average_rating', 'total_orders']
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Job.objects.none()
        return Job.objects.select_related('category', 'created_by').prefetch_related('images')

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
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[])  # Search
    def search(self, request):
        serializer = JobSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queryset = Job.objects.select_related('category', 'created_by').prefetch_related('images')

        # Apply filters
        if data.get('keyword'):
            queryset = queryset.filter(
                Q(name__icontains=data['keyword']) |
                Q(description__icontains=data['keyword'])
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
            queryset = queryset.order_by('price__price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price__price')
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


class JobImageViewSet(ModelViewSet):
    serializer_class = JobImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobImage.objects.filter(job_id=self.kwargs.get('job_pk'))
    
    def perform_create(self, serializer):
        serializer.save(job_id=self.kwargs.get('job_pk'))


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer


class JobPriceViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = JobPrice.objects.all()
    serializer_class = JobPriceSerializer


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Review.objects.filter(job_id=self.kwargs.get('job_pk'))

    def get_serializer_context(self):
        return {'job_id': self.kwargs.get('job_pk')}
