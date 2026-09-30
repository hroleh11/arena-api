import re

from django.core.exceptions import ValidationError

from api.errors import PASSWORD


class MinimumLengthValidator:
    def __init__(self, min_length=6):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                PASSWORD['MIN_LENGTH'] % {'min_length': self.min_length},
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return PASSWORD['MIN_LENGTH'] % {'min_length': self.min_length}


class BlankValidator:

    def validate(self, password, user=None):
        if password == '':
            raise ValidationError(
                PASSWORD['BLANK'],
                code='password_blank',
            )

    def get_help_text(self):
        return PASSWORD['BLANK']


class RegExpPasswordValidator:

    def __init__(self):
        self.reg_pattern = r'[A-Za-z\d\!\@\#\$\%\^\&\*\(\)\-\_\+\=\{\}\[\]\|\\\/\:\;\"\<\>\,\.\?]+'


class LetterValidator:
    def validate(self, password, user=None):
        if not any(char.isalpha() for char in password):
            raise ValidationError(
                PASSWORD['LETTER'],
                code='password_no_letter',
            )

    def get_help_text(self):
        return PASSWORD['LETTER']


class SpecSymbolPasswordValidator(RegExpPasswordValidator):
    """
    Validate whether the password is spec symbol.
    """
    def validate(self, password, user=None):
        reg_pattern = r'^(?=.*[\!\@\#\$\%\^\&\*\(\)\-\_\+\=\{\}\[\]\|\\\/\:\;\"\<\>\,\.\?])' + self.reg_pattern + r'$'
        if not re.search(reg_pattern, password):
            raise ValidationError(
                PASSWORD['SPECIAL_CHARACTER'],
                code='password_spec_symbol',
            )

    def get_help_text(self):
        return PASSWORD['SPECIAL_CHARACTER']


class NumberPasswordValidator(RegExpPasswordValidator):
    """
    Validate whether the password is number symbol.
    """
    def validate(self, password, user=None):
        reg_pattern = r'^(?=.*\d)' + self.reg_pattern + r'$'
        if not re.search(reg_pattern, password):
            raise ValidationError(
                PASSWORD['NUMBER'],
                code='password_number_symbol',
            )

    def get_help_text(self):
        return PASSWORD['NUMBER']


class UpperPasswordValidator(RegExpPasswordValidator):
    """
    Validate whether the password is upper symbol.
    """
    def validate(self, password, user=None):
        reg_pattern = r'^(?=.*[A-Z])' + self.reg_pattern + r'$'
        if not re.search(reg_pattern, password):
            raise ValidationError(
                PASSWORD['UPPER_CASE'],
                code='password_upper_letter',
            )

    def get_help_text(self):
        return PASSWORD['UPPER_CASE']


class LowerPasswordValidator(RegExpPasswordValidator):
    """
    Validate whether the password is lower symbol.
    """
    def validate(self, password, user=None):
        reg_pattern = r'^(?=.*[a-z])' + self.reg_pattern + r'$'
        if not re.search(reg_pattern, password):
            raise ValidationError(
                PASSWORD['LOWER_CASE'],
                code='password_lower_letter',
            )

    def get_help_text(self):
        return PASSWORD['LOWER_CASE']
