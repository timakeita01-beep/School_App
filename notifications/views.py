from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from classes.models import Classe
from eleves.models import Parent

from .models import Notification


@login_required
def composer(request):
    if not request.user.is_staff:
        messages.error(request, "Seul l'administrateur peut envoyer des notifications.")
        return redirect("accounts:dashboard")

    classes = Classe.objects.all().order_by("-niveau", "nom")

    parent_id = request.GET.get("parent") or request.POST.get("parent")
    parent_selectionne = Parent.objects.filter(pk=parent_id).first() if parent_id else None

    if request.method == "POST":
        message = request.POST.get("message", "").strip()

        if not message:
            messages.error(request, "Le message ne peut pas être vide.")
            return redirect(request.get_full_path())

        toutes = request.POST.get("toutes_les_classes") == "on"
        classe_ids = request.POST.getlist("classes")
        classes_ciblees = Classe.objects.none()

        if parent_selectionne:
            parents = Parent.objects.filter(pk=parent_selectionne.pk)
        else:
            if toutes:
                classes_ciblees = Classe.objects.all()
            elif classe_ids:
                classes_ciblees = Classe.objects.filter(pk__in=classe_ids)
            else:
                messages.error(
                    request,
                    "Sélectionnez au moins une classe, ou « toutes les classes ».",
                )
                return redirect("notifications:composer")

            parents = Parent.objects.filter(
                students__classroom__in=classes_ciblees
            ).distinct()

        envoyes = 0
        sans_email = 0

        for parent in parents:
            if not parent.email:
                sans_email += 1
                continue

            send_mail(
                subject="Message de l'établissement",
                message=f"Bonjour {parent.first_name},\n\n{message}\n",
                from_email=None,
                recipient_list=[parent.email],
                fail_silently=True,
            )
            envoyes += 1

        notif = Notification.objects.create(
            message=message,
            toutes_les_classes=toutes if not parent_selectionne else False,
            parent=parent_selectionne,
            envoye_par=request.user,
            nb_destinataires=envoyes,
        )

        if not parent_selectionne and not toutes:
            notif.classes.set(classes_ciblees)

        if envoyes:
            messages.success(request, f"Message envoyé à {envoyes} parent(s).")
        if sans_email:
            messages.warning(
                request,
                f"{sans_email} parent(s) n'ont pas pu être notifiés (aucun e-mail renseigné).",
            )
        if not envoyes and not sans_email:
            messages.info(request, "Aucun parent trouvé pour cette sélection.")

        return redirect("notifications:composer")

    historique = Notification.objects.select_related(
        "parent", "envoye_par"
    ).prefetch_related("classes")[:15]

    context = {
        "classes": classes,
        "parent_selectionne": parent_selectionne,
        "historique": historique,
    }

    return render(request, "notifications/composer.html", context)
