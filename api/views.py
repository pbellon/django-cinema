from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from api.serializers import (
    RegisterSpectatorSerializer,
)


class RegisterSpectatorView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSpectatorSerializer
