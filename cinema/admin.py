from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
from typing import Union

from cinema.models import Spectator, Author, Movie, User

# Unregister default models
admin.site.unregister(Group)
admin.site.unregister(Site)


@admin.register(Spectator)
class SpectatorAdmin(admin.ModelAdmin):
    list_display = ("username", "password", "first_name", "last_name", "email", "biography")


@admin.display(description="Name")
def name(obj: User):
    return f"{obj.first_name} {obj.last_name}"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        name,
        "imdb_page",
    )

    exclude = (
        "last_login",
        "permission",
        "is_active",
        "last_tmdb_populated",
        "groups",
        "user_permissions",
    )

    @admin.display(empty_value="")
    def imdb_page(self, obj: Movie):
        if len(obj.imdb_id) > 0:
            return f"https://www.imdb.com/name/{obj.imdb_id}/"

        return ""


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("imdb_page", "title")

    @admin.display(empty_value="")
    def imdb_page(self, obj: Movie):
        if len(obj.imdb_id) > 0:
            return f"https://www.imdb.com/title/{obj.imdb_id}/"

        return ""


# Register your models here.
