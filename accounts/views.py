from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView
from .models import CustomUser
from .forms import RegisterForm, LoginForm, EditProfileForm, VerificationForm, ContactForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.first_name}! Please verify your student ID to unlock all features.")
            return redirect('verify')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


def profile_view(request, pk):
    profile_user = get_object_or_404(CustomUser, pk=pk)
    listings = profile_user.listings.filter(is_active=True, is_sold=False, is_flagged=False).order_by('-created_at')[:6]
    skills = profile_user.skills.filter(is_active=True).order_by('-created_at')[:6]
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'listings': listings,
        'skills': skills,
    })


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile', pk=request.user.pk)
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def verify_view(request):
    user = request.user
    if user.is_verified:
        messages.info(request, "Your account is already verified!")
        return redirect('dashboard')
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Verification documents submitted! We'll review them shortly.")
            return redirect('dashboard')
    else:
        form = VerificationForm(instance=user)
    verification_submitted = bool(user.student_id_photo and user.selfie_photo)
    return render(request, 'accounts/verify.html', {
        'form': form,
        'verification_submitted': verification_submitted
    })


def home_view(request):
    from marketplace.models import Listing
    from skills.models import Skill, SkillCategory
    from marketplace.models import Category

    # Determine university scope for the current viewer
    user_university = None
    if request.user.is_authenticated and request.user.university_id:
        user_university = request.user.university

    verified_students = CustomUser.objects.filter(is_verified=True).count()

    listing_base = Listing.objects.filter(is_active=True, is_sold=False, is_flagged=False)
    skill_base = Skill.objects.filter(is_active=True)
    if user_university:
        listing_base = listing_base.filter(seller__university=user_university)
        skill_base = skill_base.filter(provider__university=user_university)

    active_listings_count = listing_base.count()
    skill_offerings_count = skill_base.count()

    featured_listings = listing_base.select_related('seller', 'category').prefetch_related('images').order_by('-created_at')[:6]
    featured_skills = skill_base.select_related('provider', 'category').order_by('-created_at')[:4]

    marketplace_categories = Category.objects.all()[:8]
    skill_categories = SkillCategory.objects.all()[:8]

    return render(request, 'home.html', {
        'verified_students': verified_students,
        'active_listings_count': active_listings_count,
        'skill_offerings_count': skill_offerings_count,
        'featured_listings': featured_listings,
        'featured_skills': featured_skills,
        'marketplace_categories': marketplace_categories,
        'skill_categories': skill_categories,
        'user_university': user_university,
    })


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            from support.models import Ticket
            ticket = Ticket(
                email=form.cleaned_data['email'],
                category=form.cleaned_data['category'],
                subject=form.cleaned_data['subject'],
                description=form.cleaned_data['message'],
            )
            if request.user.is_authenticated:
                ticket.user = request.user
                ticket.email = request.user.email
            ticket.save()
            messages.success(request, f"Your message has been received. Ticket {ticket.ticket_number} created.")
            return redirect('contact')
    else:
        form = ContactForm()
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
    return render(request, 'contact.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user
    listings = user.listings.filter(is_active=True).order_by('-created_at')[:5]
    skills = user.skills.filter(is_active=True).order_by('-created_at')[:5]
    bookings_as_client = user.bookings_as_client.order_by('-created_at')[:5]
    bookings_as_provider = user.bookings_as_provider.order_by('-created_at')[:5]
    tickets = []
    if user.is_authenticated:
        from support.models import Ticket
        tickets = Ticket.objects.filter(user=user).order_by('-created_at')[:5]
    unread_messages = user.received_messages.filter(is_read=False).count()
    return render(request, 'accounts/dashboard.html', {
        'listings': listings,
        'skills': skills,
        'bookings_as_client': bookings_as_client,
        'bookings_as_provider': bookings_as_provider,
        'tickets': tickets,
        'unread_messages': unread_messages,
    })
