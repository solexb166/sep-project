import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_ticket_number():
    today = timezone.now().strftime('%Y%m%d')
    last = Ticket.objects.filter(ticket_number__startswith=f'TKT-{today}').order_by('-ticket_number').first()
    if last:
        try:
            seq = int(last.ticket_number.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f'TKT-{today}-{seq:03d}'


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('Bug Report', 'Bug Report'),
        ('Payment Issue', 'Payment Issue'),
        ('Account Problem', 'Account Problem'),
        ('Listing Report', 'Listing Report'),
        ('Skill Report', 'Skill Report'),
        ('Scam/Fraud', 'Scam/Fraud'),
        ('Stolen Item', 'Stolen Item'),
        ('Dispute', 'Dispute'),
        ('General Query', 'General Query'),
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    ticket_number = models.CharField(max_length=30, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets'
    )
    email = models.EmailField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    reported_listing = models.ForeignKey(
        'marketplace.Listing', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets'
    )
    reported_skill = models.ForeignKey(
        'skills.Skill', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets'
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reports_against'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'is_staff': True}
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number}: {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = generate_ticket_number()
        # Auto-set priority for urgent categories
        if self.category in ('Scam/Fraud', 'Stolen Item'):
            self.priority = 'Urgent'
        super().save(*args, **kwargs)


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='thread')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    sender_name = models.CharField(max_length=100)
    message = models.TextField()
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender_name} on {self.ticket.ticket_number}"


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    page_url = models.CharField(max_length=500, blank=True)
    messages_json = models.JSONField(default=list)

    def __str__(self):
        return f"Session {self.session_id}"

    @property
    def message_count(self):
        return len(self.messages_json)
