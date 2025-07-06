from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.models import User, Portfolio
from users.serializers import UserSerializer, PublicUserSerializer, PortfolioSerializer, FreelancerSearchSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Prefetch


class UserProfileViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        
        base_qs = User.objects.annotate(
            total_orders=Count('created_jobs__order_items', distinct=True),
            average_rating=Avg('created_jobs__reviews__ratings')
        ).prefetch_related(Prefetch('portfolio', queryset=Portfolio.objects.all()))

        if self.request.user.is_staff:
            return base_qs
        elif self.request.user.is_authenticated:
            return base_qs.filter(id=self.request.user.id)
        return base_qs

    def get_serializer_class(self):
        # Use PublicUserSerializer for retrieve and search actions to hide sensitive fields
        if self.action in ['retrieve', 'search']:
            return PublicUserSerializer
        return self.serializer_class

    def get_permissions(self):
        # Allow public access for retrieve and search actions
        if self.action in ['retrieve', 'search']:
            return [AllowAny()]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary="List user profiles",
        operation_description="Retrieve a list of user profiles. Admins can view all profiles, authenticated users can only view their own.",
        responses={
            200: UserSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve user profile",
        operation_description="Retrieve a specific user profile. Publicly accessible, but sensitive fields (e.g., email, phone_number) are excluded.",
        responses={
            200: PublicUserSerializer,
            404: "Not found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update a user profile. Users can only update their own profile.",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Invalid data",
            401: "Unauthorized",
            403: "Permission denied"
        }
    )
    def update(self, request, *args, **kwargs):
        if self.request.user != self.get_object():
            raise PermissionDenied("You can only update your own profile")
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Search freelancers",
        operation_description="Search freelancers by keyword, skills, location, minimum rating, or sort by rating, orders, or join date. Publicly accessible.",
        query_serializer=FreelancerSearchSerializer,
        responses={
            200: PublicUserSerializer(many=True),
            400: "Invalid query parameters"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def search(self, request):
        serializer = FreelancerSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        portfolio_prefetch = Prefetch('portfolio',queryset=Portfolio.objects.select_related('user').all())

        queryset = User.objects.annotate(
            total_orders=Count('created_jobs__order_items', distinct=True),
            average_rating=Avg('created_jobs__reviews__ratings')
        ).prefetch_related(portfolio_prefetch)

        if data.get('keyword'):
            queryset = queryset.filter(
                Q(bio__icontains=data['keyword'])
            )
        if data.get('skills'):
            queryset = queryset.filter(skills__contains=data['skills'])
        if data.get('location'):
            queryset = queryset.filter(location__icontains=data['location'])
        if data.get('min_rating'):
            queryset = queryset.annotate(avg_rating=Avg('created_jobs__reviews__ratings')).filter(avg_rating__gte=data['min_rating'])

        sort_by = data.get('sort_by')
        if sort_by == 'rating_desc':
            queryset = queryset.annotate(avg_rating=Avg('created_jobs__reviews__ratings')).order_by('-avg_rating')
        elif sort_by == 'orders_desc':
            queryset = queryset.annotate(total_orders=Count('created_jobs__order_items')).order_by('-total_orders')
        elif sort_by == 'created_at_desc':
            queryset = queryset.order_by('-date_joined')

        serializer = PublicUserSerializer(queryset, many=True)
        return Response(serializer.data)


class PortfolioViewSet(ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Portfolio.objects.none()
        if self.request.user.is_staff:
            return Portfolio.objects.all()
        elif self.request.user.is_authenticated:
            return Portfolio.objects.filter(user=self.request.user)
        return Portfolio.objects.all()  # Allow public access for retrieve

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if self.request.user != self.get_object().user:
            raise PermissionDenied("You can only update your own portfolio")
        serializer.save()

    @swagger_auto_schema(
        operation_summary="Create portfolio item",
        operation_description="Create a new portfolio item for the authenticated user.",
        request_body=PortfolioSerializer,
        responses={
            201: PortfolioSerializer,
            400: "Invalid data",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="List portfolio items",
        operation_description="Retrieve a list of portfolio items. Admins can view all, authenticated users can view their own.",
        responses={
            200: PortfolioSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve portfolio item",
        operation_description="Retrieve a specific portfolio item. Publicly accessible.",
        responses={
            200: PortfolioSerializer,
            404: "Not found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update portfolio item",
        operation_description="Update a portfolio item. Users can only update their own portfolio items.",
        request_body=PortfolioSerializer,
        responses={
            200: PortfolioSerializer,
            400: "Invalid data",
            401: "Unauthorized",
            403: "Permission denied"
        }
    )
    def update(self, request, *args, **kwargs):
        if self.request.user != self.get_object().user:
            raise PermissionDenied("You can only update your own portfolio")
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="List user's portfolio",
        operation_description="Retrieve all portfolio items for the authenticated user.",
        responses={
            200: PortfolioSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_portfolio(self, request):
        portfolio = Portfolio.objects.filter(user=self.request.user)
        serializer = self.get_serializer(portfolio, many=True)
        return Response(serializer.data)