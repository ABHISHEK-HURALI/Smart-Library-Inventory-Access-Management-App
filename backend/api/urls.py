from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path('student/login/page/', views.student_login_page),
    path('student/signup/page/', views.student_signup_page),
    path('student/dashboard/', views.student_dashboard),
    path('student/register/', views.student_register),
    path('student/login/', views.student_login_view),
    
    # Teacher URLs
    path('teacher/login/page/', views.teacher_login_page),
    path('teacher/signup/page/', views.teacher_signup_page),
    path('teacher/dashboard/', views.teacher_dashboard),
    path('teacher/register/', views.teacher_register),
    path('teacher/login/', views.teacher_login_view),
    path('teacher/students/', views.get_teacher_department_students),
    
    # Admin URLs
    path('admin/login/page/', views.admin_login_page),
    path('admin/dashboard/', views.admin_dashboard),
    path('admin/register/', views.admin_register),
    path('admin/login/', views.admin_login_view),
    
    # Common Auth
    path('logout/', views.logout_view),
    
    # Book APIs (Student & General)
    path('books/', views.get_books),
    path('books/categories/', views.get_book_categories),
    path('books/authors/', views.get_authors),
    path('books/years/', views.get_publication_years),
    path('books/<int:book_id>/ratings/', views.get_book_ratings),
    path('borrow/', views.borrow_book),
    path('return/', views.return_book),
    path('my-loans/', views.my_loans),
    path('my-fines/', views.my_fines),
    path('my-notifications/', views.my_notifications),
    path('my-reading-history/', views.my_reading_history),
    path('my-reservations/', views.my_reservations),
    path('rate-book/', views.rate_book),
    path('reserve-book/', views.reserve_book),
    
    # Admin APIs
    path('admin/stats/', views.admin_stats),
    path('admin/books/', views.get_all_books),
    path('admin/add-book/', views.admin_add_book),
    path('admin/delete-book/', views.admin_delete_book),
    path('admin/loans/', views.get_all_loans),
    path('admin/students/', views.get_all_users),
    path('admin/users/', views.get_all_users),
    path('admin/activity-logs/', views.get_activity_logs),
    path('admin/popular-books/', views.get_popular_books),
    path('admin/reservations/', views.get_reservations),
    
    # Sample Data
    path('add-sample-books/', views.add_sample_books),
]