import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from decimal import Decimal
from qrcode import QRCode
from qrcode.image.styles.moduledrawers.svg import SvgPathSquareDrawer
from qrcode.image.svg import SvgPathImage
from rest_framework import serializers

from api.models import Profile, ReportedProfiles, BlockedProfiles
from api.serializers import categories, publishers
from api.validators import validate_username, validate_name

User = get_user_model()


GREETING = _('Find me on Vylo! ')


class ProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', max_length=50, required=False)
    email = serializers.EmailField(read_only=True, source='user.email')
    categories_subscription = categories.CategoriesSerializer(many=True, read_only=True)
    publishers_subscription = serializers.SerializerMethodField(read_only=True)
    personal_link = serializers.SerializerMethodField(read_only=True)
    post_counter = serializers.SerializerMethodField(read_only=True)
    followers_counter = serializers.SerializerMethodField(read_only=True)
    following_counter = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'global_id', 'username', 'email', 'profile_photo',
                  'profile_photo_svg', 'name', 'is_source', 'is_creator', 'website', 'is_approved',
                  'bio', 'phone', 'gender', 'categories_subscription', 'publishers_subscription',
                  'personal_link', 'post_counter', 'followers_counter', 'following_counter',
                  'birthday_date', 'timezone', 'creator_cash')
        extra_kwargs = {
            'global_id': {'read_only': True},
            'is_source': {'read_only': True},
            'id': {'read_only': True},
        }

    def validate_username(self, username: str):
        return validate_username(username.lower(), instance=getattr(self.instance, 'user', None))

    @staticmethod
    def validate_timezone(timezone):
        if not pytz.all_timezones_set.__contains__(timezone):
            raise serializers.ValidationError(_("Invalid timezone"))
        return timezone

    @staticmethod
    def validate_name(name: str):
        return validate_name(name)

    @staticmethod
    def get_post_counter(profile):
        status_approved = 3
        return profile.publisher_news.filter(status=status_approved).count()

    @staticmethod
    def get_followers_counter(profile):
        return profile.prof_subscribers.count()

    @staticmethod
    def get_following_counter(profile):
        return profile.publishers_subscription.count()

    @staticmethod
    def get_publishers_subscription(profile):
        query_set = profile.publishers_subscription.order_by('name')
        return publishers.PublishersSerializer(instance=query_set, many=True).data

    @staticmethod
    def get_personal_link(profile):
        url = settings.VYLO_URL + '/@' + profile.username
        return GREETING + url

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            serializer = ProfileUserSerializer(
                instance.user, data=validated_data.pop('user'))

            if serializer.is_valid(raise_exception=True):
                serializer.save()
        return super().update(instance, validated_data)


class QRCodeSerializer(serializers.ModelSerializer):
    greeting = serializers.SerializerMethodField()
    additional_info = serializers.SerializerMethodField()
    qrcode = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('profile_photo', 'username', 'greeting', 'additional_info', 'qrcode')

    @staticmethod
    def get_greeting(*args, **kwargs):
        return GREETING

    @staticmethod
    def get_qrcode(profile):
        url = settings.VYLO_URL + '/@' + profile.username

        qr = QRCode(image_factory=SvgPathImage)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(module_drawer=SvgPathSquareDrawer(size_ratio=Decimal(0.7)))
        img.save(settings.BASE_DIR / 'test_img.svg')
        return img.to_string(encoding='unicode')

    @staticmethod
    def get_additional_info(*args, **kwargs):
        return _("""Watch video responses to sport & lifestyle 
                    news from professional athletes, 
                    personalities, creators, and friends""")


