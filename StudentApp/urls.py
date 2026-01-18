from django.urls import path
from . import views

urlpatterns = [
    # --- AUTHENTICATION ---
    path('', views.student_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # --- DASHBOARDS ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    
   
    # [NEW] These are the missing lines causing your error:
 
    # --- ACADEMICS & ATTENDANCE ---
    path('apply-leave/', views.apply_leave, name='apply_leave'),
    path('attendance/my-stats/', views.student_my_attendance, name='my_attendance'),
    path('courses/', views.course_listt, name='course_listt'),
    path('pay-fee/', views.pay_fee, name='pay_fee'),
    path('id-card/', views.view_id_card, name='view_id_card'),
    path('classroom/', views.my_classroom, name='my_classroom'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('exams/', views.exam_portal, name='exam_portal'),
    path('exams/download/', views.download_certificate, name='download_certificate'),
    path('library/', views.my_library, name='my_library'),
    path('placements/', views.placement_portal, name='placement_portal'),
    path('schedule/', views.my_schedule, name='my_schedule'),
    path('lesson-plan/', views.lesson_plan, name='lesson_plan'),
    

]