from django.utils import timezone
from .models import Task, CompanyTask, Employee


class CheckOverdueTasksMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Проверка личных задач
            tasks = Task.objects.filter(user=request.user, status__in=['pending', 'in_progress'])
            for task in tasks:
                task.check_overdue()
                task.save()

            # Проверка задач компании (где пользователь является сотрудником)
            companies = Employee.objects.filter(user=request.user, is_active=True).values_list('company_id', flat=True)
            company_tasks = CompanyTask.objects.filter(company_id__in=companies, status__in=['pending', 'in_progress'])
            for task in company_tasks:
                task.check_overdue()
                task.save()

        response = self.get_response(request)
        return response