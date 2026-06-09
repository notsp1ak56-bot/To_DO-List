from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from .models import Task, Profile, Category, Company, Employee, CompanyTask, PasswordChangeRequest
from .forms import TaskForm, CustomPasswordResetForm, CustomSetPasswordForm, PasswordChangeRequestForm


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('task_list')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('task_list')
    else:
        form = AuthenticationForm()
    return render(request, 'tasks/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')


@login_required
def task_list(request):
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    tasks = Task.objects.filter(user=request.user)

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if category_filter:
        tasks = tasks.filter(categories__id=category_filter)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    paginator = Paginator(tasks, 9)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    total_tasks = Task.objects.filter(user=request.user).count()
    completed_tasks = Task.objects.filter(user=request.user, status='completed').count()
    pending_tasks = Task.objects.filter(user=request.user, status='pending').count()
    in_progress_tasks = Task.objects.filter(user=request.user, status='in_progress').count()
    categories = Category.objects.all()

    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'categories': categories,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            form.save_m2m()
            messages.success(request, 'Задача успешно создана!')
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Создать задачу'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Редактировать задачу'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена!')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'completed':
        task.status = 'pending'
        messages.info(request, f'Задача "{task.title}" возвращена в работу')
    else:
        task.status = 'completed'
        messages.success(request, f'Задача "{task.title}" выполнена!')
    task.save()
    return redirect('task_list')


@login_required
def profile_view(request):
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    profile = request.user.profile
    tasks = Task.objects.filter(user=request.user)

    context = {
        'profile': profile,
        'user': request.user,
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'recent_tasks': tasks.order_by('-created_at')[:5],
    }
    return render(request, 'tasks/profile.html', context)


