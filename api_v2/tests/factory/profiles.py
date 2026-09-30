import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from api.models import Profile


from django.db.models.signals import post_save
from contextlib import contextmanager


@factory.django.mute_signals(post_save)
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'password123')


@factory.django.mute_signals(post_save)
class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    profile_photo = factory.django.ImageField(filename='test_profile.jpg')
    # email = factory.Faker('email')
    phone = factory.Faker('numerify', text='###########')
    gender = factory.Faker('random_element',
                           elements=[Profile.Gender.MALE, Profile.Gender.FEMALE, Profile.Gender.OTHER])
    birthday_date = factory.Faker('date_of_birth')
    signup_code = factory.Faker('bothify', text='????????????????????????????????')  # 32 символа
    have_access_to_vylo_props = factory.Faker('boolean')
    dfs_pre_auth_completed = factory.Faker('boolean')
    is_source = False


@factory.django.mute_signals(post_save)
class PublishersProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    profile_photo = None
    profile_photo_svg = factory.django.FileField(filename='profile_photo.svg')
    source_name = factory.Faker('company')
    is_source = True
