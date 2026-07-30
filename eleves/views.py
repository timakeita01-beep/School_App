from django.shortcuts import render, redirect
from .models import Student, Parent
from classes.models import Classe
from django.contrib import messages
from .Form import ParentForm, StudentForm

# Create your views here.

def student_list(request):
    student_list = Student.objects.all()
    return render(request, 'student_list.html', {'student_list': student_list})

def student_detail(request, identification_number):
    student = Student.objects.get(identification_number=identification_number)
    return render(request, 'student_detail.html', {'student': student})

def student_update(request, identification_number):
    student = Student.objects.get(identification_number=identification_number)
    if request.method == 'POST':
        student.first_name = request.POST['first_name']
        student.last_name = request.POST['last_name']
        student.date_of_birth = request.POST['date_of_birth']
        student.lieu_de_naissance = request.POST['lieu_de_naissance']
        parent_id = request.POST['parent']
        classroom_id = request.POST['classroom']
        student.inscription_date = request.POST['inscription_date']

        student.parent = Parent.objects.get(id=parent_id)
        student.classroom = Classe.objects.get(id=classroom_id)

        student.save()
        return redirect('student_list')
    else:
        parents = Parent.objects.all()
        classrooms = Classe.objects.all()
        return render(request, 'student_update.html', {'student': student, 'parents': parents, 'classrooms': classrooms})

def student_delete(request, identification_number):
    student = Student.objects.get(identification_number=identification_number)
    student.delete()
    return redirect('student_list')

def parent_list(request):  
    parent_list = Parent.objects.all()
    return render(request, 'parent_list.html', {'parent_list': parent_list})

def parent_detail(request, parent_id):
    parent = Parent.objects.get(id=parent_id)
    return render(request, 'parent_detail.html', {'parent': parent})

def parent_update(request, parent_id):
    parent = Parent.objects.get(id=parent_id)
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            return redirect('parent_list')
    else:
        form = ParentForm(instance=parent)
    return render(request, 'parent_update.html', {'form': form})   

    
def parent_delete(request, parent_id):
    parent = Parent.objects.get(id=parent_id)
    parent.delete()
    return redirect('parent_list')

def student_create(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        date_of_birth = request.POST['date_of_birth']
        lieu_de_naissance = request.POST['lieu_de_naissance']
        parent_id = request.POST['parent']
        classroom_id = request.POST['classroom']
        inscription_date = request.POST['inscription_date']

        parent = Parent.objects.get(id=parent_id)
        classroom = Classe.objects.get(id=classroom_id)

        student = Student(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            lieu_de_naissance=lieu_de_naissance,
            parent=parent,
            classroom=classroom,
            inscription_date=inscription_date
        )
        student.save()
        return redirect('student_list')
    else:
        parents = Parent.objects.all()
        classrooms = Classe.objects.all()
        return render(request, 'student_create.html', {'parents': parents, 'classrooms': classrooms})

def parent_create(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        profession = request.POST['profession']
        parent = Parent(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address=address,
            profession=profession
        )
        parent.save()
        return redirect('parent_list')
    else:
        form = ParentForm()
    return render(request, 'parent_create.html', {'form': form})

def student_create(request):

    if request.method == "POST":
        # Informations du parent
        parent = Parent.objects.create(
            first_name=request.POST.get("parent_first_name"),
            last_name=request.POST.get("parent_last_name"),
            email=request.POST.get("parent_email"),
            phone_number=request.POST.get("parent_phone"),
            address=request.POST.get("parent_address"),
            profession=request.POST.get("parent_profession"),
        )
        # Informations élève
        classroom = Classe.objects.get(
            id=request.POST.get("classroom")
        )

        Student.objects.create(
            first_name=request.POST.get("student_first_name"),
            last_name=request.POST.get("student_last_name"),
            date_of_birth=request.POST.get("date_of_birth"),
            lieu_de_naissance=request.POST.get("lieu_de_naissance"),
            classroom=classroom,
            inscription_date=request.POST.get("inscription_date"),
            parent=parent,
        )

        messages.success(request, "L'élève a été inscrit avec succès.")

        return redirect("students:list")

    classrooms = Classe.objects.all()

    return render(
        request,
        "student_create.html",
        {
            "classrooms": classrooms,
        },
    )