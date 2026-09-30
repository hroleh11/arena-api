from django.utils.translation import gettext as _


SIGN_UP = {
    'EMAIL_IN_USE': _('This email is already in use. Please use different email or go to login page.'),
    'EMAIL_VERIFICATION': _('Invalid code. Please check your code and try again.'),
}

PASSWORD = {
    'LOWER_CASE': _('Password must contain at least 1 upper case.'),
    'UPPER_CASE': _('Password must contain at least 1 lower letter.'),
    'NUMBER': _('Password must contain at least 1 number.'),
    'LETTER': _('Password must contain at least 1 letter.'),
    'SPECIAL_CHARACTER': _('Password must contain at least 1 special character.'),
    'MIN_LENGTH': _('It must contain at least %(min_length)d characters.'),
    'BLANK': _('This field may not be blank.')  # TODO system doesn't see it
}

FORGOT_PASSWORD = {
    'CODE_USER': _('User not found.'),

    'CODE_BLANK': _('This field may not be blank.'),
    'CODE_MAX': _('Ensure this field has no more than 6 characters.'),
    'CODE_TRIES': _('Code is wrong. You have tries - 3/%(tries)d'),
    'CODE_EXPIRED': _('Code is expired!'),

    'CONFIRM-PASSWORD_BLANK': _('This field may not be blank.'),
    'CONFIRM-PASSWORD_MATCH': _('The two password fields didn\'t match.'),
    'CONFIRM-PASSWORD_EQUAL_WITH_OLD': _('The password must not be the same as the old one.'),
}

EDIT_PROFILE = {
    'PROFILE': _('Something went wrong, please check your data and try again.'),
}
