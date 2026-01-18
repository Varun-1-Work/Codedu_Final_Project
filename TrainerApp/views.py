from django.shortcuts import render, redirect,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from StudentApp.models import Attendance, Batch, BatchProgress,  Course,  LeaveApplication, Syllabus, Trainer, Student, ExamResult, ConductedExam
from .models import TrainerLeave
from .forms import ExamResultEditForm, TrainerLeaveForm, ExamResultForm, ConductExamForm

from StudentApp.services import check_exam_eligibility
from django.utils import timezone
from django.utils.timezone import localdate
from django.db.models import Avg


#####################################################################################################################################

@login_required
def trainer_dashboard(request):
    try:
        trainer = request.user.trainer
    except Trainer.DoesNotExist:
        messages.error(request, "Access Denied")
        return redirect('login')

    # ---------------- BATCH DATA ----------------
    batches = Batch.objects.filter(trainer=trainer).order_by('time_slot')
    today = timezone.now().date()

    dashboard_data = []

    for batch in batches:
        is_attendance_marked = Attendance.objects.filter(
            student__batch=batch,
            date=today
        ).exists()

        total_topics = Syllabus.objects.filter(course=batch.course).count()
        completed_topics = BatchProgress.objects.filter(batch=batch).count()

        progress = int((completed_topics / total_topics) * 100) if total_topics else 0

        dashboard_data.append({
            'batch': batch,
            'student_count': batch.students.count(),
            'is_attendance_marked': is_attendance_marked,
            'progress': progress,
            'completed_topics': completed_topics,
            'total_topics': total_topics,
        })

    # ---------------- EXAM CARDS DATA ----------------
    exam_cards = []

    exams = ConductedExam.objects.filter(created_by=trainer)

    for exam in exams:
        batch = exam.batch
        total_students = batch.students.count()

        attended_students = Attendance.objects.filter(
            student__batch=batch
        ).values('student').distinct().count()

        progress = int((attended_students / total_students) * 100) if total_students else 0

        exam_cards.append({
            'exam': exam,
            'batch': batch,
            'total_students': total_students,
            'attended_students': attended_students,
            'progress': progress,
        })

    total_students = Student.objects.filter(batch__in=batches).count()

    return render(request, 'trainer/dashboard_trainer.html', {
        'trainer': trainer,
        'dashboard_data': dashboard_data,
        'exam_cards': exam_cards,   # 👈 IMPORTANT
        'total_batches': batches.count(),
        'total_students': total_students,
        'today': today
    })

@login_required
def batch_students(request, batch_id):
    try:
        trainer = request.user.trainer
        batch = get_object_or_404(Batch, id=batch_id, trainer=trainer)
    except (Trainer.DoesNotExist, Batch.DoesNotExist):
        messages.error(request, "Invalid Batch or Unauthorized Access")
        return redirect('trainer_dashboard')

    students = batch.students.all()
    pending_leaves = LeaveApplication.objects.filter(student__batch=batch, status='Pending').order_by('-applied_on')

    return render(request, 'trainer/batch_students.html', {
        'batch': batch,
        'students': students,
        'pending_leaves': pending_leaves,
    })

####################################################################################################################


####################################################################################################################
# attendance 


@login_required
def admin_mark_attendance(request):
    user = request.user
    
    if user.is_superuser:
        batches = Batch.objects.all()
    elif hasattr(user, 'trainer'):
        batches = Batch.objects.filter(trainer=user.trainer)
    else:
        batches = Batch.objects.none()

    selected_batch_id = request.GET.get('batch_id')
    students = Student.objects.none()

    if selected_batch_id:
        if user.is_superuser:
            batch = get_object_or_404(Batch, id=selected_batch_id)
        else:
            batch = get_object_or_404(Batch, id=selected_batch_id, trainer=user.trainer)
        students = batch.students.all().select_related('user')

    if request.method == 'POST':
        date = request.POST.get('date')
        marked_count = 0
        
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student, 
                    date=date, 
                    defaults={'status': status}
                )
                marked_count += 1
        
        if marked_count > 0:
            messages.success(request, f"Attendance successfully marked for {marked_count} students.")
        else:
            messages.warning(request, "No attendance changes were detected.")

        return redirect(f'{request.path}?batch_id={selected_batch_id}')

    return render(request, 'trainer/mark_attendance.html', {
        'batches': batches,
        'students': students,
        'selected_batch_id': int(selected_batch_id) if selected_batch_id else None,
        'today': timezone.now().date()
    })

@login_required
def batch_leaves(request, batch_id):
    try:
        trainer = request.user.trainer
        batch = get_object_or_404(Batch, id=batch_id, trainer=trainer)
    except (Trainer.DoesNotExist, Batch.DoesNotExist):
        messages.error(request, "Access Denied: Invalid Batch")
        return redirect('trainer_dashboard')

    leaves = LeaveApplication.objects.filter(student__batch=batch).order_by('-applied_on')
    return render(request, 'trainer/leave_requests.html', {'batch': batch, 'leaves': leaves})

