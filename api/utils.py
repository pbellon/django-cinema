from django.core.exceptions import PermissionDenied

from cinema.models import Spectator


def get_spectator_from_request(request):
    try:
        return request.user.spectator
    except Spectator.DoesNotExist:
        raise PermissionDenied("You must be a spectator to perform this query")
