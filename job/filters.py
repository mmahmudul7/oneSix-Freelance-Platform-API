from django_filters import rest_framework as filters
from job.models import Job, Category
from django.db.models import Avg, Q


class JobFilter(filters.FilterSet):
    keyword = filters.CharFilter(method='filter_keyword')
    category = filters.ModelChoiceFilter(queryset=Category.objects.all())
    min_price = filters.NumberFilter(field_name='price__price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price__price', lookup_expr='lte')
    min_rating = filters.NumberFilter(method='filter_min_rating')  # rating filter
    max_duration_days = filters.NumberFilter(field_name='duration_days', lookup_expr='lte')
    creator_email = filters.CharFilter(field_name='created_by__email', lookup_expr='icontains')

    class Meta:
        model = Job
        fields = ['keyword', 'category', 'min_price', 'max_price', 'min_rating', 'max_duration_days', 'creator_email']

    def filter_keyword(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__name__icontains=value)
        )

    def filter_min_rating(self, queryset, name, value):
        return queryset.annotate(avg_rating=Avg('reviews__ratings')).filter(avg_rating__gte=value)