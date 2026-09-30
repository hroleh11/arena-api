from templated_mail.mail import BaseEmailMessage

from api.models import ResetCode


class PasswordResetEmail(BaseEmailMessage):
    template_name = "password_reset.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")
        obj, created = ResetCode.objects.update_or_create(user=user)
        if not created:
            obj.code = obj.generate_code()
            obj.tries = 3
            obj.save()
        context["code"] = obj.code
        return context


class PasswordChangedConfirmationEmail(BaseEmailMessage):
    template_name = "password_changed_confirmation.html"


class ActivateAccountEmail(BaseEmailMessage):
    template_name = 'activate_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        draft_user = context.get("draft_user")

        if not draft_user.is_active:
            draft_user.code = draft_user.generate_code()
            draft_user.tries = 3
            draft_user.save()

        context["code"] = draft_user.code
        context["deep_link"] = 'https://app.vylo.com/5AUZ'
        return context


class ActivateBetaAccountEmail(BaseEmailMessage):
    template_name = 'activate_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        beta_user = context.get("beta_user")
        active_code = beta_user.active_code
        if not beta_user.is_active:
            active_code.code = active_code.generate_code()
            active_code.tries = 3
            active_code.save()

        context["code"] = active_code.code
        return context


class CreatorInviteEmail(BaseEmailMessage):
    template_name = "creator_invite.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["password"] = context.get("password")
        return context
