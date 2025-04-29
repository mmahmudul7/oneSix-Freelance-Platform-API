from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from job.models import Job, Category
from job.serializers import JobSerializer, CategorySerializer
from django.db.models import Count


@api_view(['GET', 'POST'])
def view_jobs(request):
    if request.method == 'GET':
        jobs = Job.objects.select_related('category').all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def view_specific_job(request, id):
    if request.method == 'GET':
        job = get_object_or_404(Job, pk=id)
        serializer = JobSerializer(job)
        return Response(serializer.data)
    if request.method == 'PUT':
        job = get_object_or_404(Job, pk=id)
        serializer = JobSerializer(job, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    if request.method == 'DELETE':
        job = get_object_or_404(Job, pk=id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view()
def view_categories(request):
    categories = Category.objects.annotate(job_count=Count('jobs')).prefetch_related('jobs')
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view()
def view_specific_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    serializer = CategorySerializer(category)
    return Response(serializer.data)