from django.contrib import admin

from .models import MonthlyGrade


@admin.register(MonthlyGrade)
class MonthlyGradeAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "class_name",
        "subject_name",
        "year",
        "month_index",
        "month_label",
        "score",
        "created_at",
    )
    list_filter = ("year", "class_name", "subject_name")
    search_fields = ("student_name", "class_name", "subject_name")
    ordering = ("-year", "student_name")

