from rest_framework.response import Response
from rest_framework import status
from job.models import Job, Category, Review
from job.serializers import JobSerializer, CategorySerializer, ReviewSerializer
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet


class JobViewSet(ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if job.price > 499:
            return Response({
                'Message': "Job with price more then 499 could not be deleted"
            })
        self.perform_destroy(job)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(job_id=self.kwargs['job_pk'])

    def get_serializer_context(self):
        return {'job_id': self.kwargs['job_pk']}


