from django.contrib import admin

from .models import Presence


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("student", "classe", "date", "present", "parent_notifie", "enseignant")
    list_filter = ("present", "parent_notifie", "classe", "date")
