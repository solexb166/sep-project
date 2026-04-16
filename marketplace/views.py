from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Category, Listing, ListingImage, Wishlist, Message
from .forms import ListingForm, MessageForm, ListingFilterForm


def listing_list(request):
    qs = Listing.objects.filter(is_active=True, is_sold=False, is_flagged=False).select_related('seller', 'category').prefetch_related('images')

    # Restrict to same university when the viewer belongs to one
    user_university = None
    if request.user.is_authenticated and request.user.university_id:
        user_university = request.user.university
        qs = qs.filter(seller__university=user_university)

    form = ListingFilterForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category_slug = form.cleaned_data.get('category')
        condition = form.cleaned_data.get('condition')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort = form.cleaned_data.get('sort') or '-created_at'

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if condition:
            qs = qs.filter(condition=condition)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        qs = qs.order_by(sort)
    else:
        qs = qs.order_by('-created_at')

    # Category filter from GET param
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        qs = qs.filter(category__slug=category_slug)

    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    listings = paginator.get_page(page)
    categories = Category.objects.all()

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True))

    return render(request, 'marketplace/listing_list.html', {
        'listings': listings,
        'categories': categories,
        'selected_category': selected_category,
        'form': form,
        'wishlist_ids': wishlist_ids,
        'user_university': user_university,
    })


def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk, is_active=True, is_flagged=False)

    # Block cross-university access
    if request.user.is_authenticated and request.user.university_id:
        if listing.seller.university_id != request.user.university_id:
            from django.http import Http404
            raise Http404

    # Increment view count
    Listing.objects.filter(pk=pk).update(views_count=listing.views_count + 1)
    listing.refresh_from_db()

    related_qs = Listing.objects.filter(
        category=listing.category, is_active=True, is_sold=False, is_flagged=False
    ).exclude(pk=pk)
    # Keep related within the same university
    if request.user.is_authenticated and request.user.university_id:
        related_qs = related_qs.filter(seller__university=request.user.university)
    related = related_qs[:4]

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, listing=listing).exists()

    message_form = MessageForm()
    return render(request, 'marketplace/listing_detail.html', {
        'listing': listing,
        'related': related,
        'is_wishlisted': is_wishlisted,
        'message_form': message_form,
    })


@login_required
def create_listing(request):
    if not request.user.can_create_listing:
        messages.error(request, "You've reached the free tier limit of 3 active listings. Upgrade to Pro for unlimited listings.")
        return redirect('listing_list')

    if request.method == 'POST':
        form = ListingForm(request.POST)
        images = request.FILES.getlist('images')

        if not images:
            messages.error(request, "Please upload at least one image.")
        elif len(images) > 5:
            messages.error(request, "You can upload a maximum of 5 images.")
        elif form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()

            for i, img in enumerate(images):
                ListingImage.objects.create(
                    listing=listing,
                    image=img,
                    is_primary=(i == 0),
                    order=i
                )
            messages.success(request, "Listing created successfully!")
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ListingForm()

    return render(request, 'marketplace/create_listing.html', {'form': form})


@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        new_images = request.FILES.getlist('images')
        if form.is_valid():
            form.save()
            if new_images:
                existing_count = listing.images.count()
                for i, img in enumerate(new_images):
                    if existing_count + i < 5:
                        ListingImage.objects.create(
                            listing=listing,
                            image=img,
                            order=existing_count + i
                        )
            messages.success(request, "Listing updated successfully!")
            return redirect('listing_detail', pk=listing.pk)
    else:
        form = ListingForm(instance=listing)

    return render(request, 'marketplace/edit_listing.html', {'form': form, 'listing': listing})


@login_required
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        listing.is_active = False
        listing.save()
        messages.success(request, "Listing deleted successfully.")
        return redirect('my_listings')
    return render(request, 'marketplace/delete_listing.html', {'listing': listing})


@login_required
def my_listings(request):
    listings = request.user.listings.filter(is_active=True).order_by('-created_at')
    return render(request, 'marketplace/my_listings.html', {'listings': listings})


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related('listing').order_by('-created_at')
    return render(request, 'marketplace/wishlist.html', {'items': items})


@login_required
@require_POST
def toggle_wishlist(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


@login_required
def messages_inbox(request):
    user = request.user
    # Get all conversations: unique (other_user, listing) pairs
    sent = Message.objects.filter(sender=user).select_related('receiver', 'listing')
    received = Message.objects.filter(receiver=user).select_related('sender', 'listing')

    conversations = {}
    for msg in list(sent) + list(received):
        other = msg.receiver if msg.sender == user else msg.sender
        key = (other.pk, msg.listing_id)
        if key not in conversations or conversations[key].created_at < msg.created_at:
            conversations[key] = msg

    conversation_list = sorted(conversations.values(), key=lambda m: m.created_at, reverse=True)
    return render(request, 'marketplace/messages_inbox.html', {'conversations': conversation_list})


@login_required
def message_thread(request, other_pk, listing_pk=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    other_user = get_object_or_404(User, pk=other_pk)
    listing = None
    if listing_pk:
        listing = get_object_or_404(Listing, pk=listing_pk)

    thread = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    )
    if listing:
        thread = thread.filter(listing=listing)
    thread = thread.order_by('created_at')

    # Mark received messages as read
    thread.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        if not request.user.can_send_message:
            messages.error(request, "You've reached your daily message limit (15). Upgrade to Pro for unlimited messages.")
            return redirect('message_thread', other_pk=other_pk)

        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.listing = listing
            msg.save()
            if listing_pk:
                return redirect('message_thread_listing', other_pk=other_pk, listing_pk=listing_pk)
            return redirect('message_thread', other_pk=other_pk)
    else:
        form = MessageForm()

    return render(request, 'marketplace/message_thread.html', {
        'other_user': other_user,
        'thread': thread,
        'listing': listing,
        'form': form,
    })


@login_required
def send_message(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    if listing.seller == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect('listing_detail', pk=listing_pk)

    if not request.user.can_send_message:
        messages.error(request, "You've reached your daily message limit. Upgrade to Pro.")
        return redirect('listing_detail', pk=listing_pk)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = listing.seller
            msg.listing = listing
            msg.save()
            messages.success(request, "Message sent!")
            return redirect('message_thread_listing', other_pk=listing.seller.pk, listing_pk=listing_pk)
    return redirect('listing_detail', pk=listing_pk)
