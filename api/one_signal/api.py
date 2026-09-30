from abc import ABC

import requests
from django.conf import settings


class OneSignal(ABC):
    _instance = None

    HOST = 'https://api.onesignal.com'
    APP_ID = settings.ONESIGNAL_APP_ID
    APP_KEY = settings.ONESIGNAL_APP_KEY
    USER_KEY = REST_API_KEY = settings.ONESIGNAL_USER_KEY

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(OneSignal, cls).__new__(cls)
        return cls._instance


class UserAPI(OneSignal):
    def __init__(self):
        self.url = f'{self.HOST}/apps/{self.APP_ID}/users'
        self.headers = {'Authorization': f'Bearer {self.APP_KEY}'}

    def get_user(self, unique_key):
        response = requests.get(f'{self.url}/by/external_id/{unique_key}', headers=self.headers, allow_redirects=False)
        return response.status_code, response.json()

    def create_user(self, identity: dict, properties: dict):
        response = requests.post(self.url, headers=self.headers, json={
            "identity": identity,
            "properties": properties
        })
        return response.status_code, response.json()

    def update_user(self, unique_key, properties: dict):
        response = requests.patch(f'{self.url}/by/external_id/{unique_key}', headers=self.headers, json={
            "properties": properties
        })
        return response.status_code, response.json()

    def update_aliases(self, unique_key, aliases: dict):
        response = requests.patch(f'{self.url}/by/external_id/{unique_key}/identity', headers=self.headers, json={
            "identity": aliases
        })
        return response.status_code, response.json()

    def delete_user(self, unique_key):
        response = requests.delete(f'{self.url}/by/external_id/{unique_key}', headers=self.headers)
        return response.status_code, response.json()

    def create_subscription(self, unique_key, sub_type, token, enabled=True):
        response = requests.post(f'{self.url}/by/external_id/{unique_key}/subscriptions', headers=self.headers, json={
            "subscription": {
                "type": sub_type,
                "enabled": enabled,
                "token": token
            }
        })
        return response.status_code, {}


class SubscriptionsAPI(OneSignal):
    def __init__(self):
        self.url = f'{self.HOST}/apps/{self.APP_ID}/subscriptions'
        self.headers = {'Authorization': f'Bearer {self.APP_KEY}'}

    def update_subscription(self, subscription_id, token, enabled=True):
        response = requests.patch(f'{self.url}/{subscription_id}', headers=self.headers, json={
            "subscription": {
                "token": token,
                "enabled": enabled
            }
        })
        return response.status_code, response.json()

    def transfer_subscription(self, subscription_id, external_id):
        response = requests.patch(f'{self.url}/{subscription_id}/owner', headers=self.headers, json={
            "identity": {
                "external_id": external_id
            }
        })
        return response.status_code, response.json()


class SegmentAPI(OneSignal):
    def __init__(self):
        self.url = f'{self.HOST}/apps/{self.APP_ID}/segments'
        self.headers = {'Authorization': f'Basic {self.APP_KEY}'}

    def get_segments(self):
        response = requests.get(self.url, headers=self.headers)
        return response.status_code, response.json()

    def create_segment(self, name: str, filters: list):
        response = requests.post(self.url, headers=self.headers, json={
            "name": name,
            "filters": filters
        })
        return response.status_code, response.json()

    def delete_segment(self, segment_id: str):
        response = requests.delete(f'{self.url}/{segment_id}', headers=self.headers)
        return response.status_code, response.json()