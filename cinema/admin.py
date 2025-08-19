from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group

from cinema.models import Spectator, Author, Movie

# Unregister default models
admin.site.unregister(Group)
admin.site.unregister(Site)


@admin.register(Spectator)
class SpectatorAdmin(admin.ModelAdmin):
    pass


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    pass


# Register your models here.