class ExternalProfileSerializer(ProfileSerializer):
    im_following = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField(read_only=True)
    is_blocked_by_me = serializers.SerializerMethodField(read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = ('id', 'global_id', 'username', 'email', 'profile_photo',
                  'profile_photo_svg', 'name', 'is_source', 'website', 'is_approved',
                  'bio', 'phone', 'gender', 'categories_subscription', 'publishers_subscription',
                  'personal_link', 'post_counter', 'followers_counter', 'following_counter',
                  'birthday_date', 'im_following', 'is_creator', 'is_blocked_by_me')

    def get_im_following(self, profile):
        request = self.context.get('request')
        if request is None:
            return False
        return request.user.profile.publishers_subscription.filter(id=profile.id).exists()

    def get_is_blocked_by_me(self, profile):
        request = self.context.get('request')
        if request is None:
            return False
        return request.user.profile.i_block_users.filter(blocked_profile__id=profile.id).exists()

    @staticmethod
    def get_is_creator(is_creator):
        return False  # Mocked function to IOS support


class ProfileWebSerializer(ProfileSerializer):
    headers = serializers.SerializerMethodField()
    personal_link = serializers.SerializerMethodField()
    web_external_link = serializers.SerializerMethodField()

    class Meta(ProfileSerializer.Meta):
        fields = ('username', 'name', 'website', 'bio', 'profile_photo',
                  'post_counter', 'followers_counter', 'following_counter',
                  'headers', 'personal_link', 'web_external_link')

    @staticmethod
    def get_personal_link(profile):
        return profile.personal_link

    @staticmethod
    def get_headers(profile):
        og_image = profile.profile_photo
        return {
            "title": profile.username,
            "description": profile.bio,
            "og_image": getattr(og_image, 'url', ''),
            "android": {
                'name': settings.PROJECT_NAME,
                'url': settings.ANDROID_URL_GOOGLE_STORE,
                'package': settings.ANDROID_PACKAGE_NAME
            },
            "ios": {
                'name': settings.PROJECT_NAME,
                'url': settings.APPLE_URL_APP_STORE,
                'id': settings.APPLE_ID_APP_STORE,
                # 'arguments': f'ngid={feed.global_id}'
            }
        }

    @staticmethod
    def get_web_external_link(profile):
        return profile.personal_link


class ProfileImageSaveSerializer(serializers.ModelSerializer):
    media_type = 'image/*'

    class Meta:
        model = Profile
        fields = ['profile_photo']


class ProfileGlobalIdField(serializers.RelatedField):
    def get_queryset(self):
        print('get query set')
        return Profile.objects.all()

    def to_representation(self, instance):
        return instance.global_id

    def to_internal_value(self, data):
        try:
            profile = Profile.objects.get(global_id=data)
        except Profile.DoesNotExist:
            raise serializers.ValidationError(
                f"Profile [global id {data}] does not exist")
        return profile


class ReportProfilesSerializer(serializers.ModelSerializer):
    reported_profile_global_id = ProfileGlobalIdField(many=False)

    class Meta:
        model = ReportedProfiles
        fields = ('reported_profile_global_id', 'status')

    def validate(self, attrs):
        reporter = self.context.get('request').user.profile
        try:
            ReportedProfiles.objects.get(
                reporter_profile=reporter,
                reported_profile=attrs.get('reported_profile_global_id'))
            raise serializers.ValidationError(
                f"Duplicate report {attrs.get('reported_profile_global_id')}")
        except ReportedProfiles.DoesNotExist:
            pass
        return super().validate(attrs)

    def create(self, validated_data):
        reporter = self.context.get('request').user.profile

        inst = ReportedProfiles.objects.create(
            reporter_profile=reporter,
            reported_profile=validated_data.get('reported_profile_global_id'),
            status=validated_data.get('status'))
        return self.data


class BlockProfileListSerializer(serializers.ModelSerializer):
    global_id = serializers.UUIDField(source='blocked_profile.global_id', allow_null=True)
    username = serializers.CharField(source='blocked_profile.user.username', allow_null=True)
    name = serializers.CharField(source='blocked_profile.name', allow_null=True)
    profile_photo = serializers.ImageField(source='blocked_profile.profile_photo', allow_null=True, use_url=True)

    class Meta:
        model = BlockedProfiles
        fields = ('global_id', 'username', 'name', 'profile_photo')


class BlockProfilesSerializer(serializers.ModelSerializer):
    blocked_profile_global_id = ProfileGlobalIdField()

    class Meta:
        model = BlockedProfiles
        fields = ('blocked_profile_global_id',)

    def validate(self, attrs):
        profile = self.context.get('request').user.profile
        try:
            BlockedProfiles.objects.get(
                profile=profile,
                blocked_profile=attrs.get('blocked_profile_global_id'))
            raise serializers.ValidationError(
                f"Duplicate block {attrs.get('blocked_profile_global_id')}")
        except BlockedProfiles.DoesNotExist:
            pass
        return super().validate(attrs)

    def create(self, validated_data):
        profile = self.context.get('request').user.profile

        inst = BlockedProfiles.objects.create(
            profile=profile,
            blocked_profile=validated_data.get('blocked_profile_global_id'))

        # Delete subscriptions
        subscriptions = validated_data.get('blocked_profile_global_id')
        profile.publishers_subscription.remove(subscriptions)
        
        return self.data
