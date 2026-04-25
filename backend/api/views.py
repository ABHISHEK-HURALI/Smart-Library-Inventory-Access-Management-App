from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Book, BookLoan, UserProfile, Rating, Reservation, ReadingHistory, Notification, ActivityLog
from .serializers import BookSerializer, BookLoanSerializer, UserSerializer
import json
from datetime import datetime, timedelta
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
import random
import string

# ==================== PAGE VIEWS ====================

def student_login_page(request):
    return render(request, 'auth/student-login.html')

def student_signup_page(request):
    return render(request, 'auth/student-signup.html')

def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/api/student/login/page/')
    return render(request, 'dashboards/student-dashboard.html')

def admin_login_page(request):
    return render(request, 'auth/admin-login.html')

def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/api/admin/login/page/')
    return render(request, 'dashboards/admin-dashboard.html')

def teacher_login_page(request):
    return render(request, 'auth/teacher-login.html')

def teacher_signup_page(request):
    return render(request, 'auth/teacher-signup.html')

def teacher_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/api/teacher/login/page/')
    return render(request, 'dashboards/teacher-dashboard.html')

# ==================== AUTHENTICATION ====================

@csrf_exempt
@require_http_methods(["POST"])
def student_register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        enrollment_id = data.get('enrollment_id')
        department = data.get('department', '')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='student', enrollment_id=enrollment_id, department=department)
        
        ActivityLog.objects.create(user=user, action='Student Registered', details=f'Student {username} registered')
        
        return JsonResponse({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def teacher_register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        employee_id = data.get('employee_id')
        department = data.get('department')
        designation = data.get('designation', '')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='teacher', employee_id=employee_id, department=department, designation=designation)
        
        ActivityLog.objects.create(user=user, action='Teacher Registered', details=f'Teacher {username} registered')
        
        return JsonResponse({'message': 'Registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def admin_register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        admin_key = data.get('admin_key')
        
        if admin_key != 'ADMIN123':
            return JsonResponse({'error': 'Invalid admin key'}, status=401)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role='admin')
        
        return JsonResponse({'message': 'Admin registration successful'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def student_login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = UserProfile.objects.get(user=user)
            if profile.role == 'student':
                login(request, user)
                ActivityLog.objects.create(user=user, action='Student Login', details=f'Student {username} logged in')
                return JsonResponse({'message': 'Login successful', 'redirect': '/api/student/dashboard/'})
            return JsonResponse({'error': 'Not a student account'}, status=401)
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def teacher_login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = UserProfile.objects.get(user=user)
            if profile.role == 'teacher':
                login(request, user)
                ActivityLog.objects.create(user=user, action='Teacher Login', details=f'Teacher {username} logged in')
                return JsonResponse({'message': 'Login successful', 'redirect': '/api/teacher/dashboard/'})
            return JsonResponse({'error': 'Not a teacher account'}, status=401)
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def admin_login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = UserProfile.objects.get(user=user)
            if profile.role == 'admin':
                login(request, user)
                ActivityLog.objects.create(user=user, action='Admin Login', details=f'Admin {username} logged in')
                return JsonResponse({'message': 'Login successful', 'redirect': '/api/admin/dashboard/'})
            return JsonResponse({'error': 'Not an admin account'}, status=401)
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, action='Logout', details=f'{request.user.username} logged out')
    logout(request)
    return JsonResponse({'message': 'Logged out successfully'})

# ==================== STUDENT BOOK APIs ====================

def get_books(request):
    books = Book.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        books = books.filter(
            Q(title__icontains=search) | 
            Q(author__icontains=search) | 
            Q(category__icontains=search)
        )
    
    category = request.GET.get('category', '')
    if category:
        books = books.filter(category=category)
    
    author = request.GET.get('author', '')
    if author:
        books = books.filter(author__icontains=author)
    
    year = request.GET.get('year', '')
    if year:
        books = books.filter(publication_year=year)
    
    serializer = BookSerializer(books, many=True)
    data = serializer.data
    for book_data, book_obj in zip(data, books):
        book_data['prediction'] = book_obj.predict_availability()
    return JsonResponse({'books': data})

def get_book_categories(request):
    categories = Book.CATEGORY_CHOICES
    return JsonResponse({'categories': [{'code': c[0], 'name': c[1]} for c in categories]})

def get_authors(request):
    authors = Book.objects.values_list('author', flat=True).distinct()
    return JsonResponse({'authors': list(authors)})

def get_publication_years(request):
    years = Book.objects.values_list('publication_year', flat=True).distinct().exclude(publication_year__isnull=True).order_by('-publication_year')
    return JsonResponse({'years': list(years)})

@csrf_exempt
@require_http_methods(["POST"])
def borrow_book(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        user = request.user
        qr_code = data.get('qr_code', None)
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Please login first'}, status=401)
        
        if qr_code:
            book = Book.objects.get(qr_code=qr_code)
        else:
            book = Book.objects.get(id=book_id)
        
        if book.available_copies <= 0:
            return JsonResponse({'error': 'Book not available'}, status=400)
        
        profile = UserProfile.objects.get(user=user)
        active_loans = BookLoan.objects.filter(user=user, status__in=['borrowed', 'issued']).count()
        
        limit = 10 if profile.role == 'teacher' else 5
        if active_loans >= limit:
            return JsonResponse({'error': f'Maximum {limit} books allowed'}, status=400)
        
        book.available_copies -= 1
        book.save()
        
        due_days = 30 if profile.role == 'teacher' else 14
        due_date = timezone.now() + timedelta(days=due_days)
        loan = BookLoan.objects.create(book=book, user=user, due_date=due_date, status='borrowed')
        
        ReadingHistory.objects.create(user=user, book=book, borrowed_at=timezone.now())
        
        waiting_reservation = Reservation.objects.filter(book=book, status='waiting').first()
        if waiting_reservation:
            Notification.objects.create(
                user=waiting_reservation.user,
                message=f'Book "{book.title}" is now available! You were first in queue.',
                type='reservation_available'
            )
            waiting_reservation.status = 'notified'
            waiting_reservation.save()
        
        Notification.objects.create(
            user=user, 
            message=f'You borrowed "{book.title}". Due: {due_date.strftime("%Y-%m-%d")}',
            type='borrow'
        )
        
        ActivityLog.objects.create(user=user, action='Book Borrowed', details=f'{user.username} borrowed "{book.title}" via {"QR" if qr_code else "button"}')
        
        return JsonResponse({'message': 'Book borrowed successfully', 'due_date': due_date})
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def return_book(request):
    try:
        data = json.loads(request.body)
        loan_id = data.get('loan_id')
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Please login first'}, status=401)
        
        loan = BookLoan.objects.get(id=loan_id, user=user)
        loan.return_date = timezone.now()
        loan.status = 'returned'
        
        fine = loan.calculate_fine()
        if fine > 0:
            loan.fine_amount = fine
            profile = UserProfile.objects.get(user=user)
            profile.total_fine += fine
            profile.save()
        
        loan.save()
        
        try:
            history = ReadingHistory.objects.get(user=user, book=loan.book, returned_at__isnull=True)
            history.returned_at = timezone.now()
            history.save()
        except:
            pass
        
        book = loan.book
        book.available_copies += 1
        book.save()
        
        next_reservation = Reservation.objects.filter(book=book, status='waiting').order_by('reservation_date').first()
        if next_reservation:
            next_reservation.status = 'notified'
            next_reservation.save()
            Notification.objects.create(
                user=next_reservation.user,
                message=f'Book "{book.title}" is now available! You can borrow it now.',
                type='reservation_ready'
            )
        
        Notification.objects.create(
            user=user, 
            message=f'You returned "{book.title}". Fine: ₹{fine}',
            type='return'
        )
        
        ActivityLog.objects.create(user=user, action='Book Returned', details=f'{user.username} returned "{book.title}"')
        
        return JsonResponse({'message': 'Book returned successfully', 'fine': fine})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def my_loans(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    loans = BookLoan.objects.filter(user=request.user, status__in=['borrowed', 'issued'])
    result = []
    for loan in loans:
        fine = loan.calculate_fine()
        result.append({
            'id': loan.id,
            'book_title': loan.book.title,
            'book_id': loan.book.id,
            'issue_date': loan.issue_date,
            'due_date': loan.due_date,
            'fine': fine,
            'status': loan.status
        })
    return JsonResponse({'loans': result})

def my_fines(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    return JsonResponse({'total_fine': float(profile.total_fine)})

def my_notifications(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    data = [{'id': n.id, 'message': n.message, 'type': n.type, 'created_at': n.created_at} for n in notifications]
    return JsonResponse({'notifications': data})

def my_reading_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    history = ReadingHistory.objects.filter(user=request.user).select_related('book')[:20]
    data = [{
        'book_title': h.book.title,
        'borrowed_at': h.borrowed_at,
        'returned_at': h.returned_at,
        'book_id': h.book.id
    } for h in history]
    return JsonResponse({'history': data})

@csrf_exempt
@require_http_methods(["POST"])
def rate_book(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        rating = data.get('rating')
        review = data.get('review', '')
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Please login'}, status=401)
        
        book = Book.objects.get(id=book_id)
        has_borrowed = BookLoan.objects.filter(user=user, book=book, status='returned').exists()
        if not has_borrowed:
            return JsonResponse({'error': 'You can only rate books you have borrowed and returned'}, status=403)
        
        rating_obj, created = Rating.objects.update_or_create(
            book=book, user=user,
            defaults={'rating': rating, 'review': review}
        )
        
        return JsonResponse({'message': 'Rating submitted', 'average_rating': book.average_rating})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_book_ratings(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
        ratings = Rating.objects.filter(book=book).select_related('user')
        data = [{
            'username': r.user.username,
            'rating': r.rating,
            'review': r.review,
            'date': r.created_at
        } for r in ratings]
        return JsonResponse({'ratings': data, 'average': book.average_rating, 'count': book.total_ratings})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def reserve_book(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        user = request.user
        
        if not user.is_authenticated:
            return JsonResponse({'error': 'Please login'}, status=401)
        
        book = Book.objects.get(id=book_id)
        if book.available_copies > 0:
            return JsonResponse({'error': 'Book is available, you can borrow directly'}, status=400)
        
        existing_reservation = Reservation.objects.filter(book=book, user=user, status='waiting').first()
        if existing_reservation:
            return JsonResponse({'error': 'You already have a reservation for this book'}, status=400)
        
        count_before = Reservation.objects.filter(book=book, status='waiting').count()
        reservation = Reservation.objects.create(book=book, user=user, status='waiting', queue_position=count_before + 1)
        
        ActivityLog.objects.create(user=user, action='Book Reserved', details=f'{user.username} reserved "{book.title}"')
        
        return JsonResponse({'message': f'Book reserved. You are number {reservation.queue_position} in queue.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def my_reservations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    reservations = Reservation.objects.filter(user=request.user, status='waiting').select_related('book')
    data = [{
        'id': r.id,
        'book_title': r.book.title,
        'reservation_date': r.reservation_date,
        'queue_position': r.queue_position
    } for r in reservations]
    return JsonResponse({'reservations': data})

# ==================== ADMIN APIs ====================

def admin_stats(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    total_books = Book.objects.count()
    total_issued = BookLoan.objects.filter(status__in=['borrowed', 'issued']).count()
    total_students = UserProfile.objects.filter(role='student').count()
    total_teachers = UserProfile.objects.filter(role='teacher').count()
    overdue_books = BookLoan.objects.filter(status__in=['borrowed', 'issued'], due_date__lt=timezone.now()).count()
    total_fines_collected = BookLoan.objects.filter(fine_amount__gt=0).aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
    
    most_borrowed = BookLoan.objects.values('book__title', 'book__id').annotate(count=Count('id')).order_by('-count')[:5]
    
    return JsonResponse({
        'total_books': total_books,
        'total_issued': total_issued,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'overdue_books': overdue_books,
        'total_fines_collected': float(total_fines_collected),
        'most_borrowed': list(most_borrowed)
    })

def get_all_books(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return JsonResponse({'books': serializer.data})

@csrf_exempt
@require_http_methods(["POST"])
def admin_add_book(request):
    try:
        data = json.loads(request.body)
        qr_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        book = Book.objects.create(
            title=data.get('title'),
            author=data.get('author'),
            isbn=data.get('isbn'),
            category=data.get('category'),
            publication_year=data.get('publication_year'),
            total_copies=data.get('total_copies', 1),
            available_copies=data.get('total_copies', 1),
            shelf_location=data.get('shelf_location', 'A1'),
            rack_number=data.get('rack_number', '1'),
            floor=data.get('floor', 1),
            description=data.get('description', ''),
            qr_code=qr_str
        )
        ActivityLog.objects.create(user=request.user, action='Book Added', details=f'Added "{book.title}"')
        return JsonResponse({'message': 'Book added successfully', 'qr_code': qr_str})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def admin_delete_book(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        book = Book.objects.get(id=book_id)
        book_title = book.title
        book.delete()
        ActivityLog.objects.create(user=request.user, action='Book Deleted', details=f'Deleted "{book_title}"')
        return JsonResponse({'message': 'Book deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_all_loans(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    loans = BookLoan.objects.filter(status__in=['borrowed', 'issued']).select_related('user', 'book')
    data = []
    for loan in loans:
        data.append({
            'id': loan.id,
            'student_name': loan.user.username,
            'book_title': loan.book.title,
            'issue_date': loan.issue_date,
            'due_date': loan.due_date,
            'fine': loan.calculate_fine()
        })
    return JsonResponse({'loans': data})

def get_all_users(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    users = UserProfile.objects.select_related('user').all()
    data = []
    for u in users:
        data.append({
            'username': u.user.username,
            'email': u.user.email,
            'role': u.role,
            'department': u.department,
            'created_at': u.created_at,
            'total_fine': float(u.total_fine)
        })
    return JsonResponse({'users': data})

def get_teacher_department_students(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'teacher':
        return JsonResponse({'error': 'Teacher access only'}, status=403)
    
    students = UserProfile.objects.filter(role='student', department=profile.department).select_related('user')
    data = []
    for s in students:
        issued = BookLoan.objects.filter(user=s.user, status__in=['borrowed', 'issued']).count()
        data.append({
            'username': s.user.username,
            'enrollment_id': s.enrollment_id,
            'issued_books': issued,
            'total_fine': float(s.total_fine)
        })
    return JsonResponse({'students': data})

def get_activity_logs(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    logs = ActivityLog.objects.all().order_by('-created_at')[:100]
    data = [{'user': l.user.username, 'action': l.action, 'details': l.details, 'time': l.created_at} for l in logs]
    return JsonResponse({'logs': data})

def get_popular_books(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    popular = Book.objects.filter(total_ratings__gt=0).order_by('-average_rating')[:10]
    serializer = BookSerializer(popular, many=True)
    return JsonResponse({'popular_books': serializer.data})

def get_reservations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    profile = UserProfile.objects.get(user=request.user)
    if profile.role != 'admin':
        return JsonResponse({'error': 'Admin access only'}, status=403)
    
    reservations = Reservation.objects.filter(status='waiting').select_related('user', 'book')
    data = [{'user': r.user.username, 'book': r.book.title, 'date': r.reservation_date, 'queue': r.queue_position} for r in reservations]
    return JsonResponse({'reservations': data})

# ==================== SAMPLE DATA ====================

def add_sample_books(request):
    books_data = [
        {'title': 'Python Programming', 'author': 'John Doe', 'isbn': '9781234567890', 'category': 'Programming', 'publication_year': 2020, 'total_copies': 5},
        {'title': 'Django for Beginners', 'author': 'Jane Smith', 'isbn': '9781234567891', 'category': 'Web Development', 'publication_year': 2021, 'total_copies': 3},
        {'title': 'Electronic Devices', 'author': 'Robert Boylestad', 'isbn': '9781234567895', 'category': 'Electronics', 'publication_year': 2016, 'total_copies': 4},
        {'title': 'Communication Systems', 'author': 'Simon Haykin', 'isbn': '9781234567896', 'category': 'Communication', 'publication_year': 2019, 'total_copies': 3},
        {'title': 'Thermodynamics', 'author': 'Yunus Cengel', 'isbn': '9781234567901', 'category': 'Mechanical', 'publication_year': 2019, 'total_copies': 5},
    ]
    count = 0
    for book_data in books_data:
        book_data['available_copies'] = book_data['total_copies']
        book_data['qr_code'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        obj, created = Book.objects.get_or_create(isbn=book_data['isbn'], defaults=book_data)
        if created:
            count += 1
    return JsonResponse({'message': f'{count} sample books added successfully'})


from django.db.models import Q
from django.http import JsonResponse
from .models import Book
from .serializers import BookSerializer

def get_books(request):
    books = Book.objects.all()
    search = request.GET.get('search', '')
    if search:
        books = books.filter(
            Q(title__icontains=search) | 
            Q(author__icontains=search) | 
            Q(category__icontains=search)
        )
    category = request.GET.get('category', '')
    if category:
        books = books.filter(category=category)
    author = request.GET.get('author', '')
    if author:
        books = books.filter(author__icontains=author)
    year = request.GET.get('year', '')
    if year:
        books = books.filter(publication_year=year)
    serializer = BookSerializer(books, many=True)
    return JsonResponse({'books': serializer.data})