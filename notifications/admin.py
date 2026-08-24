from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("date_envoi", "envoye_par", "toutes_les_classes", "parent", "nb_destinataires")
    list_filter = ("toutes_les_classes",)
    readonly_fields = ("date_envoi",)
