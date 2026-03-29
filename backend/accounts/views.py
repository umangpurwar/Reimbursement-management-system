from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import UserPublicSerializer, UserSerializer

User = get_user_model()


class IsAdminOrSelf(permissions.BasePermission):
    """Allow full access to admins; users can only read/update themselves."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin or request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj == request.user
        return obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for User.

    - Admins see / manage all users.
    - Everyone else sees only themselves.
    """

    queryset = User.objects.select_related("manager").order_by("username")
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_serializer_class(self):
        if self.request.user.is_admin or self.request.user.is_staff:
            return UserSerializer
        return UserPublicSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(pk=user.pk)

    @action(detail=True, methods=["get"])
    def direct_reports(self, request: Request, pk=None) -> Response:
        """Return all users whose manager is this user."""
        manager = self.get_object()
        reports = manager.get_direct_reports().select_related("manager")
        serializer = UserPublicSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """Shortcut: return the currently authenticated user."""
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)