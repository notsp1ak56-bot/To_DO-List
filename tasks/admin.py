from django.contrib import admin
from .models import Task, Category, Profile, Company, Employee, CompanyTask, PasswordChangeRequest


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'due_date', 'created_at', 'is_overdue']
    list_filter = ['status', 'priority', 'created_at', 'categories', 'is_overdue']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'telegram', 'created_at']
    search_fields = ['user__username', 'phone']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'get_employee_count']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'is_active', 'invited_at']
    list_filter = ['role', 'is_active', 'company']
    search_fields = ['user__username', 'company__name']


@admin.register(CompanyTask)
class CompanyTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'status', 'priority', 'due_date', 'created_by', 'is_overdue']
    list_filter = ['status', 'priority', 'company', 'is_overdue']
    search_fields = ['title', 'description']


@admin.register(PasswordChangeRequest)
class PasswordChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email']
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for req in queryset:
            if req.status == 'pending':
                req.approve(request.user)
        self.message_user(request, f'Одобрено {queryset.count()} заявок')

    approve_requests.short_description = 'Одобрить выбранные заявки'

    def reject_requests(self, request, queryset):
        for req in queryset:
            if req.status == 'pending':
                req.reject(request.user, 'Отклонено администратором')
        self.message_user(request, f'Отклонено {queryset.count()} заявок')

    reject_requests.short_description = 'Отклонить выбранные заявки'