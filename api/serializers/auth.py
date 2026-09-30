from datetime import datetime, timedelta

import django.contrib.auth.password_validation as validators
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.core import exceptions as dj_exceptions
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from djoser import utils
from djoser.conf import settings
from djoser.serializers import UserCreateSerializer
from requests.exceptions import HTTPError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from six import text_type
from social_core import exceptions
from social_core.utils import partial_pipeline_data
from social_django.utils import load_backend, load_strategy
from social_django.views import _do_login

from api.models import Categories, Profile, DraftProfile, AutoFollow
from api.validators import validate_email, validate_username
from api.errors import SIGN_UP, FORGOT_PASSWORD

# from social_core.actions import do_complete

User = get_user_model()


class EmailResetSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email',)

    def get_user(self, is_active=True):
        try:
            return User.objects.get(is_active=is_active, **{'email': self.data.get('email', "")})
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': ["User with given email does not exist."]})


class CustomPasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField()
    re_new_password = serializers.CharField()

    default_error_messages = {
        "invalid_token": settings.CONSTANTS.messages.INVALID_TOKEN_ERROR,
        "password_mismatch": FORGOT_PASSWORD['CONFIRM-PASSWORD_MATCH'],
        "equal_with_old_pass": FORGOT_PASSWORD['CONFIRM-PASSWORD_EQUAL_WITH_OLD']
    }

    def validate(self, attrs):
        try:
            ts_b36, _, uid = attrs.get('token').split("-")

            uid = utils.decode_uid(uid)
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            key_error = "invalid_token"
            raise ValidationError(
                {"token": [self.error_messages[key_error]]}, code=key_error
            )

        self._validate_token(attrs.get('code'))
        self._validate_password(attrs.get('new_password'), attrs.get('re_new_password'))

        is_token_valid = self.context["view"].token_generator.check_token(
            self.user, f'{ts_b36}-{_}'
        )
        if is_token_valid:
            return attrs
        else:
            key_error = "invalid_token"
            raise ValidationError(
                {"token": [self.error_messages[key_error]]}, code=key_error
            )

    def _validate_token(self, code):
        try:
            reset_code = self.user.reset_code
        except User.DoesNotExist:
            raise ValidationError({"code": FORGOT_PASSWORD['CODE_USER']})

        if reset_code.tries <= 0:
            raise ValidationError({"code": FORGOT_PASSWORD['CODE_TRIES'] % {'tries': reset_code.tries}})

        if reset_code.code != code:
            reset_code.tries -= 1
            reset_code.save()
            raise ValidationError({"code": FORGOT_PASSWORD['CODE_TRIES'] % {'tries': reset_code.tries}})

        if self.is_expired(reset_code.updated_at):
            raise ValidationError({"code": FORGOT_PASSWORD['CODE_EXPIRED']})

    def _validate_password(self, new_password, re_new_password):
        if self.user.check_password(new_password):
            raise ValidationError({"new_password": FORGOT_PASSWORD['CONFIRM-PASSWORD_EQUAL_WITH_OLD']})
        if new_password != re_new_password:
            # self.fail("password_mismatch")
            raise ValidationError({"new_password": FORGOT_PASSWORD['CONFIRM-PASSWORD_MATCH']})

        try:
            validators.validate_password(password=new_password, user=self.user)
        except dj_exceptions.ValidationError as e:
            raise serializers.ValidationError({"news_password": list(e.messages)})

    @staticmethod
    def is_expired(timestamp: datetime) -> bool:
        return True if datetime.now(timezone.utc) > timestamp + timedelta(minutes=5) else False


class ProfileRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name', 'gender', 'birthday_date', 'is_remember_me']


class ProfileTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['global_id', 'profile_photo', 'name',
                  'website', 'phone', 'gender', 'have_access_to_vylo_props']


class RegisterSocialUserSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(write_only=True, required=True)
    gender = serializers.CharField(write_only=True, required=True)
    birthday_date = serializers.DateField(write_only=True, required=False)
    is_remember_me = serializers.BooleanField(write_only=True, required=False)
    signup_code = serializers.CharField(write_only=True, required=False)

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @staticmethod
    def validate_username(username: str):
        return validate_username(username.lower())

    @staticmethod
    def validate_password(password):
        return validators.validate_password(password)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request = self.context['request']
        kwargs = self.context["view"].kwargs

        request.social_strategy = load_strategy(request)

        if not hasattr(request, 'strategy'):
            request.strategy = request.social_strategy

        try:
            request.backend = load_backend(request.social_strategy, kwargs.get('social'), '/')
        except exceptions.MissingBackend:
            raise Http404('Backend not found')

        backend = request.backend
        partial = partial_pipeline_data(backend, None, request=request,
                                        partial_token=kwargs.get('partial_token'), end_partial=True,
                                        **attrs)
        user = backend.continue_pipeline(partial)
        backend.strategy.clean_partial_pipeline(partial.token)
        social_user = user.social_user
        _do_login(backend, user, social_user)
        backend.strategy.session_set('social_auth_last_login_backend', social_user.provider)
        return {'user': user}

    def create(self, validated_data):
        user = validated_data.get('user')

        refresh = RefreshToken.for_user(user)
        refresh['profile'] = ProfileTokenSerializer(user.profile).data
        refresh['user'] = {
            'username': user.username,
            'email': user.email
        }

        return {
            "access": text_type(refresh.access_token),
            "refresh": text_type(refresh),
        }


class RegisterUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(source='profile.name', required=True)
    gender = serializers.CharField(source='profile.gender', required=True)
    birthday_date = serializers.DateField(source='profile.birthday_date', required=False)
    is_remember_me = serializers.BooleanField(source="profile.is_remember_me", required=False)
    signup_code = serializers.CharField(source="profile.signup_code", required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'name', 'gender', 'birthday_date', 'is_remember_me', 'signup_code')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_username(self, username: str):
        return validate_username(username.lower(), self.instance)

    def validate_email(self, email):
        return validate_email(email, self.instance)

    def validate(self, attrs):
        profile_data = attrs.pop('profile', None)
        ProfileRegisterSerializer(data=profile_data).is_valid(raise_exception=True)
        attrs = super().validate(attrs)
        attrs['profile'] = profile_data
        return attrs

    def perform_create(self, validated_data):
        profile_data = validated_data.pop('profile', dict())

        with transaction.atomic():
            password = validated_data.pop('password', None)

            user = User(**validated_data)
            user.set_password(password)
            user.is_active = False if settings.SEND_ACTIVATION_EMAIL else True

            user._profile = profile_data
            user.save()
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        user = super().update(instance, validated_data)
        self.profile_update(profile_data, user.profile)
        return user

    @staticmethod
    def profile_update(data, profile):
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()

    def login(self):
        user = self.instance
        refresh = RefreshToken.for_user(user)
        refresh['profile'] = ProfileTokenSerializer(user.profile).data
        refresh['user'] = {
            'username': user.username,
            'email': user.email
        }
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }


class RenamingTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['profile'] = ProfileTokenSerializer(user.profile).data  # .profile.name
        token['user'] = {
            'username': user.username,
            'email': user.email
        }

        return token

    def validate(self, attrs):
        user_obj = User.objects.filter(email__iexact=attrs.get("username", '')).first() or User.objects.filter(
            username__iexact=attrs.get("username")).first()
        if user_obj:
            attrs['username'] = user_obj.username
        return super().validate(attrs)


