from rest_framework.response import Response
from rest_framework import status
from job.models import Job, Category
from job.serializers import JobSerializer, CategorySerializer
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