from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# Create your views here.
def home(request):
    return render(request, "home.html")

def is_teacher(user):
    return user.groups.filter(name="Teacher").exists()

def is_admin(user):
    return user.is_staff

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "accounts/login.html", {
                "error": "Nom ou mot de passe incorrect"
            })

    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    else:
        return redirect("teacher_dashboard")


def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect("dashboard")

    return render(request, "accounts/teacher_dashboard.html")

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect("dashboard")

    return render(request, "accounts/admin_dashboard.html")
