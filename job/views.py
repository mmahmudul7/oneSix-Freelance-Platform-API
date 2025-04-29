from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from job.models import Job, Category
from job.serializers import JobSerializer, CategorySerializer
from django.db.models import Count
from rest_framework.views import APIView


class ViewJobs(APIView):
    def get(self, request):
        jobs = Job.objects.select_related('category').all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ViewSpecificJob(APIView):
    def get(self, request, id):
        job = get_object_or_404(Job, pk=id)
        serializer = JobSerializer(job)
        return Response(serializer.data)
    
    def put(self, request, id):
        job = get_object_or_404(Job, pk=id)
        serializer = JobSerializer(job, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def delete(self, request, id):
        job = get_object_or_404(Job, pk=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ViewCategories(APIView):
    def get(self, request):
        categories = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ViewSpecificCategory(APIView):
    def get(self, request, pk):
        category = get_object_or_404(
            Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs'),
            pk=pk
        )
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    
    def put(self, request, pk):
        category = get_object_or_404(
            Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs'),
            pk=pk
        )
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data)
    
    def delete(self, request, pk):
        category = get_object_or_404(
            Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs'),
            pk=pk
        )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)