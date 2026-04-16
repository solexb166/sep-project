from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chatbot_api, name='chatbot_api'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<str:ticket_number>/', views.ticket_detail, name='ticket_detail'),
]
