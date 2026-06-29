from decimal import Decimal

from django.db.models import Avg
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import MonthlyGrade


def monthly_grades_list(request: HttpRequest):
    """Liste des notes mensuelles (filtrage simple)."""
    year = request.GET.get("year")
    student_name = request.GET.get("student")
    class_name = request.GET.get("class")
    subject_name = request.GET.get("subject")

    qs = MonthlyGrade.objects.all().order_by("year", "month_index")

    if year:
        qs = qs.filter(year=year)
    if student_name:
        qs = qs.filter(student_name__icontains=student_name)
    if class_name:
        qs = qs.filter(class_name__icontains=class_name)
    if subject_name:
        qs = qs.filter(subject_name__icontains=subject_name)

    context = {
        "grades": qs,
        "filters": {
            "year": year,
            "student": student_name,
            "class": class_name,
            "subject": subject_name,
        },
    }
    return render(request, "bulletins/monthly_grades_list.html", context)


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