@login_required
def profile_edit(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        profile = request.user.profile
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.telegram = request.POST.get('telegram', '')

        if request.FILES.get('avatar'):
            if profile.avatar:
                profile.avatar.delete()
            profile.avatar = request.FILES['avatar']

        profile.save()

        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')

    return render(request, 'tasks/profile_edit.html', {'user': request.user})


@login_required
def dashboard_view(request):
    tasks = Task.objects.filter(user=request.user)

    status_stats = {
        'pending': tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed': tasks.filter(status='completed').count(),
    }

    priority_stats = {
        'urgent': tasks.filter(priority='urgent').count(),
        'high': tasks.filter(priority='high').count(),
        'medium': tasks.filter(priority='medium').count(),
        'low': tasks.filter(priority='low').count(),
    }

    context = {
        'total_tasks': tasks.count(),
        'status_stats': status_stats,
        'priority_stats': priority_stats,
        'recent_tasks': tasks.order_by('-created_at')[:10],
    }
    return render(request, 'tasks/dashboard.html', context)


def is_company_admin(user, company_id):
    try:
        employee = Employee.objects.get(user=user, company_id=company_id, is_active=True)
        return employee.role in ['owner', 'admin']
    except Employee.DoesNotExist:
        return False


def is_company_owner(user, company_id):
    try:
        company = Company.objects.get(id=company_id)
        return company.created_by == user
    except Company.DoesNotExist:
        return False


def can_manage_tasks(user, company_id):
    try:
        employee = Employee.objects.get(user=user, company_id=company_id, is_active=True)
        return employee.role in ['owner', 'admin']
    except Employee.DoesNotExist:
        return False


@login_required
def company_list(request):
    my_companies = Company.objects.filter(created_by=request.user)
    my_employments = Employee.objects.filter(user=request.user, is_active=True).select_related('company')

    context = {
        'my_companies': my_companies,
        'my_employments': my_employments,
    }
    return render(request, 'tasks/company_list.html', context)


@login_required
def company_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if name:
            company = Company.objects.create(
                name=name,
                description=description,
                created_by=request.user
            )
            Employee.objects.create(
                user=request.user,
                company=company,
                role='owner',
                is_active=True
            )
            messages.success(request, f'Компания "{name}" успешно создана!')
            return redirect('company_detail', company_id=company.id)

    return render(request, 'tasks/company_create.html')


@login_required
def company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    try:
        employee = Employee.objects.get(user=request.user, company=company, is_active=True)
        user_role = employee.role
    except Employee.DoesNotExist:
        messages.error(request, 'Вы не являетесь сотрудником этой компании')
        return redirect('company_list')

    employees = Employee.objects.filter(company=company, is_active=True).select_related('user')
    tasks = CompanyTask.objects.filter(company=company)
    can_manage = user_role in ['owner', 'admin']

    context = {
        'company': company,
        'employees': employees,
        'tasks': tasks,
        'user_role': user_role,
        'can_manage': can_manage,
        'is_owner': user_role == 'owner',
    }
    return render(request, 'tasks/company_detail.html', context)


@login_required
def company_add_employee(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if not is_company_admin(request.user, company_id):
        messages.error(request, 'У вас нет прав для добавления сотрудников')
        return redirect('company_detail', company_id=company_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role', 'employee')

        try:
            user = User.objects.get(username=username)
            existing = Employee.objects.filter(user=user, company=company).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.role = role
                    existing.save()
                    messages.success(request, f'Сотрудник {username} повторно добавлен')
                else:
                    messages.warning(request, f'{username} уже является сотрудником')
            else:
                Employee.objects.create(
                    user=user,
                    company=company,
                    role=role,
                    is_active=True
                )
                messages.success(request, f'Сотрудник {username} добавлен!')
        except User.DoesNotExist:
            messages.error(request, f'Пользователь {username} не найден')

    return redirect('company_detail', company_id=company_id)


@login_required
def company_remove_employee(request, company_id, user_id):
    company = get_object_or_404(Company, id=company_id)

    if not is_company_owner(request.user, company_id):
        messages.error(request, 'Только владелец компании может удалять сотрудников')
        return redirect('company_detail', company_id=company_id)

    employee = get_object_or_404(Employee, user_id=user_id, company=company)

    if employee.role == 'owner':
        messages.error(request, 'Нельзя удалить владельца компании')
    else:
        employee.delete()
        messages.success(request, 'Сотрудник удален')

    return redirect('company_detail', company_id=company_id)


@login_required
def company_task_create(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if not can_manage_tasks(request.user, company_id):
        messages.error(request, 'Только руководитель может создавать задачи')
        return redirect('company_detail', company_id=company_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date')

        if title:
            CompanyTask.objects.create(
                company=company,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date if due_date else None,
                created_by=request.user,
                status='pending'
            )
            messages.success(request, f'Задача "{title}" создана!')
            return redirect('company_detail', company_id=company_id)

    return render(request, 'tasks/company_task_form.html', {'company': company})


@login_required
def company_task_complete(request, task_id):
    task = get_object_or_404(CompanyTask, id=task_id)

    if not can_manage_tasks(request.user, task.company.id):
        messages.error(request, 'Только руководитель может завершать задачи')
        return redirect('company_detail', company_id=task.company.id)

    if task.status == 'completed':
        messages.warning(request, 'Задача уже выполнена')
    else:
        task.mark_completed(request.user)
        messages.success(request, f'Задача "{task.title}" выполнена!')

    return redirect('company_detail', company_id=task.company.id)


@login_required
def company_task_delete(request, task_id):
    task = get_object_or_404(CompanyTask, id=task_id)

    if not can_manage_tasks(request.user, task.company.id):
        messages.error(request, 'Только руководитель может удалять задачи')
        return redirect('company_detail', company_id=task.company.id)

    task.delete()
    messages.success(request, 'Задача удалена')
    return redirect('company_detail', company_id=task.company.id)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'tasks/password_reset.html'
    email_template_name = 'tasks/password_reset_email.html'
    subject_template_name = 'tasks/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'tasks/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'tasks/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = CustomSetPasswordForm


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'tasks/password_reset_complete.html'


@login_required
def password_change_request(request):
    if request.method == 'POST':
        form = PasswordChangeRequestForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            PasswordChangeRequest.objects.create(
                user=request.user,
                new_password=new_password
            )
            messages.success(request, 'Заявка на смену пароля отправлена администратору')
            return redirect('profile')
    else:
        form = PasswordChangeRequestForm()

    return render(request, 'tasks/password_change_request.html', {'form': form})


@user_passes_test(lambda u: u.is_staff)
def admin_password_requests(request):
    pending_requests = PasswordChangeRequest.objects.filter(status='pending')
    approved_requests = PasswordChangeRequest.objects.filter(status='approved')[:20]
    rejected_requests = PasswordChangeRequest.objects.filter(status='rejected')[:20]

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')

        try:
            req = PasswordChangeRequest.objects.get(id=request_id, status='pending')
            if action == 'approve':
                req.approve(request.user)
                messages.success(request, f'Заявка от {req.user.username} одобрена')
            elif action == 'reject':
                req.reject(request.user, comment)
                messages.warning(request, f'Заявка от {req.user.username} отклонена')
        except PasswordChangeRequest.DoesNotExist:
            messages.error(request, 'Заявка не найдена')

        return redirect('admin_password_requests')

    context = {
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
    }
    return render(request, 'tasks/admin_password_requests.html', context)