@login_required
def update_leave_status(request, leave_id, status):
    if not (request.user.is_staff or hasattr(request.user, 'trainer')):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    leave = get_object_or_404(LeaveApplication, id=leave_id)
    if status in ['Approved', 'Rejected']:
        leave.status = status
        leave.save()
        action = "Approved" if status == 'Approved' else "Rejected"
        messages.success(request, f"Leave for {leave.student.user.first_name} has been {action}.")
    
    return redirect(request.META.get('HTTP_REFERER', 'trainer_dashboard'))

####################################################################################################################



@login_required
def apply_leave(request):
    try:
        trainer = request.user.trainer
    except:
        messages.error(request, "Access Denied")
        return redirect('login')

    # Handle Form Submission
    if request.method == 'POST':
        form = TrainerLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.trainer = trainer
            leave.save()
            messages.success(request, "Leave application submitted successfully!")
            return redirect('trainer_apply_leave')
    else:
        form = TrainerLeaveForm()

    # Fetch History
    leave_history = TrainerLeave.objects.filter(trainer=trainer).order_by('-applied_on')

    return render(request, 'trainer/apply_leave.html', {
        'form': form,
        'leave_history': leave_history
    })


########################################################################################################################

@login_required
def trainer_exam_eligibility(request):
    trainer = request.user.trainer

    selected_batch = request.GET.get("batch")
    selected_course = request.GET.get("course")

    students = Student.objects.filter(batch__trainer=trainer)

    if selected_batch:
        students = students.filter(batch_id=selected_batch)

    if selected_course:
        students = students.filter(batch__course_id=selected_course)

    eligibility_data = []
    for student in students.select_related("batch", "batch__course", "user"):
        result = check_exam_eligibility(student)
        eligibility_data.append({
            "student": student,
            "result": result
        })

    # ✅ FIXED QUERIES
    batches = Batch.objects.filter(trainer=trainer)

    courses = Course.objects.filter(
        batches__trainer=trainer
    ).distinct()

    return render(request, "trainer/exam_eligibility.html", {
        "eligibility_data": eligibility_data,
        "batches": batches,
        "courses": courses,
        "selected_batch": selected_batch,
        "selected_course": selected_course,
    })

@login_required
def upload_exam_marks(request, exam_id):
    trainer = request.user.trainer

    exam = get_object_or_404(
        ConductedExam,
        id=exam_id,
        created_by=trainer
    )

    students = Student.objects.filter(batch=exam.batch)

    if request.method == "POST":
        for student in students:
            marks = request.POST.get(f"marks_{student.id}")

            if marks is not None and marks != "":
                marks = int(marks)

                ExamResult.objects.update_or_create(
                    student=student,
                    exam_name=exam,
                    defaults={
                        "marks_obtained": marks,
                        "total_marks": exam.total_marks,
                        "date_conducted": exam.date_conducted,
                        "is_passed": (marks / exam.total_marks) * 100 >= 40
                    }
                )

        messages.success(request, "Marks uploaded successfully.")
        return redirect("uploaded_marks_history", exam_id=exam.id)

    return render(request, "trainer/upload_exam_marks.html", {
        "exam": exam,
        "students": students,
    })



@login_required
def conduct_exam(request):
    trainer = request.user.trainer
    today = localdate()

    # ---------------- ADD EXAM ----------------
    if request.method == "POST":
        form = ConductExamForm(request.POST, trainer=trainer)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = trainer
            exam.save()

            

            messages.success(request, f"Exam '{exam.exam_name}' added successfully!")
            return redirect('conduct_exam')
    else:
        form = ConductExamForm(trainer=trainer)

    # ---------------- FETCH EXAMS ----------------
    exams = ConductedExam.objects.filter(
        created_by=trainer
    ).select_related('batch')

    exam_cards = []

    for exam in exams:
        batch = exam.batch
        if not batch:
            continue

        total_students = batch.students.count()

        uploaded_marks = ExamResult.objects.filter(
            student__batch=batch,
            exam_name=exam,
            marks_obtained__isnull=False
        ).values('student').distinct().count()

        progress = int((uploaded_marks / total_students) * 100) if total_students else 0

        # STATUS LOGIC
        if total_students > 0 and uploaded_marks == total_students:
            status = "Completed"
        elif exam.date_conducted <= today and uploaded_marks > 0:
            status = "Pending"
        elif exam.date_conducted <= today:
            status = "Pending"
        else:
            status = "Scheduled"

        exam_cards.append({
            'exam': exam,
            'total_students': total_students,
            'uploaded_marks': uploaded_marks,
            'progress': progress,
            'status': status,
        })

    # ---------------- CONTEXT ----------------
    context = {
        'form': form,
        'exams': exams,
        'exam_cards': exam_cards,
        'today': today,   # ✅ REQUIRED for template logic
    }

    return render(request, 'trainer/conduct_exam.html', context)


def add_exam(request):
    trainer = request.user.trainer

    if request.method == 'POST':
        form = ConductExamForm(request.POST, trainer=trainer)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = trainer
            exam.save()
            return redirect('conduct_exam')
    else:
        form = ConductExamForm(trainer=trainer)

    return render(request, 'trainer/add_exam.html', {'form': form})

def edit_exam(request, id):
    exam = get_object_or_404(ConductedExam, id=id)

    if request.method == 'POST':
        form = ConductExamForm(request.POST, instance=exam, trainer=exam.created_by)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam updated successfully.")
            return redirect('conduct_exam')  # your conduct exam page
    else:
        form = ConductExamForm(instance=exam, trainer=exam.created_by)

    context = {
        'form': form,
        'exam': exam
    }
    return render(request, 'trainer/edit_exam.html', context)

def delete_exam(request, id):
    exam = get_object_or_404(ConductedExam, id=id)
    exam.delete()
    messages.success(request, "Exam deleted successfully.")
    return redirect('conduct_exam')

@login_required
def add_exam_marks(request):
    trainer = request.user.trainer

    if request.method == "POST":
        form = ExamResultForm(request.POST, trainer=trainer)
        if form.is_valid():
            result = form.save(commit=False)

            # prevent duplicate entry
            if ExamResult.objects.filter(
                student=result.student,
                exam_name=result.exam_name
            ).exists():
                messages.warning(
                    request,
                    "Marks already uploaded for this student and exam."
                )
                return redirect("add_exam_marks")

            result.date_conducted = timezone.now().date()
            result.is_passed = (result.marks_obtained / result.total_marks) * 100 >= 40
            result.save()

            messages.success(request, "Exam marks uploaded successfully!")
            return redirect("add_exam_marks")
    else:
        form = ExamResultForm(trainer=trainer)

    return render(request, "trainer/add_mark.html", {
        "form": form
    })



@login_required
def edit_exam_marks(request, pk):
    trainer = request.user.trainer
    mark = get_object_or_404(
        ExamResult,
        pk=pk,
        exam_name__created_by=trainer
    )

    if request.method == "POST":
        form = ExamResultEditForm(request.POST, instance=mark)
        if form.is_valid():
            obj = form.save(commit=False)

            # pass/fail logic
            if obj.total_marks and obj.marks_obtained is not None:
                obj.is_passed = (obj.marks_obtained / obj.total_marks) * 100 >= 40
            else:
                obj.is_passed = False

            obj.save()
            messages.success(request, "Marks updated successfully.")
            return redirect("uploaded_marks_history", exam_id=obj.exam_name.id)
    else:
        form = ExamResultEditForm(instance=mark)

    return render(request, "trainer/edit_exam_marks.html", {
        "form": form,
        "mark": mark,
    })


@login_required
def uploaded_marks_history(request, exam_id):
    exam = get_object_or_404(ConductedExam, id=exam_id)

    marks = ExamResult.objects.filter(
        exam_name=exam
    ).select_related("student", "student__batch")

    return render(request, "trainer/marks_history.html", {
        "exam": exam,
        "marks": marks,
    })


@login_required
def upload_or_edit_marks(request, exam_id):
    trainer = request.user.trainer

    exam = get_object_or_404(
        ConductedExam,
        id=exam_id,
        created_by=trainer
    )

    # check if marks already uploaded
    marks_exist = ExamResult.objects.filter(
        exam_name=exam
    ).exists()

    if marks_exist:
        return redirect("uploaded_marks_history", exam_id=exam.id)
    else:
        return redirect("upload_exam_marks", exam_id=exam.id)


# Helper function to check eligibility
def check_student_eligibility(student):
    """
    Returns a dict with eligibility info for a single student.
    """
    result = {
        'eligible': True,
        'reasons': []
    }

    # 1. Fee check
    if not student.is_fee_paid:
        result['eligible'] = False
        result['reasons'].append("Fee not paid")

    # 2. Attendance check (average attendance >= 75)
    if hasattr(student, 'results') and student.results.exists():
        avg_attendance = student.results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
        if avg_attendance < 75:
            result['eligible'] = False
            result['reasons'].append("Attendance below 75%")
    else:
        result['eligible'] = False
        result['reasons'].append("No exam results")

    # 3. Academics check (must pass all exams)
    if student.results.exists():
        failed_exams = student.results.filter(is_passed=False)
        if failed_exams.exists():
            result['eligible'] = False
            result['reasons'].append("Failed in one or more exams")
    else:
        result['eligible'] = False
        result['reasons'].append("No exams attempted")

    return result

def load_courses(request):
    batch_id = request.GET.get('batch_id')
    courses = []

    if batch_id:
        # Fetch the batch; use get_object_or_404 for safety if you want 404 on invalid ID
        batch = Batch.objects.filter(id=batch_id).first()

        if batch:
            # If batch has a related course, add it to the list
            if hasattr(batch, 'course') and batch.course:
                courses = [batch.course]

    return render(request, 'trainer/course_dropdown_list_options.html', {'courses': courses})