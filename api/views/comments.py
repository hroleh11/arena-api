from django.shortcuts import get_object_or_404
from rest_framework import generics

from api.serializers import CommentsSerializer, CommentsSerializerUpdate


class CommentsCreate(generics.CreateAPIView):
    serializer_class = CommentsSerializer

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class CommentsUpdate(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentsSerializerUpdate
    lookup_field = "global_id"

    def get_object(self):
        global_id = self.kwargs.get(self.lookup_field)
        return get_object_or_404(self.request.user.profile.comments, global_id=global_id)