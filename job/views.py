from job.models import Job, Category, Review, JobImage
from job.serializers import JobSerializer, CategorySerializer, ReviewSerializer, JobImageSerializer
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from job.filters import JobFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from job.paginations import DefaultPagination
from api.permissions import IsAdminOrReadOnly
from job.permissions import IsReviewAuthorOrReadOnly


class JobViewSet(ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    pagination_class = DefaultPagination
    search_fields = ['name', 'description']
    ordering_fields = ['price']
    permission_classes = [IsAdminOrReadOnly]


class JobImageViewSet(ModelViewSet):
    serializer_class = JobImageSerializer

    def get_queryset(self):
        return JobImage.objects.filter(product_id=self.kwargs['job_pk'])
    
    def perform_create(self, serializer):
        serializer.save(product_id=self.kwargs['job_pk'])


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Review.objects.filter(job_id=self.kwargs['job_pk'])

    def get_serializer_context(self):
        return {'job_id': self.kwargs['job_pk']}


