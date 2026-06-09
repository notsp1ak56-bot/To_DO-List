from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Category(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField('Иконка', max_length=50, default='fas fa-tag')
    color = models.CharField('Цвет', max_length=20, default='secondary')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('О себе', max_length=500, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    telegram = models.CharField('Telegram', max_length=100, blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f'https://ui-avatars.com/api/?background=667eea&color=fff&size=100&name={self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]

    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает'),
        ('in_progress', '🔄 В процессе'),
        ('completed', '✅ Выполнена'),
        ('cancelled', '❌ Отменена'),
        ('overdue', '⚠️ Просрочена'),
    ]

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('Приоритет', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField('Срок выполнения', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    categories = models.ManyToManyField(Category, blank=True, related_name='tasks', verbose_name='Категории')
    is_overdue = models.BooleanField('Просрочена', default=False)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title

    def check_overdue(self):
        if self.due_date and self.status != 'completed':
            if timezone.now() > self.due_date:
                self.is_overdue = True
                if self.status != 'cancelled':
                    self.status = 'overdue'
            else:
                self.is_overdue = False
                if self.status == 'overdue':
                    self.status = 'pending'
            return True
        return False


class Company(models.Model):
    name = models.CharField('Название компании', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    logo = models.ImageField('Логотип', upload_to='company_logos/', blank=True, null=True)

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'

    def __str__(self):
        return self.name

    def get_employee_count(self):
        return self.employees.filter(is_active=True).count()

    def get_task_count(self):
        return self.company_tasks.count()


class Employee(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('employee', 'Сотрудник'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employments')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='employee')
    is_active = models.BooleanField('Активен', default=True)
    invited_at = models.DateTimeField('Дата приглашения', auto_now_add=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        unique_together = ['user', 'company']

    def __str__(self):
        return f'{self.user.username} - {self.company.name} ({self.get_role_display()})'


class CompanyTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В процессе'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена'),
        ('overdue', 'Просрочена'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_tasks')
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('Приоритет', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField('Срок выполнения', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_company_tasks')
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    completed_at = models.DateTimeField('Дата выполнения', blank=True, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='completed_company_tasks')
    is_overdue = models.BooleanField('Просрочена', default=False)

    class Meta:
        verbose_name = 'Задача компании'
        verbose_name_plural = 'Задачи компании'
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return f'{self.title} ({self.company.name})'

    def mark_completed(self, user):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()

    def check_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            if timezone.now() > self.due_date:
                self.is_overdue = True
                if self.status != 'cancelled':
                    self.status = 'overdue'
            else:
                self.is_overdue = False
                if self.status == 'overdue':
                    self.status = 'pending'
            return True
        return False


class PasswordChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_requests')
    new_password = models.CharField('Новый пароль', max_length=128)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_requests')
    reviewed_at = models.DateTimeField('Дата рассмотрения', null=True, blank=True)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Заявка на смену пароля'
        verbose_name_plural = 'Заявки на смену пароля'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_status_display()}'

    def approve(self, admin_user):
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.user.set_password(self.new_password)
        self.user.save()
        self.save()

    def reject(self, admin_user, comment=''):
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.comment = comment
        self.save()