class CustomRefreshToken(RefreshToken):
    @property
    def access_token(self) -> AccessToken:
        """
        Returns an access token created from this refresh token.  Copies all
        claims present in this refresh token to the new access token except
        those claims listed in the `no_copy_claims` attribute.
        """
        user_global_id = self.payload.get('profile').get('global_id')
        profile = Profile.objects.filter(global_id=user_global_id).first()
        update_last_login(User, profile.user)

        user_data = self.payload.get('user')

        if not user_data:
            self.payload['user'] = {
                'username': profile.user.username,
                'email': profile.user.email
            }
        self.payload['profile'] = ProfileTokenSerializer(profile).data

        access = super().access_token

        return access


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = CustomRefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

            data["refresh"] = str(refresh)

        return data


class SocialAuthSerializer(serializers.Serializer):
    TOKEN_NAMES = {
        'facebook': 'access_token',
        'google-plus': 'id_token',
        'apple-id': 'id_token'
    }

    is_new = serializers.BooleanField(read_only=True)
    access = serializers.CharField(allow_null=True, read_only=True)
    refresh = serializers.CharField(allow_null=True, read_only=True)
    partial_token = serializers.CharField(allow_null=True, read_only=True)

    def create(self, validated_data):
        auth = validated_data.get('auth')
        user_info = dict(is_new=auth.is_new, partial_token=None, access=None, refresh=None)
        # print(auth.__dict__)
        if auth.is_new:
            user_info['partial_token'] = auth.partial_token
        elif auth.is_active:
            refresh = RefreshToken.for_user(auth)
            refresh['profile'] = ProfileTokenSerializer(auth.profile).data
            refresh['user'] = {
                'username': auth.username,
                'email': auth.email
            }

            user_info['access'] = str(refresh.access_token)
            user_info['refresh'] = str(refresh)
        else:
            raise AuthenticationFailed({'details': ['No active account found with the given credentials']})
        return user_info

    def validate(self, attrs):
        request = self.context["request"]
        social = self.context["view"].kwargs["social"]
        token_name = self.TOKEN_NAMES[social]

        strategy = load_strategy(request)
        try:
            backend = load_backend(strategy, social, redirect_uri='/')
        except exceptions.MissingBackend:
            raise Http404('Backend not found')
        try:
            auth = backend.do_auth(access_token=request.POST.get(token_name))
        except exceptions.AuthException as e:
            raise serializers.ValidationError(str(e))
        except HTTPError as e:
            raise serializers.ValidationError(str(e))
        return {'auth': auth}


class PublishersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['global_id', 'name']


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['global_id', 'name']


class IsValidUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, username: str):
        return validate_username(username.lower())


class DraftUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                User.objects.all(),
                message=SIGN_UP['EMAIL_IN_USE']
            )
        ]
    )

    class Meta:
        model = DraftProfile
        fields = ('email', 'code', 'tries', 'is_active')
        read_only_fields = ('code', 'tries', 'is_active')

    def create(self, validated_data):
        instance, created = DraftProfile.objects.get_or_create(email=validated_data.pop('email', ''),
                                                               defaults=validated_data)
        return instance

    def activate(self, code):
        email = self.validated_data.get('email')
        prof = DraftProfile.objects.filter(email=email).first()
        if hasattr(prof, 'code'):
            if code == prof.code and prof.tries > 0:
                prof.is_active = True
                prof.save()
                return True
            elif code != prof.code and prof.tries > 0:
                prof.tries -= 1
                prof.save()
        return False


class AutoFollowSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='profile.id')
    name = serializers.CharField(source='profile.name', allow_null=True)
    global_id = serializers.CharField(source='profile.global_id')
    username = serializers.CharField(source='profile.user.username')
    profile_photo = serializers.ImageField(source='profile.profile_photo', use_url=True, allow_null=True)
    is_approved = serializers.BooleanField(source='profile.is_approved')
    description = serializers.SerializerMethodField()

    class Meta:
        model = AutoFollow
        fields = ('id', 'name', 'username', 'profile_photo', 'global_id', 'is_approved', 'description')

    @staticmethod
    def get_description(obj):
        description = obj.description
        return description if description else obj.profile.bio
