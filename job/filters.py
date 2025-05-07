from django_filters.rest_framework import FilterSet
from job.models import Job

class JobFilter(FilterSet):
    class Meta:
        model = Job
        fields = {
            'category_id': ['exact'],
            'price': ['gt', 'lt'],
        }