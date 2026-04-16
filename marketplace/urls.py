from django.urls import path
from . import views

urlpatterns = [
    path('', views.listing_list, name='listing_list'),
    path('create/', views.create_listing, name='create_listing'),
    path('mine/', views.my_listings, name='my_listings'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('messages/<int:other_pk>/', views.message_thread, name='message_thread'),
    path('messages/<int:other_pk>/<int:listing_pk>/', views.message_thread, name='message_thread_listing'),
    path('<int:pk>/', views.listing_detail, name='listing_detail'),
    path('<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('<int:pk>/delete/', views.delete_listing, name='delete_listing'),
    path('<int:pk>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('<int:listing_pk>/message/', views.send_message, name='send_message'),
]
