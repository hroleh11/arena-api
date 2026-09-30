from django.contrib.auth import get_user_model
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenVerifyView

from api.views import auth
from api.views.auth import CustomRefreshTokenView, CustomTokenObtainPairView

router = DefaultRouter()
router.register("auth/users", auth.CustomUserViewSet, basename='user')

User = get_user_model()


schema_view = get_schema_view(
    openapi.Info(
        title="Content API",
        default_version='v1',
        description="",
        # terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="y.berkutov@artk.ai"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(JWTAuthentication,),
)

urlpatterns = [
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),

    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name="jwt-create"),
    path('auth/jwt/refresh/', CustomRefreshTokenView.as_view(), name="jwt-refresh"),
    path('auth/jwt/verify/', TokenVerifyView.as_view(), name="jwt-verify"),

    path('auth/social/<str:social>/', auth.SocialView.as_view()),
    path('auth/social/<str:social>/<str:partial_token>', auth.SocialAuthView.as_view()),
    path('api/', include('api.urls')),
    path('api/v2/', include('api.versioned.v2.urls')),

    path('api_v2/', include('api_v2.urls')),
] + router.urls
