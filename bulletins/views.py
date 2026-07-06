from decimal import Decimal

from django.db.models import Avg
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import MonthlyGrade
from classes.models import Classe


def bulletins_home(request: HttpRequest):
    """Page d'accueil des bulletins avec recherche."""
    # Si des paramètres de recherche sont fournis, rediriger vers la vue bulletin_eleve
    student_name = request.GET.get("student_name")
    class_name = request.GET.get("class_name")
    year = request.GET.get("year")
    
    if student_name and class_name and year:
        return redirect("bulletin_eleve", student_name=student_name, class_name=class_name, year=year)
    
    # Récupérer les années et classes disponibles pour les filtres
    years = MonthlyGrade.objects.values_list('year', flat=True).distinct().order_by('-year')
    classes = MonthlyGrade.objects.values_list('class_name', flat=True).distinct().order_by('class_name')
    
    context = {
        "years": years,
        "classes": classes,
        "classes_list": Classe.objects.all().order_by('-niveau'),
    }
    return render(request, "bulletins/bulletins_home.html", context)


def monthly_grades_list(request: HttpRequest):
    """Liste des notes mensuelles (filtrage simple)."""
    month_labels = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    selected_months = request.GET.getlist("months")

    qs = MonthlyGrade.objects.all().order_by("year", "month_index")

    if selected_months:
        qs = qs.filter(month_index__in=selected_months)

    context = {
        "grades": qs,
        "filters": {
            "months": selected_months,
        },
        "month_labels": month_labels,
    }
    return render(request, "bulletins/monthly_grades_list.html", context)


def bulletin_eleve(request: HttpRequest, student_name: str, class_name: str, year: int):
    """Affiche le bulletin complet d’un élève pour une année scolaire."""
    # Récupérer toutes les notes de l'élève pour l'année
    grades = MonthlyGrade.objects.filter(
        student_name=student_name,
        class_name=class_name,
        year=year,
    ).order_by("subject_name", "month_index")

    # Organiser les notes par matière
    subjects = {}
    for grade in grades:
        if grade.subject_name not in subjects:
            subjects[grade.subject_name] = {
                "name": grade.subject_name,
                "months": {i: None for i in range(9)},  # Oct -> Jun
            }
        subjects[grade.subject_name]["months"][grade.month_index] = grade.score

    # Calculer la moyenne annuelle par matière
    for subject_name, data in subjects.items():
        scores = [s for s in data["months"].values() if s is not None]
        if scores:
            data["average"] = sum(scores) / len(scores)
        else:
            data["average"] = None

    # Calculer la moyenne générale
    all_averages = [data["average"] for data in subjects.values() if data["average"] is not None]
    general_average = sum(all_averages) / len(all_averages) if all_averages else None

    context = {
        "student_name": student_name,
        "class_name": class_name,
        "year": year,
        "subjects": subjects,
        "general_average": general_average,
        "month_labels": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    }
    return render(request, "bulletin_eleve.html", context)


def student_year_average(request: HttpRequest, year: int, student_name: str, class_name: str, subject_name: str):
    """Calcule la moyenne de l’année scolaire (Oct -> Jun).

    Règle: moyenne sur les mois pour lesquels score n’est pas NULL.
    """
    qs = MonthlyGrade.objects.filter(
        year=year,
        student_name=student_name,
        class_name=class_name,
        subject_name=subject_name,
        month_index__gte=0,
        month_index__lte=8,
        score__isnull=False,
    )

    avg = qs.aggregate(v=Avg("score")).get("v")
    if avg is None:
        avg = Decimal("0.00")

    return JsonResponse(
        {
            "year": year,
            "student": student_name,
            "class": class_name,
            "subject": subject_name,
            "average": str(avg),
            "months_count": qs.count(),
        }
    )

