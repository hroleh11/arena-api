from django.contrib.auth import get_user_model
from social_core.pipeline.partial import partial

User = get_user_model()


@partial
def get_profile_data_and_username(strategy, details, user=None, is_new=False, *args, **kwargs):
    if is_new and not kwargs.get('end_partial', False):
        partial_token = kwargs.get('current_partial').token

        response_redirect = strategy.redirect('/auth/social/{}/{}'.format(
            kwargs.get('backend').name, partial_token)
        )
        response_redirect.partial_token = partial_token
        response_redirect.is_new = is_new
        return response_redirect


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}
    user_fields = {name: kwargs.get(name, details.get(name))
                   for name in ['email', 'username']}
    profile_fields = {name: kwargs.get(name, details.get(name))
                      for name in ['name', 'gender', 'birthday_date', 'signup_code']}
    if not user_fields:
        return

    user = User(**user_fields)
    if 'password' in kwargs:
        user.set_password(kwargs.get('password'))
    user._profile = profile_fields or {}
    user.save()

    return {
        'is_new': True,
        'user': user
    }
