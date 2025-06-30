from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from users.models import User, Portfolio
from users.serializers import UserSerializer, PortfolioSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class UserProfileViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to view their own profile, admins can view all
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        # Only allow users to update their own profile
        if self.request.user != self.get_object():
            raise PermissionDenied("You can only update your own profile")
        serializer.save()


class PortfolioViewSet(ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
    