from rest_framework import generics, response, status
from api.serializers.creators import CreatorSocialAssociationSerializer
from api.models import CreatorSocialAssociation

class ConnectedSocialsList(generics.ListCreateAPIView):
    serializer_class = CreatorSocialAssociationSerializer

    def list(self, request, *args, **kwargs):
        profile = self.request.user.profile
        creator_social = profile.creator_socials.first()  # <-- currently only one social can be connected

        socials = CreatorSocialAssociation.SocialNetworks.__members__

        connected_socials = []
        for key, value in socials.items():
            social_data = {
                'id': None,
                'provider': key.lower(),
                'username': None,
                'is_submitted': None
            }
            if creator_social is not None and value == creator_social.provider:
                social_data['id'] = creator_social.id
                social_data['username'] = creator_social.username
                social_data['is_submitted'] = creator_social.is_submitted
            connected_socials.append(social_data)

        return response.Response(connected_socials, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ConnectedSocialDestroy(generics.DestroyAPIView):
    lookup_field = 'id'

    def get_object(self):
        return self.request.user.profile.creator_socials.get(pk=self.kwargs['id'])
