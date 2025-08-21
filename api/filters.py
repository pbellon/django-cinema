from cinema.models import CreationSource
from rest_framework.exceptions import ValidationError


class CreationSourceFilterMixin:
    """
    Adds ?created_source=TMDB or ?created_source=ADMIN,TMDB filtering.
    Replace 'created_source' with your actual field name if different.
    """

    def filter_by_created_source(self, qs):
        param = self.request.query_params.get("creation_source")
        if not param:
            return qs

        param = param.strip().upper()

        allowed = {code for code, _ in CreationSource.choices}
        if param not in allowed:
            raise ValidationError(
                {
                    "creation_source": f"Invalid value(s): {param}. Allowed: {sorted(allowed)}"
                }
            )

        return qs.filter(creation_source=param)
