from django.urls import path
from . import views

urlpatterns = [
    path('', views.skill_list, name='skill_list'),
    path('create/', views.create_skill, name='create_skill'),
    path('mine/', views.my_skills, name='my_skills'),
    path('<int:pk>/', views.skill_detail, name='skill_detail'),
    path('<int:pk>/edit/', views.edit_skill, name='edit_skill'),
    path('<int:pk>/delete/', views.delete_skill, name='delete_skill'),
    path('<int:pk>/book/', views.book_session, name='book_session'),
]

bookings_urlpatterns = [
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:pk>/<str:action>/', views.update_booking_status, name='update_booking_status'),
    path('bookings/<int:booking_pk>/review/', views.leave_review, name='leave_review'),
]

urlpatterns += bookings_urlpatterns
