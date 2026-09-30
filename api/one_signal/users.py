from api.one_signal.api import UserAPI, SubscriptionsAPI


class UserBuilder:
    def __init__(self):
        self.user_api = UserAPI()
        self.subscriptions_api = SubscriptionsAPI()

    def update_or_create(self, identity, properties):
        status_code, data = self.user_api.update_user(identity.get('external_id'), properties.get('tags', dict()))
        if status_code == 404:
            return self.user_api.create_user(identity, properties)

        return status_code, data

    def get_subscriptions(self, username):
        status_code, data = self.user_api.get_user(username)

        return data.get('subscriptions', list()) if status_code == 200 else list()

    def transfer_subscription(self, subscription_id, global_id):
        return self.subscriptions_api.transfer_subscription(subscription_id, global_id)
