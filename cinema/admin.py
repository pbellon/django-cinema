from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group

from cinema.models import (
    Spectator,
    Author,
    Movie,
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


@admin.register(Spectator)
class SpectatorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email")
    exclude = ("full_name",)
    inlines = [
        SpectatorFavoriteAuthorsInline,
        SpectatorFavoriteMoviesInline,
    ]


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
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "imdb_page",
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
    list_display = ("title", "release_date", "imdb_page")
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
