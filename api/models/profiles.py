import random
import re
import secrets
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection

from api.shortcust import generate_deep_link


class Profile(models.Model):
    @staticmethod
    def user_profile_image_name(instance, filename):
        ext = filename.split('.')[-1]
        old_file_name = instance.profile_photo.name.split('/')[-1]
        cnt = re.search('_(.*)\.', old_file_name)

        print(cnt, old_file_name)
        if cnt is None:
            cnt = 1
        else:
            try:
                cnt = int(cnt.group(1)) + 1
            except ValueError:
                cnt = 1
        return f'user_profile_images/profile{instance.global_id}_{cnt:04d}.{ext}'

    class Gender(models.TextChoices):
        MALE = 'male'
        FEMALE = 'female'
        OTHER = 'other'

    # class Type(models.IntegerChoices):
    #     PUBLISHER = 1, 'Publisher'
    #     USER = 2, 'User'

    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    # type = models.IntegerField(choices=Type.choices)

    # TODO in case parent_link=True we can easily manage user and profile
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    profile_photo = models.ImageField(
        upload_to=user_profile_image_name.__func__,
        default=None, null=True)
    profile_photo_svg = models.FileField(
        upload_to=user_profile_image_name.__func__,
        default=None, null=True)
    name = models.CharField(max_length=100, default='', blank=True)
    website = models.URLField(default='', blank=True)
    bio = models.CharField(max_length=200, default='', blank=True)
    phone = models.CharField(max_length=13, default='', blank=True)
    gender = models.CharField(max_length=6, default=Gender.OTHER, choices=Gender.choices)
    is_approved = models.BooleanField(default=False)
    account_rate = models.FloatField(default=0)
    is_source = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)
    is_remember_me = models.BooleanField(default=False)
    is_email_subscribed = models.BooleanField(default=True)
    birthday_date = models.DateField(blank=True, null=True, default=None)
    personal_link = models.URLField(null=True)
    timezone = models.CharField(max_length=32, default=settings.TIME_ZONE, blank=True)

    signup_code = models.CharField(max_length=32, default=None, null=True)

    updated_at = models.DateTimeField(auto_now=True, null=True)

    categories_subscription = models.ManyToManyField(
        "Categories", related_name='cat_subscribers')
    publishers_subscription = models.ManyToManyField(
        'self', related_name='prof_subscribers', symmetrical=False)
    have_access_to_vylo_props = models.BooleanField(default=False)
    dfs_pre_auth_completed = models.BooleanField(default=False)
    creator_cash = models.BooleanField(default=False)
    def __str__(self):
        return f'Profile {self.id} User {self.username}'

    @property
    def username(self):
        return self.user.username if self.user is not None else ''

    @property
    def profile_photo_url(self):
        return f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{self.profile_photo}'

    @property
    def profile_photo_big_thumb(self):
        image = self.profile_photo
        if image:
            return image.url + '.big.thumb'

    @property
    def profile_photo_small_thumb(self):
        image = self.profile_photo
        if image:
            return image.url + '.small.thumb'

    def regenerate_link(self):
        web_link = 'https://{}/profile/{}'.format(settings.EXTERNAL_IDS_DOMAIN, self.username)
        personal_link, code = generate_deep_link(web_link, pid=self.global_id)
        if code == 200:
            self.personal_link = personal_link
            self.save()

    @classmethod
    def generate_password(cls):
        # Define character sets for different types of characters
        # special_characters = '~`!@#$%^&*()-_+={}[]|\/:;"<>,.?\''
        digits = string.digits
        lowercase_letters = string.ascii_lowercase
        uppercase_letters = string.ascii_uppercase

        # Ensure at least one character from each category
        password = (
                # secrets.choice(special_characters) +
                secrets.choice(digits) +
                secrets.choice(lowercase_letters) +
                secrets.choice(uppercase_letters)
        )

        # Generate the remaining characters randomly
        # remaining_length = secrets.randbelow(5) + 4  # Ensure a total length between 8 and 12
        remaining_length = 5  # Fixed length of 8 characters (3 characters already chosen)
        all_characters = digits + lowercase_letters + uppercase_letters

        password += ''.join(secrets.choice(all_characters) for _ in range(remaining_length))

        # Shuffle the password to make it more secure
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        password = ''.join(password_list)

        return password

    def category_subscriptions(self):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT 
                    LOWER(ac.name) AS category,
                    MAX(CASE WHEN apcs.profile_id IS NOT NULL THEN 1 ELSE 0 END) AS subscribed
                FROM 
                    api_categories AS ac
                LEFT JOIN 
                    api_profile_categories_subscription AS apcs 
                    ON ac.id = apcs.categories_id AND apcs.profile_id = {self.id}
                GROUP BY
                    LOWER(ac.name)
                """
            )
            return dict(cursor.fetchall())


class WhitelistedUsernames(models.Model):
    username = models.CharField(max_length=15, default='')

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.username


class DraftProfile(models.Model):

    @staticmethod
    def generate_code():
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

    email = models.EmailField(unique=True)
    code = models.CharField(
        max_length=8, default=generate_code.__func__, blank=True)
    tries = models.IntegerField(default=3, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.email} -> {self.tries}'


class ResetCode(models.Model):
    @staticmethod
    def generate_code():
        return random.random().__str__().split('.')[1][:6]


    user = models.OneToOneField(
        User,
        related_name='reset_code',
        on_delete=models.CASCADE
    )
    code = models.CharField(max_length=6, default=generate_code.__func__)
    tries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Code {self.code} for user {self.user.username}'


class ReportedProfiles(models.Model):
    class Statuses(models.IntegerChoices):
        OFFTOPIC = 1, 'This is off topic'
        INTELLECTUAL = 2, 'This infringes on intellectual property rights'
        HATE = 3, 'Hate speech or symbols'
        SEXUAL = 4, 'Nudity or sexual activity'
        SPAM = 5, 'This is spam or fraud'
        SOMETHINGELSE = 6, 'Something else'

    reporter_profile = models.ForeignKey(
        Profile,
        related_name='i_report_users',
        on_delete=models.SET_NULL,
        null=True)
    reported_profile = models.ForeignKey(
        Profile,
        related_name='users_reported_me',
        on_delete=models.SET_NULL,
        null=True)
    status = models.IntegerField(choices=Statuses.choices)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('reporter_profile', 'reported_profile',)

    def __str__(self):
        return f'User {self.reporter_profile.global_id} reported  {self.reported_profile.global_id}'


class BlockedProfiles(models.Model):
    profile = models.ForeignKey(
        Profile,
        related_name='i_block_users',
        on_delete=models.SET_NULL,
        null=True)
    blocked_profile = models.ForeignKey(
        Profile,
        related_name='users_block_me',
        on_delete=models.SET_NULL,
        null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('profile', 'blocked_profile',)

    def __str__(self):
        return f'User {self.profile.global_id} block {self.blocked_profile.global_id}'


class BetaUsers(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male'
        FEMALE = 'female'
        OTHER = 'other'

    name = models.CharField(max_length=50, default='', blank=True, null=True)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=6,
                              default=Gender.OTHER,
                              choices=Gender.choices,
                              blank=True, null=True)
    birthday_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name.__str__()


class BetaRefCode(models.Model):
    @staticmethod
    def generate_code():
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

    code = models.CharField(max_length=8)
    tries = models.IntegerField(default=3)
    beta_user = models.OneToOneField(
        BetaUsers, related_name='active_code', on_delete=models.SET_NULL, null=True)
    ref_users = models.ManyToManyField(
        DraftProfile, related_name='ref_code', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.beta_user.is_active:
            return f'{self.beta_user} -> ref users {self.ref_users.count()}'
        return f'{self.beta_user} -> tries {self.tries}'


class AutoFollow(models.Model):
    global_id = models.UUIDField(default=uuid.uuid4)
    sort_order = models.IntegerField(default=0)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    description = models.TextField(default='', blank=True)

    def follow_by_everyone(self):
        profiles = Profile.objects.filter(is_source=False).exclude(id=self.profile.id)

        for profile in profiles:
            profile.publishers_subscription.add(self.profile)


class CreatorSocialAssociation(models.Model):
    class SocialNetworks(models.TextChoices):
        INSTAGRAM = 'instagram'
        TIKTOK = 'tiktok'
        YOUTUBE = 'youtube'

    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    is_submitted = models.BooleanField(default=False)
    provider = models.CharField(max_length=9, choices=SocialNetworks.choices)
    username = models.CharField(max_length=255)
    profile = models.ForeignKey(Profile, related_name='creator_socials', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('provider', 'profile',)

    @property
    def profile_link(self):
        domain = {
            'instagram': 'https://www.instagram.com/',
            'tiktok': 'https://www.tiktok.com/@',
            'youtube': 'https://www.youtube.com/channel/',
        }
        return f'{domain[self.provider]}{self.username}'

    def link_identifier(self, profile_link):
        if not profile_link:
            return None

        clean_url = profile_link.rstrip('/')
        username = None

        if self.provider == self.SocialNetworks.INSTAGRAM:
            username = clean_url.split('/')[-1]
        elif self.provider == self.SocialNetworks.TIKTOK:
            username = clean_url.split('@')[-1]
        elif self.provider == self.SocialNetworks.YOUTUBE:
            username = clean_url.split('/')[-1]

        return username


__all__ = [
    'Profile', 'WhitelistedUsernames', 'DraftProfile', 'ResetCode', 'ReportedProfiles',
    'BlockedProfiles', 'BetaUsers', 'BetaRefCode', 'AutoFollow', 'CreatorSocialAssociation'
]