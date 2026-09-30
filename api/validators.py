import re

from django.contrib.auth import get_user_model
from rest_framework.serializers import ValidationError

from api.models import WhitelistedUsernames

User = get_user_model()


def validate_username(username, instance=None):
    objs = User.objects.filter(username__iexact=username)

    if hasattr(instance, 'pk'):
        objs = objs.exclude(pk=instance.pk)

    if objs:
        raise ValidationError('This username has been taken. Please choose another.')

    whitelisted_users = WhitelistedUsernames.objects.filter(username=username)
    if whitelisted_users:
        raise ValidationError('This username is in the whitelist')

    if not (24 >= len(username) >= 3):
        raise ValidationError('Username must be between 3-24 characters')
    if not re.search(r'^[a-z\d_.]+$', username):
        raise ValidationError(
            'Username can contain alphanumeric characters and underscores ( _ ) and periods ( . )'
        )
    if not re.search(r'^(?!\w*(?:vylo|admin))[A-Za-z\d_.]+$', username, flags=re.I):
        raise ValidationError(
            'Username can not contain vylo or admin words'
        )

    return username


def validate_email(email, instance=None):
    objs = User.objects.filter(email__iexact=email)
    if hasattr(instance, 'pk'):
        objs = objs.exclude(pk=instance.pk)

    if objs:
        raise ValidationError('User with this email already exists.')

    return email


def validate_name(name):
    if re.search(r'[0-9]+', name):
        raise ValidationError('Name can not contain numbers')
    if name == '':
        raise ValidationError('Name can not be blank')
    return name
