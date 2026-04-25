from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
import random

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    enrollment_id = models.CharField(max_length=50, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    total_fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('Programming', 'Programming'),
        ('Web Development', 'Web Development'),
        ('Data Science', 'Data Science'),
        ('Electronics', 'Electronics'),
        ('Communication', 'Communication'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('AI & ML', 'AI & ML'),
        ('Robotics', 'Robotics'),
        ('Networking', 'Networking'),
        ('Database', 'Database'),
        ('Other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    publication_year = models.IntegerField(null=True, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    shelf_location = models.CharField(max_length=50, default='A1')
    rack_number = models.CharField(max_length=10, default='1')
    floor = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    qr_code = models.CharField(max_length=100, blank=True, null=True)  # QR code string
    average_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.available_copies}/{self.total_copies})"

    def update_rating(self):
        ratings = Rating.objects.filter(book=self)
        if ratings.exists():
            self.average_rating = ratings.aggregate(models.Avg('rating'))['rating__avg']
            self.total_ratings = ratings.count()
        else:
            self.average_rating = 0
            self.total_ratings = 0
        self.save()

    def predict_availability(self):
        """Smart prediction: when this book might become available"""
        active_loans = BookLoan.objects.filter(book=self, status__in=['borrowed', 'issued']).count()
        if active_loans == 0:
            return "Available now"
        # Calculate average return days from past loans
        returned_loans = BookLoan.objects.filter(book=self, status='returned', return_date__isnull=False)
        if returned_loans.exists():
            avg_days = (returned_loans.extra(select={'diff': "return_date - issue_date"}).values('diff')).aggregate(models.Avg('diff'))['diff__avg']
            if avg_days:
                days = int(avg_days.total_seconds() / 86400)
                return f"Likely available in ~{days} days"
        return "Check back later"

class BookLoan(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')

    def save(self, *args, **kwargs):
        if not self.due_date:
            # Teachers get 30 days, students 14
            profile = UserProfile.objects.get(user=self.user)
            days = 30 if profile.role == 'teacher' else 14
            self.due_date = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)

    def calculate_fine(self):
        if self.status == 'returned':
            return 0
        today = timezone.now()
        if today > self.due_date:
            days_overdue = (today - self.due_date).days
            return days_overdue * 5
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Rating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.book.update_rating()

class Reservation(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reservation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='waiting')  # waiting, notified, fulfilled, cancelled
    queue_position = models.IntegerField(default=0)

    class Meta:
        ordering = ['reservation_date']

    def __str__(self):
        return f"{self.user.username} reserved {self.book.title}"

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-borrowed_at']

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"