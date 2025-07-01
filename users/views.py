from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from users.models import User, Portfolio
from users.serializers import UserSerializer, PortfolioSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from rest_framework.exceptions import PermissionDenied


class UserProfileViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        # Allow users to view their own profile, admins can view all
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        # Only allow users to update their own profile
        if self.request.user != self.get_object():
            raise PermissionDenied("You can only update your own profile")
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[])  # Freelancer search
    def search(self, request):
        serializer = UserSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queryset = User.objects.all()

        # Apply filters
        if data.get('keyword'):
            queryset = queryset.filter(
                Q(email__icontains=data['keyword']) |
                Q(bio__icontains=data['keyword'])
            )
        if data.get('skills'):
            queryset = queryset.filter(skills__contains=data['skills'])
        if data.get('location'):
            queryset = queryset.filter(location__icontains=data['location'])
        if data.get('min_rating'):
            queryset = queryset.annotate(avg_rating=Avg('created_jobs__reviews__ratings')).filter(avg_rating__gte=data['min_rating'])

        # Apply sorting
        sort_by = data.get('sort_by')
        if sort_by == 'rating_desc':
            queryset = queryset.annotate(avg_rating=Avg('created_jobs__reviews__ratings')).order_by('-avg_rating')
        elif sort_by == 'orders_desc':
            queryset = queryset.annotate(total_orders=Count('created_jobs__order_items')).order_by('-total_orders')
        elif sort_by == 'created_at_desc':
            queryset = queryset.order_by('-date_joined')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PortfolioViewSet(ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Portfolio.objects.none()
        # Users can view their own portfolio, admins can view all
        if self.request.user.is_staff:
            return Portfolio.objects.all()
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow users to update their own portfolio
        if self.request.user != self.get_object().user:
            raise PermissionDenied("You can only update your own portfolio")
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_portfolio(self, request):
        portfolio = Portfolio.objects.filter(user=request.user)
        serializer = self.get_serializer(portfolio, many=True)
        return Response(serializer.data)
    