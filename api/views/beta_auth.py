from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import response, views, status, generics, permissions
from rest_framework.serializers import ValidationError
from api.email import ActivateAccountEmail
from api.models import BetaUsers, DraftProfile, BetaRefCode
from api.serializers import beta_auth
from api.shortcust import generate_deep_link
from column.celery import app
from django.conf import settings
from api.serializers.auth import DraftUserSerializer


class WaitListView(generics.CreateAPIView):
    serializer_class = beta_auth.EmailSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        app.send_task('column.tasks.move2waitlist',
                      args=[request.data],
                      queue='admin')
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class CreateBetaUser(generics.CreateAPIView):
    serializer_class = beta_auth.BetaUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response.Response({'is_valid': True})
    #     serializer = self.get_serializer(data=request.data)
    #     try:
    #         is_valid = serializer.is_beta_user()
    #     except ValidationError as err:
    #         return response.Response(err.detail, status=status.HTTP_400_BAD_REQUEST)
    #
    #     if not is_valid:
    #         data = {'email': request.data.get('email', None)}
    #         try:
    #             self.create_draft_user(request, data)
    #         except ValidationError as err:
    #             print()
    #             return response.Response(err.detail, status=status.HTTP_400_BAD_REQUEST)
    #     return response.Response({'is_valid': is_valid})
    #
    # @staticmethod
    # def create_draft_user(request, data):
    #     serializer = DraftUserSerializer(data=data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     instance = serializer.instance
    #     context = {"draft_user": instance}
    #     to = [instance.email]
    #     ActivateAccountEmail(request, context).send(to)

        # if is_valid:
        #
        #     is_beta_user = serializer.is_beta_user()
        #     if is_beta_user:
        #         return response.Response({'is_valid': is_beta_user}, status=status.HTTP_201_CREATED)
        #
        #     is_ref_user = serializer.is_ref_user()
        #     if is_ref_user:
        #         self.perform_create(serializer)
        #         return response.Response({'is_valid': is_ref_user}, status=status.HTTP_201_CREATED)
        #
        #     return response.Response({'is_valid': False}, status=status.HTTP_400_BAD_REQUEST)
        #
        # return response.Response({'is_valid': is_valid}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        instance = serializer.save_draft()

        context = {"draft_user": instance}
        to = [instance.email]
        ActivateAccountEmail(self.request, context).send(to)


class ActivateBetaUser(generics.CreateAPIView):
    serializer_class = DraftUserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        is_valid = serializer.is_valid(raise_exception=False)
        is_active = serializer.activate(kwargs.get(self.lookup_field))
        return response.Response({'is_valid': is_valid and is_active}, status=status.HTTP_200_OK)

    # serializer_class = beta_auth.BetaUserSerializer
    # permission_classes = [permissions.AllowAny]
    # lookup_field = 'code'
    #
    # def create(self, request, *args, **kwargs):
    #     serializer = self.serializer_class(data=request.data)
    #     is_valid = serializer.is_valid(raise_exception=False)
    #     data = serializer.activate(kwargs.get(self.lookup_field))
    #     if is_valid and data:
    #         return response.Response(data, status=status.HTTP_200_OK)
    #     return response.Response(status=status.HTTP_400_BAD_REQUEST)


class InviteUser(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        email = request.user.email
        ref_code = self.get_ref_code(email)
        link, status_code = generate_deep_link(settings.VYLO_URL, ref_code=ref_code)
        return response.Response({'invite_link': link}, status=status_code)

    @staticmethod
    def get_ref_code(email):
        beta_user = BetaUsers.objects.filter(email=email).first()

        if beta_user:
            return beta_user.active_code.code
        else:
            draft = DraftProfile.objects.filter(email=email).first()
            draft_code = BetaRefCode.objects.filter(ref_users=draft).first()

            if draft_code:
                return draft_code.code
        return ''


class InviteCode(views.APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING)
            },
        )
    )
    def post(self, request, **kwargs):
        code = request.data.get('code', None)
        if code in settings.UNIVERSAL_CODES or BetaRefCode.objects.filter(code=code).first():
            return response.Response({'is_valid': True})

        return response.Response({"code": ["Code is invalid. Please try again"]}, status=status.HTTP_400_BAD_REQUEST)
