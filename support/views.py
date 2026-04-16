import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from .models import Ticket, TicketMessage, ChatSession

SEP_SYSTEM_PROMPT = """You are SEP Bot, the support assistant for SEP — a campus marketplace for university students in Uganda.

PLATFORM KNOWLEDGE:
- Marketplace: Students sell used goods (textbooks, electronics, clothing, furniture, sports gear, stationery, food) priced in UGX. Listings expire after 30 days.
- Skills Exchange: Students offer skills (tutoring, IT, design, writing, photography, music, languages, business, fitness) and charge per session in UGX.
- Free tier: 3 listings, 2 skill offerings, 15 messages/day. Pro tier: UGX 5,000/month (MTN or Airtel MoMo) — unlimited everything.
- Registration: Sign up → upload student ID + selfie → admin verifies → verified badge on profile.
- Messaging: In-app only. No personal contacts needed.
- Payments: Off-platform via Mobile Money. Listings show only to students from the same university.
- Universities: Cavendish, Makerere, KIU, UCU, Kyambogo.

RESPONSE RULES — follow these strictly:
- Give short, direct answers. 1–3 sentences maximum unless absolutely necessary.
- Never use bullet points, numbered lists, or markdown formatting.
- No greetings or sign-offs in every message. Get straight to the answer.
- Plain conversational text only — like a helpful friend texting back.
- If unsure, say so briefly and offer to open a support ticket.
- For reports: ask what the issue is, collect details, confirm, then create the ticket."""


def get_or_create_session(session_id_str, user, page_url):
    if session_id_str:
        try:
            session = ChatSession.objects.get(session_id=uuid.UUID(session_id_str))
            return session
        except (ChatSession.DoesNotExist, ValueError):
            pass
    session = ChatSession.objects.create(
        user=user if (user and user.is_authenticated) else None,
        page_url=page_url or ''
    )
    return session


@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = data.get('message', '').strip()
    session_id_str = data.get('session_id', '')
    page_url = data.get('page_url', '')
    context = data.get('context', {})

    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    # Rate limiting
    user = request.user if request.user.is_authenticated else None
    if user:
        today_sessions = ChatSession.objects.filter(user=user, started_at__date=timezone.now().date())
        total_today = sum(len(s.messages_json) for s in today_sessions)
        if total_today >= 100:
            return JsonResponse({'reply': 'You have reached your daily chat limit of 100 messages. Please try again tomorrow.', 'session_id': session_id_str}, status=200)

    session = get_or_create_session(session_id_str, request.user, page_url)

    # Session message limit
    if len(session.messages_json) >= 60:
        return JsonResponse({'reply': 'This chat session has reached its message limit. Please refresh to start a new session.', 'session_id': str(session.session_id)}, status=200)

    # Build message history for Claude
    history = session.messages_json.copy()

    # Handle report context
    action = context.get('action', '')
    ticket_created = None

    if action == 'report' and not history:
        listing_title = context.get('listing_title', 'this item')
        skill_title = context.get('skill_title', '')
        seller = context.get('seller', '')
        item_desc = f"listing '{listing_title}'" if listing_title else f"skill '{skill_title}'"
        intro = f"I see you want to report the {item_desc}. Could you tell me what the issue is?"
        history.append({'role': 'assistant', 'content': intro})
        session.messages_json = history
        session.save()
        return JsonResponse({
            'reply': intro,
            'session_id': str(session.session_id),
            'ticket_created': None,
            'quick_actions': ['Stolen Item', 'Scam/Fraud', 'Inappropriate Content', 'Wrong Information', 'Other']
        })

    # Add user message to history
    history.append({'role': 'user', 'content': user_message})

    # Check if this is a report confirmation
    if _is_report_confirmation(user_message, history, context):
        ticket_created = _create_report_ticket(request.user, context, history, session)

    # Call Claude API
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        claude_messages = [{'role': m['role'], 'content': m['content']} for m in history if m.get('role') in ('user', 'assistant')]

        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=200,
            system=SEP_SYSTEM_PROMPT,
            messages=claude_messages
        )
        bot_reply = response.content[0].text
    except Exception as e:
        bot_reply = "I'm having trouble connecting right now. Please try again or use the contact form."

    history.append({'role': 'assistant', 'content': bot_reply})
    session.messages_json = history
    session.save()

    return JsonResponse({
        'reply': bot_reply,
        'session_id': str(session.session_id),
        'ticket_created': ticket_created,
    })


def _is_report_confirmation(message, history, context):
    keywords = ['yes', 'proceed', 'confirm', 'create ticket', 'submit', 'go ahead']
    msg_lower = message.lower()
    if context.get('action') == 'report' and any(k in msg_lower for k in keywords):
        # Check if bot asked for confirmation in last assistant message
        for m in reversed(history):
            if m.get('role') == 'assistant' and 'should i proceed' in m.get('content', '').lower():
                return True
    return False


def _create_report_ticket(user, context, history, session):
    from marketplace.models import Listing
    from skills.models import Skill

    listing_id = context.get('listing_id')
    skill_id = context.get('skill_id')
    listing_title = context.get('listing_title', '')
    skill_title = context.get('skill_title', '')
    seller = context.get('seller', '')

    # Determine category from conversation
    category = 'Listing Report' if listing_id else 'Skill Report'
    for m in history:
        content = m.get('content', '').lower()
        if 'stolen' in content:
            category = 'Stolen Item'
            break
        elif 'scam' in content or 'fraud' in content:
            category = 'Scam/Fraud'
            break

    subject = f"Report: {listing_title or skill_title or 'Item'}"
    description = '\n'.join([f"{m['role'].title()}: {m['content']}" for m in history if m.get('role') in ('user', 'assistant')])

    ticket = Ticket(
        category=category,
        subject=subject,
        description=description,
        email=user.email if user and user.is_authenticated else 'anonymous@sep.ug',
    )
    if user and user.is_authenticated:
        ticket.user = user

    if listing_id:
        try:
            listing_obj = Listing.objects.get(pk=listing_id)
            ticket.reported_listing = listing_obj
            listing_obj.is_flagged = True
            listing_obj.save()
        except Listing.DoesNotExist:
            pass

    if skill_id:
        try:
            ticket.reported_skill = Skill.objects.get(pk=skill_id)
        except Skill.DoesNotExist:
            pass

    ticket.save()

    return {'ticket_number': ticket.ticket_number, 'ticket_id': ticket.pk}


@login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'support/ticket_list.html', {'tickets': tickets})


@login_required
def ticket_detail(request, ticket_number):
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number, user=request.user)
    thread = ticket.thread.all()

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                sender_name=request.user.get_full_name(),
                message=message_text,
                is_bot=False
            )
            messages.success(request, "Reply added.")
            return redirect('ticket_detail', ticket_number=ticket_number)

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'thread': thread,
    })
