from django.conf import settings as default_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.utils.timezone import now
from djoser import utils
from djoser.compat import get_user_email
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import generics, response, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from api.email import ActivateAccountEmail
from api.models import AutoFollow
from api.serializers.auth import (
    SocialAuthSerializer, DraftUserSerializer,
    IsValidUsernameSerializer, RegisterSocialUserSerializer,
    AutoFollowSerializer, CustomTokenRefreshSerializer, RenamingTokenObtainPairSerializer
)

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def join_link(request):
    link = default_settings.LINK_JOIN
    return Response({'join_link': link})


class SocialView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SocialAuthSerializer


class SocialAuthView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSocialUserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = RenamingTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            update_last_login(User, user)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomRefreshTokenView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class CustomUserViewSet(UserViewSet):

    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        if user:
            context = {"user": user}
            to = [get_user_email(user)]
            settings.EMAIL.password_reset(self.request, context).send(to)

        return response.Response({
            'token': f'{default_token_generator.make_token(user)}-{utils.encode_uid(user.pk)}'
        }, status=status.HTTP_200_OK)

    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.user.set_password(serializer.data["new_password"])
        if hasattr(serializer.user, "last_login"):
            serializer.user.last_login = now()
        serializer.user.save()

        if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": serializer.user}
            to = [get_user_email(serializer.user)]
            settings.EMAIL.password_changed_confirmation(self.request, context).send(to)
        return response.Response({"detail": "Done"})

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": self.request.user}
            to = [get_user_email(self.request.user)]
            settings.EMAIL.password_changed_confirmation(self.request, context).send(to)

        if settings.LOGOUT_ON_PASSWORD_CHANGE:
            raise Exception('This settings not implemented')
        elif settings.CREATE_SESSION_ON_LOGIN:
            raise Exception('This settings not implemented')
        return response.Response({"detail": "Done"})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response(serializer.login(), status=status.HTTP_201_CREATED)


class IsValidUsernameView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = IsValidUsernameSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        return response.Response({'is_valid': is_valid}, status=status.HTTP_200_OK)


class CreateDraftUser(generics.CreateAPIView):
    serializer_class = DraftUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=False)
        if is_valid:
            self.perform_create(serializer)
        return response.Response({'is_valid': is_valid}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

        instance = serializer.instance
        context = {"draft_user": instance}
        to = [instance.email]
        ActivateAccountEmail(self.request, context).send(to)


class ActivateDraftUser(generics.CreateAPIView):
    serializer_class = DraftUserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        is_valid = serializer.is_valid(raise_exception=False)
        is_active = serializer.activate(kwargs.get(self.lookup_field))
        return response.Response({'is_valid': is_valid and is_active}, status=status.HTTP_200_OK)


class AutoFollowList(generics.ListAPIView):
    queryset = AutoFollow.objects.all().order_by('sort_order')
    serializer_class = AutoFollowSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination
