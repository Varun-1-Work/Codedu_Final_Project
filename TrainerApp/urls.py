from django.urls import path
from . import views

urlpatterns = [
    path('trainer/dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    path('trainer/batch/<int:batch_id>/', views.batch_students, name='batch_students'),

    path('attendance/manage/', views.admin_mark_attendance, name='admin_attendance'),
    path('trainer/batch/<int:batch_id>/leaves/', views.batch_leaves, name='batch_leaves'),
    path('leave/update/<int:leave_id>/<str:status>/', views.update_leave_status, name='update_leave_status'),
    # Leave Application (THIS IS THE MISSING LINK)
    path('leave/apply/', views.apply_leave, name='trainer_apply_leave'),
   
    path('exam-eligibility/', views.trainer_exam_eligibility, name='trainer_exam_eligibility'),
    path('conduct-exam/', views.conduct_exam, name='conduct_exam'),
    path('exam/edit/<int:id>/', views.edit_exam, name='edit_exam'),
    path('exam/delete/<int:id>/', views.delete_exam, name='delete_exam'),
    path('exam/add/', views.add_exam, name='add_exam'),
    
    path('add-exam-marks/', views.add_exam_marks, name='add_exam_marks'),

    path("exam/<int:exam_id>/upload/", views.upload_exam_marks, name="upload_exam_marks"),
    path("exam/<int:exam_id>/marks/", views.uploaded_marks_history, name="uploaded_marks_history"),
    path("marks/<int:pk>/edit/", views.edit_exam_marks, name="edit_exam_marks"),

    path(
        "exam/<int:exam_id>/marks-action/",
        views.upload_or_edit_marks,
        name="upload_or_edit_marks"
    ),
path('ajax/load-courses/', views.load_courses, name='ajax_load_batch_course'),


]