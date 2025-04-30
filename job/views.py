from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from job.models import Job, Category
from job.serializers import JobSerializer, CategorySerializer
from django.db.models import Count
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


class JobList(ListCreateAPIView):
    queryset = Job.objects.select_related('category').all()
    serializer_class = JobSerializer


class JobDetails(RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def delete(self, request, pk):
        job = get_object_or_404(Job, pk = pk)
        if job.price > 499:
            return Response(
                {
                    'Message': "Job with price more then 499 could not be deleted"
                }
            )
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
 

class CategoriesList(ListCreateAPIView):
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer


class CategoryDetails(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer_class = CategorySerializer
