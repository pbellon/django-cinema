from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
from django.db.models import CharField, Value
from django.db.models.functions import Concat, Coalesce, Lower
from django.utils.html import format_html


from cinema.models import (
    Spectator,
    Author,
    Movie,
    User,
    SpectatorAuthorEvaluation,
    SpectatorMovieEvaluation,
    SpectatorFavoriteMovie,
    SpectatorFavoriteAuthor,
)

# Unregister default models
admin.site.unregister(Group)
admin.site.unregister(Site)


class SpectatorFavoriteMoviesInline(admin.TabularInline):
    model = SpectatorFavoriteMovie
    extra = 1
    show_change_link = True
    raw_id_fields = ["spectator"]


class SpectatorFavoriteAuthorsInline(admin.TabularInline):
    model = SpectatorFavoriteAuthor
    extra = 1
    show_change_link = True
    raw_id_fields = ["spectator"]


class FullNameColumnMixin:
    """
    Adds a sortable 'Full name' column for models with first_name/last_name.
    - Renders 'First Last'
    - Sorts by a DB annotation 'full_name_sort' (case-insensitive, last then first)
    """

    full_name_sort_field = "full_name_sort"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Case-insensitive sort by last_name then first_name via a single annotation
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
        # Display keeps original casing; sorting uses the lowercase annotation above
        return (f"{first} {last}").strip()


@admin.register(Spectator)
class SpectatorAdmin(FullNameColumnMixin, admin.ModelAdmin):
    list_display = ("full_name_admin", "email")
    exclude = (
        "full_name",
        "groups",
        "user_permissions",
    )
    inlines = [
        SpectatorFavoriteAuthorsInline,
        SpectatorFavoriteMoviesInline,
    ]


@admin.display(description="IMDB page")
def imdb_page_admin(obj):
    link = obj.imdb_page
    if len(link) > 0:
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
        imdb_page_admin,
    )

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
    list_display = ("title", "release_date", imdb_page_admin)
    list_filter = ["release_date", "evaluation", "status"]
    inlines = [MovieEvaluationsInline]


@admin.register(SpectatorFavoriteAuthor)
class FavoriteAuthorAdmin(admin.ModelAdmin):
    list_display = ["spectator_full_name", "author_full_name"]

    @admin.display(description="Spectator")
    def spectator_full_name(self, obj):
        return obj.spectator.full_name

    @admin.display(description="Author")
    def author_full_name(self, obj):
        return obj.author.full_name


@admin.register(SpectatorFavoriteMovie)
class FavoriteMovieAdmin(admin.ModelAdmin):
    list_display = ["spectator_full_name", "movie_title"]

    @admin.display(description="Spectator")
    def spectator_full_name(self, obj):
        return obj.spectator.full_name

    @admin.display(description="Movie")
    def movie_title(self, obj):
        return obj.movie.title


@admin.register(SpectatorMovieEvaluation)
class MovieEvaluationAdmin(admin.ModelAdmin):
    pass


@admin.register(SpectatorAuthorEvaluation)
class AuthorEvaluationAdmin(admin.ModelAdmin):
    pass
