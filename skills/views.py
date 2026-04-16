from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import SkillCategory, Skill, Booking, Review
from .forms import SkillForm, BookingForm, ReviewForm, SkillFilterForm


def skill_list(request):
    qs = Skill.objects.filter(is_active=True).select_related('provider', 'category').prefetch_related('reviews')

    # Restrict to same university when the viewer belongs to one
    user_university = None
    if request.user.is_authenticated and request.user.university_id:
        user_university = request.user.university
        qs = qs.filter(provider__university=user_university)

    form = SkillFilterForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category_slug = form.cleaned_data.get('category')
        delivery = form.cleaned_data.get('delivery_method')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if delivery:
            qs = qs.filter(delivery_method=delivery)
        if min_price:
            qs = qs.filter(max_price__gte=min_price)
        if max_price:
            qs = qs.filter(min_price__lte=max_price)

    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = SkillCategory.objects.filter(slug=category_slug).first()

    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    skills = paginator.get_page(page)
    categories = SkillCategory.objects.all()

    return render(request, 'skills/skill_list.html', {
        'skills': skills,
        'categories': categories,
        'selected_category': selected_category,
        'form': form,
        'user_university': user_university,
    })


def skill_detail(request, pk):
    skill = get_object_or_404(Skill, pk=pk, is_active=True)

    # Block cross-university access
    if request.user.is_authenticated and request.user.university_id:
        if skill.provider.university_id != request.user.university_id:
            from django.http import Http404
            raise Http404

    related = Skill.objects.filter(category=skill.category, is_active=True).exclude(pk=pk)
    if request.user.is_authenticated and request.user.university_id:
        related = related.filter(provider__university=request.user.university)
    related = related[:3]
    reviews = skill.reviews.select_related('reviewer').order_by('-created_at')
    return render(request, 'skills/skill_detail.html', {
        'skill': skill,
        'related': related,
        'reviews': reviews,
    })


@login_required
def create_skill(request):
    if not request.user.can_create_skill:
        messages.error(request, "You've reached the free tier limit of 2 skill offerings. Upgrade to Pro for unlimited skills.")
        return redirect('skill_list')

    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.provider = request.user
            skill.save()
            messages.success(request, "Skill listing created!")
            return redirect('skill_detail', pk=skill.pk)
    else:
        form = SkillForm()
    return render(request, 'skills/create_skill.html', {'form': form})


@login_required
def edit_skill(request, pk):
    skill = get_object_or_404(Skill, pk=pk, provider=request.user)
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, "Skill updated!")
            return redirect('skill_detail', pk=skill.pk)
    else:
        form = SkillForm(instance=skill)
    return render(request, 'skills/edit_skill.html', {'form': form, 'skill': skill})


@login_required
def delete_skill(request, pk):
    skill = get_object_or_404(Skill, pk=pk, provider=request.user)
    if request.method == 'POST':
        skill.is_active = False
        skill.save()
        messages.success(request, "Skill removed.")
        return redirect('my_skills')
    return render(request, 'skills/delete_skill.html', {'skill': skill})


@login_required
def my_skills(request):
    skills = request.user.skills.filter(is_active=True).order_by('-created_at')
    return render(request, 'skills/my_skills.html', {'skills': skills})


@login_required
def book_session(request, pk):
    skill = get_object_or_404(Skill, pk=pk, is_active=True)
    if skill.provider == request.user:
        messages.error(request, "You cannot book your own skill.")
        return redirect('skill_detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.skill = skill
            booking.client = request.user
            booking.provider = skill.provider
            booking.save()
            messages.success(request, f"Booking request sent to {skill.provider.get_full_name()}!")
            return redirect('my_bookings')
    else:
        form = BookingForm(initial={'agreed_price': skill.min_price})
    return render(request, 'skills/book_session.html', {'skill': skill, 'form': form})


@login_required
def my_bookings(request):
    bookings_client = request.user.bookings_as_client.select_related('skill', 'provider').order_by('-created_at')
    bookings_provider = request.user.bookings_as_provider.select_related('skill', 'client').order_by('-created_at')
    return render(request, 'skills/my_bookings.html', {
        'bookings_client': bookings_client,
        'bookings_provider': bookings_provider,
    })


@login_required
def update_booking_status(request, pk, action):
    booking = get_object_or_404(Booking, pk=pk)
    allowed_actions = {
        'confirm': ('provider', 'Pending', 'Confirmed'),
        'complete': ('provider', 'Confirmed', 'Completed'),
        'cancel': (None, None, 'Cancelled'),
        'dispute': (None, None, 'Disputed'),
    }

    if action not in allowed_actions:
        messages.error(request, "Invalid action.")
        return redirect('my_bookings')

    role, required_status, new_status = allowed_actions[action]

    if role == 'provider' and booking.provider != request.user:
        messages.error(request, "Permission denied.")
        return redirect('my_bookings')
    if role is None and request.user not in [booking.client, booking.provider]:
        messages.error(request, "Permission denied.")
        return redirect('my_bookings')
    if required_status and booking.status != required_status:
        messages.error(request, f"Booking must be {required_status} to perform this action.")
        return redirect('my_bookings')

    booking.status = new_status
    booking.save()
    messages.success(request, f"Booking marked as {new_status}.")
    return redirect('my_bookings')


@login_required
def leave_review(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk, client=request.user, status='Completed')
    if hasattr(booking, 'review'):
        messages.info(request, "You've already reviewed this booking.")
        return redirect('my_bookings')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.reviewer = request.user
            review.skill = booking.skill
            review.save()
            messages.success(request, "Review submitted!")
            return redirect('skill_detail', pk=booking.skill.pk)
    else:
        form = ReviewForm()
    return render(request, 'skills/leave_review.html', {'form': form, 'booking': booking})
