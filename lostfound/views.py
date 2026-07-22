from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.text import slugify
from django.conf import settings
import os

from .models import (
    Profile, Case, CaseImage, SightingReport, DetectiveApplication,
    DetectiveRequest, CaseAssignment, InvestigationUpdate,
    DetectiveAchievement, Feedback, Blog, Notification
)
from .ai_engine import add_to_index, search_similar_images


# ============== DECORATORS ==============

def user_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'USER':
            messages.error(request, "Access denied. User privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def detective_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'DETECTIVE':
            messages.error(request, "Access denied. Detective privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ============== AUTHENTICATION VIEWS ==============

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect('register')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
        
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect('register')
        
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, phone=phone)
        
        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')
    
    return render(request, 'lostfound/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'lostfound/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ============== HOME & PUBLIC VIEWS ==============

def home_view(request):
    lost_cases = Case.objects.filter(case_type='LOST', status='OPEN').order_by('-created_at')[:6]
    found_cases = Case.objects.filter(case_type='FOUND', status='OPEN').order_by('-created_at')[:6]
    blogs = Blog.objects.filter(published=True).order_by('-created_at')[:3]
    
    context = {
        'lost_cases': lost_cases,
        'found_cases': found_cases,
        'blogs': blogs,
        'total_cases': Case.objects.count(),
        'solved_cases': Case.objects.filter(status='RESOLVED').count(),
    }
    return render(request, 'lostfound/home.html', context)


def cases_list_view(request):
    case_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', 'OPEN')
    
    cases = Case.objects.all()
    
    if case_type:
        cases = cases.filter(case_type=case_type)
    if category:
        cases = cases.filter(category=category)
    if status:
        cases = cases.filter(status=status)
    
    paginator = Paginator(cases.order_by('-created_at'), 12)
    page = request.GET.get('page', 1)
    cases_page = paginator.get_page(page)
    
    context = {
        'cases': cases_page,
        'case_type': case_type,
        'category': category,
        'status': status,
    }
    return render(request, 'lostfound/cases_list.html', context)


def case_detail_view(request, pk):
    case = get_object_or_404(Case, pk=pk)
    images = case.images.all()
    sightings = case.sightings.all()
    assignments = case.assignments.all()
    
    # Get investigation updates for this case
    updates = []
    for assignment in assignments:
        updates.extend(assignment.updates.all())
    updates = sorted(updates, key=lambda x: x.created_at, reverse=True)
    
    context = {
        'case': case,
        'images': images,
        'sightings': sightings,
        'updates': updates,
        'assignments': assignments,
    }
    return render(request, 'lostfound/case_detail.html', context)


def blog_list_view(request):
    blogs = Blog.objects.filter(published=True).order_by('-created_at')
    paginator = Paginator(blogs, 9)
    page = request.GET.get('page', 1)
    blogs_page = paginator.get_page(page)
    
    context = {'blogs': blogs_page}
    return render(request, 'lostfound/blog_list.html', context)


def blog_detail_view(request, slug):
    blog = get_object_or_404(Blog, slug=slug)
    context = {'blog': blog}
    return render(request, 'lostfound/blog_detail.html', context)


def map_view(request):
    lost_cases = Case.objects.filter(
        case_type='LOST',
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'title', 'case_type', 'latitude', 'longitude', 'reward_amount')
    
    found_cases = Case.objects.filter(
        case_type='FOUND',
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'title', 'case_type', 'latitude', 'longitude', 'reward_amount')
    
    context = {
        'lost_cases': list(lost_cases),
        'found_cases': list(found_cases),
    }
    return render(request, 'lostfound/map.html', context)


# ============== AI SEARCH VIEW ==============

def ai_search_view(request):
    results = []
    query_image = None
    
    if request.method == 'POST' and request.FILES.get('query_image'):
        query_image = request.FILES['query_image']
        
        # Save temporarily
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp_query.jpg')
        with open(temp_path, 'wb+') as destination:
            for chunk in query_image.chunks():
                destination.write(chunk)
        
        # Search
        search_results = search_similar_images(temp_path, top_k=10)
        
        # Get case details for results
        for result in search_results:
            case = Case.objects.filter(pk=result['case_id']).first()
            if case:
                result['case'] = case
                primary_image = case.images.filter(is_primary=True).first() or case.images.first()
                result['image_url'] = primary_image.image.url if primary_image else None
        
        results = search_results
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    context = {'results': results, 'query_image': query_image}
    return render(request, 'lostfound/ai_search.html', context)


# ============== USER CASE MANAGEMENT ==============

@login_required
def create_case_view(request):
    if request.method == 'POST':
        profile = request.user.profile
        
        case_type = request.POST.get('case_type', '')
        category = request.POST.get('category', '')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        last_seen_location = request.POST.get('last_seen_location', '').strip()
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        date = request.POST.get('date', '')
        reward_amount = request.POST.get('reward_amount', '0') or '0'
        contact_phone = request.POST.get('contact_phone', profile.phone)
        
        if not all([case_type, category, title, description, last_seen_location, date]):
            messages.error(request, "All required fields must be filled.")
            return redirect('create_case')
        
        case = Case.objects.create(
            owner=profile,
            case_type=case_type,
            category=category,
            title=title,
            description=description,
            last_seen_location=last_seen_location,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            date=date,
            reward_amount=reward_amount,
            contact_phone=contact_phone,
        )
        
        # Update profile cases posted count
        profile.cases_posted += 1
        profile.save()
        
        # Handle image uploads
        images = request.FILES.getlist('images')
        for i, img in enumerate(images):
            case_image = CaseImage.objects.create(
                case=case,
                image=img,
                is_primary=(i == 0)
            )
            # Generate and store embedding
            try:
                add_to_index(img.file.name, case.id, case_image.id)
                # Store embedding in DB as well
                from .ai_engine import generate_embedding
                emb = generate_embedding(img.file.name)
                if emb:
                    case_image.clip_embedding = emb
                    case_image.save()
            except Exception as e:
                print(f"Error generating embedding: {e}")
        
        messages.success(request, "Case created successfully!")
        return redirect('case_detail', pk=case.pk)
    
    return render(request, 'lostfound/create_case.html')


@login_required
def submit_sighting_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    
    if request.method == 'POST':
        profile = request.user.profile
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        image = request.FILES.get('image')
        
        if not description or not location:
            messages.error(request, "Description and location are required.")
            return redirect('case_detail', pk=case_pk)
        
        SightingReport.objects.create(
            case=case,
            reporter=profile,
            description=description,
            location=location,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            image=image
        )
        
        messages.success(request, "Sighting report submitted successfully!")
        return redirect('case_detail', pk=case_pk)
    
    return redirect('case_detail', pk=case_pk)


@login_required
def request_detective_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    
    if request.method == 'POST':
        profile = request.user.profile
        message = request.POST.get('message', '').strip()
        
        if not message:
            messages.error(request, "Message is required.")
            return redirect('case_detail', pk=case_pk)
        
        DetectiveRequest.objects.create(
            case=case,
            requested_by=profile,
            message=message
        )
        
        messages.success(request, "Detective request submitted!")
        return redirect('case_detail', pk=case_pk)
    
    return redirect('case_detail', pk=case_pk)


# ============== DETECTIVE VIEWS ==============

@login_required
def apply_detective_view(request):
    if request.method == 'POST':
        profile = request.user.profile
        experience_years = request.POST.get('experience_years', 0)
        photo = request.FILES.get('photo')
        govt_id = request.FILES.get('govt_id')
        address_proof = request.FILES.get('address_proof')
        certificates = request.FILES.get('certificates')
        
        if not all([photo, govt_id, address_proof]):
            messages.error(request, "Photo, Govt ID, and Address Proof are required.")
            return redirect('apply_detective')
        
        DetectiveApplication.objects.create(
            user=profile,
            experience_years=experience_years,
            photo=photo,
            govt_id=govt_id,
            address_proof=address_proof,
            certificates=certificates
        )
        
        messages.success(request, "Application submitted for review!")
        return redirect('dashboard')
    
    return render(request, 'lostfound/apply_detective.html')


@login_required
def detective_dashboard_view(request):
    if not request.user.profile.is_detective:
        messages.error(request, "You are not a verified detective.")
        return redirect('home')
    
    assignments = CaseAssignment.objects.filter(
        detective=request.user.profile,
        status='ACTIVE'
    )
    
    context = {'assignments': assignments}
    return render(request, 'lostfound/detective_dashboard.html', context)


@login_required
def add_investigation_update_view(request, assignment_pk):
    assignment = get_object_or_404(CaseAssignment, pk=assignment_pk)
    
    if request.user.profile != assignment.detective:
        messages.error(request, "Access denied.")
        return redirect('detective_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        milestone = request.POST.get('milestone', 'STARTED')
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        image = request.FILES.get('image')
        
        if not title or not description:
            messages.error(request, "Title and description are required.")
            return redirect('add_update', pk=assignment_pk)
        
        InvestigationUpdate.objects.create(
            assignment=assignment,
            title=title,
            description=description,
            milestone=milestone,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            image=image
        )
        
        messages.success(request, "Investigation update added!")
        return redirect('detective_dashboard')
    
    return render(request, 'lostfound/add_update.html', {'assignment': assignment})


# ============== ADMIN VIEWS ==============

@login_required
def admin_dashboard_view(request):
    if not request.user.profile.role == 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    total_users = Profile.objects.count()
    total_cases = Case.objects.count()
    solved_cases = Case.objects.filter(status='RESOLVED').count()
    pending_applications = DetectiveApplication.objects.filter(status='PENDING').count()
    
    applications = DetectiveApplication.objects.filter(status='PENDING')
    
    context = {
        'total_users': total_users,
        'total_cases': total_cases,
        'solved_cases': solved_cases,
        'pending_applications': pending_applications,
        'applications': applications,
    }
    return render(request, 'lostfound/admin_dashboard.html', context)


@login_required
def approve_detective_view(request, app_pk):
    if not request.user.profile.role == 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    application = get_object_or_404(DetectiveApplication, pk=app_pk)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'approve':
            application.status = 'APPROVED'
            application.user.is_detective = True
            application.user.detective_verified = True
            application.user.role = 'DETECTIVE'
            application.user.save()
            application.save()
            messages.success(request, "Detective application approved!")
        elif action == 'reject':
            application.status = 'REJECTED'
            application.save()
            messages.info(request, "Detective application rejected.")
        
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@login_required
def assign_detective_view(request, case_pk):
    if not request.user.profile.role == 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    case = get_object_or_404(Case, pk=case_pk)
    detectives = Profile.objects.filter(is_detective=True, detective_verified=True)
    
    if request.method == 'POST':
        detective_id = request.POST.get('detective_id')
        
        if detective_id:
            detective = get_object_or_404(Profile, pk=detective_id)
            CaseAssignment.objects.create(
                case=case,
                detective=detective,
                assigned_by=request.user
            )
            case.status = 'UNDER_INVESTIGATION'
            case.save()
            messages.success(request, "Detective assigned successfully!")
        else:
            messages.error(request, "Please select a detective.")
        
        return redirect('admin_dashboard')
    
    context = {'case': case, 'detectives': detectives}
    return render(request, 'lostfound/assign_detective.html', context)


@login_required
def create_blog_view(request):
    if not request.user.profile.role == 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'SAFETY')
        cover_image = request.FILES.get('cover_image')
        published = request.POST.get('published') == 'on'
        
        if not title or not content or not cover_image:
            messages.error(request, "Title, content, and cover image are required.")
            return redirect('create_blog')
        
        slug = slugify(title)
        if Blog.objects.filter(slug=slug).exists():
            slug = f"{slug}-{request.user.id}"
        
        Blog.objects.create(
            author=request.user.profile,
            title=title,
            slug=slug,
            content=content,
            category=category,
            cover_image=cover_image,
            published=published
        )
        
        messages.success(request, "Blog post created!")
        return redirect('blog_list')
    
    return render(request, 'lostfound/create_blog.html')


# ============== PROFILE VIEWS ==============

@login_required
def profile_view(request):
    profile = request.user.profile
    cases = profile.cases.all()
    notifications = profile.notifications.filter(is_read=False)
    
    context = {
        'profile': profile,
        'cases': cases,
        'notifications': notifications,
    }
    return render(request, 'lostfound/profile.html', context)


@login_required
def edit_profile_view(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        district = request.POST.get('district', '').strip()
        bio = request.POST.get('bio', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        profile.phone = phone
        profile.address = address
        profile.city = city
        profile.state = state
        profile.country = country
        profile.district = district
        profile.bio = bio
        
        if profile_picture:
            profile.profile_picture = profile_picture
        
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    
    return render(request, 'lostfound/edit_profile.html', {'profile': profile})


@login_required
def dashboard_view(request):
    profile = request.user.profile
    cases = profile.cases.all()
    notifications = profile.notifications.order_by('-created_at')[:10]
    
    context = {
        'profile': profile,
        'cases': cases,
        'notifications': notifications,
    }
    return render(request, 'lostfound/dashboard.html', context)


# ============== API ENDPOINTS ==============

@require_http_methods(["GET"])
def cases_api(request):
    case_type = request.GET.get('type', '')
    cases = Case.objects.all()
    
    if case_type:
        cases = cases.filter(case_type=case_type)
    
    data = []
    for case in cases[:50]:  # Limit to 50
        primary_image = case.images.filter(is_primary=True).first()
        data.append({
            'id': case.id,
            'title': case.title,
            'case_type': case.case_type,
            'category': case.category,
            'status': case.status,
            'location': case.last_seen_location,
            'latitude': str(case.latitude) if case.latitude else None,
            'longitude': str(case.longitude) if case.longitude else None,
            'reward': str(case.reward_amount),
            'image_url': primary_image.image.url if primary_image else None,
            'created_at': case.created_at.isoformat(),
        })
    
    return JsonResponse({'cases': data})
