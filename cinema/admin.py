from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import CharField, Value
from django.db.models.functions import Coalesce, Concat, Lower
from django.utils.html import format_html

from cinema.models import (
    Author,
    Movie,
    Spectator,
    SpectatorAuthorEvaluation,
    SpectatorMovieEvaluation,
)

# Unregister default models
admin.site.unregister(Group)
admin.site.unregister(Site)


class FullNameColumnMixin:
    """
    Adds a sortable 'Full name' column for models with first_name/last_name.
    """

    full_name_sort_field = "full_name_sort"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            full_name_sort=Concat(
                Lower(Coalesce("last_name", Value(""))),
                Value(" "),
                Lower(Coalesce("first_name", Value(""))),
                output_field=CharField(),
            )
        )

    @admin.display(description="Full name", ordering="full_name_sort")
    def full_name_admin(self, obj):
        first = obj.first_name or ""
        last = obj.last_name or ""
        return (f"{first} {last}").strip()


@admin.register(Spectator)
class SpectatorAdmin(FullNameColumnMixin, admin.ModelAdmin):
    list_display = ("full_name_admin", "email")
    exclude = (
        "full_name",
        "groups",
        "user_permissions",
    )


@admin.display(description="IMDB page")
def imdb_page_admin(obj):
    link = obj.imdb_page
    if link:
        return format_html(f'<a href="{link}" target="_blank">{link}</a>')
    return "-"


class AuthorsMoviesFilter(admin.SimpleListFilter):
    title = "Movies associated"
    parameter_name = "with_movies"

    def lookups(self, _request, _model_admin):
        return [
            ("yes", "At least one associated movie"),
            ("no", "Without any associated movie"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(movies__isnull=False)

        if self.value() == "no":
            return queryset.filter(movies__isnull=True)


class AuthorMoviesInline(admin.TabularInline):
    model = Author.movies.through
    extra = 1
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(FullNameColumnMixin, admin.ModelAdmin):
    list_display = (
        "full_name_admin",
        "creation_source",
        imdb_page_admin,
    )
    readonly_fields = ("creation_source",)

    list_filter = [AuthorsMoviesFilter]

    exclude = (
        "last_login",
        "permission",
        "is_active",
        "last_tmdb_populated",
        "full_name",
        "groups",
        "user_permissions",
    )
    inlines = [AuthorMoviesInline]


class MovieEvaluationsInline(admin.TabularInline):
    model = SpectatorMovieEvaluation
    extra = 1
    show_change_link = True
    raw_id_fields = ["movie"]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", imdb_page_admin, "creation_source")
    list_filter = ["release_date", "evaluation", "status"]
    readonly_fields = ("creation_source",)
    inlines = [MovieEvaluationsInline]


@admin.register(SpectatorMovieEvaluation)
class MovieEvaluationAdmin(admin.ModelAdmin):
    pass


@admin.register(SpectatorAuthorEvaluation)
class AuthorEvaluationAdmin(admin.ModelAdmin):
    pass
