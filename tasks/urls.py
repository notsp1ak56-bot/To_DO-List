from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create/', views.task_create, name='task_create'),
    path('edit/<int:pk>/', views.task_edit, name='task_edit'),
    path('delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('toggle/<int:pk>/', views.task_toggle_status, name='task_toggle'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<int:company_id>/add-employee/', views.company_add_employee, name='company_add_employee'),
    path('companies/<int:company_id>/remove-employee/<int:user_id>/', views.company_remove_employee,
         name='company_remove_employee'),
    path('companies/<int:company_id>/task/create/', views.company_task_create, name='company_task_create'),
    path('companies/task/<int:task_id>/complete/', views.company_task_complete, name='company_task_complete'),
    path('companies/task/<int:task_id>/delete/', views.company_task_delete, name='company_task_delete'),

    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('password-change-request/', views.password_change_request, name='password_change_request'),
    path('admin-password-requests/', views.admin_password_requests, name='admin_password_requests'),
]