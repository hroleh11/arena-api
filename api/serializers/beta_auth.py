from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.models import BetaUsers, BetaRefCode, DraftProfile
from api.validators import validate_email

User = get_user_model()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class BetaUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    # code = serializers.CharField(source='active_code.code')
    # ref_code = serializers.CharField(required=False)
    # MAX_REF = 50

    class Meta:
        model = BetaUsers
        fields = ('name', 'email', 'gender', 'birthday_date',
                  'is_active', 'created_at',
                  # 'code', 'ref_code'
                  )
        read_only_fields = ('name', 'gender', 'birthday_date', 'is_active',
                            'created_at')

    def validate_email(self, email):
        return validate_email(email)

    # def is_beta_user(self):
    #     attrs = self.initial_data
    #     try:
    #         beta_user = BetaUsers.objects.get(email=attrs.get('email'))
    #     except BetaUsers.DoesNotExist:
    #         return False
    #
    #     try:
    #         BetaRefCode.objects.get(beta_user=beta_user, code=attrs.get('code'))
    #     except BetaRefCode.DoesNotExist:
    #         raise serializers.ValidationError({'email': ['It looks like code and email do not match. Please enter code from your “Welcome to Vylo” email letter!']})
    #
    #     beta_user.is_active = True
    #     beta_user.save()
    #
    #     return True

    # def is_beta_user(self) -> bool:
    #     email = self.validated_data.get('email')
    #     return BetaUsers.objects.filter(email__iexact=email).exists() and not User.objects.filter(email__iexact=email).exists()
    #
    # def is_ref_user(self) -> bool:
    #     validated_data = self.validated_data
    #
    #     try:
    #         ref_code = BetaRefCode.objects.get(code=validated_data.get('ref_code'))
    #     except BetaRefCode.DoesNotExist:
    #         return False
    #
    #     ref_users = ref_code.ref_users.filter(is_active=True).count()
    #     beta_user = ref_code.beta_user
    #
    #     is_user_exist = beta_user.is_active and User.objects.filter(email=validated_data.get('email')).exists()
    #     is_code_valid = ref_users < self.MAX_REF
    #     return bool(is_code_valid and not is_user_exist)
    #
    # def save_draft(self):
    #     instance, created = DraftProfile.objects.get_or_create(email=self.validated_data.get('email'))
    #
    #     if created:
    #         ref_code = BetaRefCode.objects.get(code=self.validated_data.get('ref_code'))
    #         ref_code.ref_users.add(instance)
    #     return instance
    #
    # def activate(self, code):
    #     email = self.validated_data.get('email')
    #     ref_code = self.validated_data.get('ref_code')
    #     if ref_code:
    #         draft = DraftProfile.objects.filter(email__iexact=email).first()
    #         return self.activate_draft(draft, code)
    #
    #     beta = BetaUsers.objects.filter(email__iexact=email).first()
    #     return self.activate_beta(beta, code)
    #
    # @staticmethod
    # def activate_draft(instance, code):
    #     if hasattr(instance, 'code'):
    #         if code == instance.code and instance.tries > 0:
    #             instance.is_active = True
    #             instance.save()
    #             return {
    #                 'name': '',
    #                 'gender': '',
    #                 'birthday_date': '',
    #             }
    #         elif code != instance.code and instance.tries > 0:
    #             instance.tries -= 1
    #             instance.save()
    #     # raise serializers.ValidationError('Account not activated!')

    @staticmethod
    def activate_beta(instance, code):
        if hasattr(instance, 'active_code'):
            active_code = instance.active_code
            if code == active_code.code and active_code.tries > 0:
                instance.is_active = True
                instance.save()
                return {
                    'name': instance.name or '',
                    'gender': instance.gender or '',
                    'birthday_date': instance.birthday_date or '',
                }
            elif code != active_code.code and active_code.tries > 0:
                active_code.tries -= 1
                active_code.save()
        # raise serializers.ValidationError('Account not activated!')
