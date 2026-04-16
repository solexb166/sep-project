/**
 * SEP Chatbot Widget
 * Floating AI support widget powered by Claude API
 */
(function () {
    'use strict';

    const cfg = window.SEP_CHATBOT_CONFIG || {};
    const API_URL = cfg.apiUrl || '/support/api/chat/';
    const CSRF_TOKEN = cfg.csrfToken || '';
    const USER_NAME = cfg.userName || 'You';
    const STORAGE_KEY = 'sep_chat_session';

    let sessionId = null;
    let isOpen = false;
    let isTyping = false;
    let reportContext = null;

    // DOM refs
    const toggle = document.getElementById('chatbot-toggle');
    const panel = document.getElementById('chatbot-panel');
    const messagesEl = document.getElementById('chatbot-messages');
    const typingEl = document.getElementById('chatbot-typing');
    const quickActions = document.getElementById('chatbot-quick-actions');
    const form = document.getElementById('chatbot-form');
    const inputEl = document.getElementById('chatbot-input-field');
    const sendBtn = document.getElementById('chatbot-send');
    const minimizeBtn = document.getElementById('chatbot-minimize');
    const closeBtn = document.getElementById('chatbot-close');
    const chatIcon = document.getElementById('chat-icon');
    const closeIcon = document.getElementById('close-icon');

    if (!toggle) return; // Widget not present

    // ── Draggable toggle button ──────────────────────────────────────
    (function makeDraggable() {
        let startX, startY, startLeft, startBottom;
        let dragged = false;

        function getPos() {
            const rect = toggle.getBoundingClientRect();
            return {
                left: rect.left,
                bottom: window.innerHeight - rect.bottom
            };
        }

        function clamp(val, min, max) { return Math.min(Math.max(val, min), max); }

        function onMove(clientX, clientY) {
            const dx = clientX - startX;
            const dy = clientY - startY;
            if (Math.abs(dx) > 4 || Math.abs(dy) > 4) dragged = true;
            if (!dragged) return;

            const newLeft = clamp(startLeft + dx, 8, window.innerWidth - toggle.offsetWidth - 8);
            const newBottom = clamp(startBottom - dy, 8, window.innerHeight - toggle.offsetHeight - 8);

            toggle.style.left = newLeft + 'px';
            toggle.style.right = 'auto';
            toggle.style.bottom = newBottom + 'px';
            toggle.style.top = 'auto';

            // Keep panel aligned with button
            if (isOpen) positionPanel();
        }

        function onEnd() {
            toggle.classList.remove('dragging');
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', onTouchEnd);

            // Save position
            localStorage.setItem('sep_chat_pos', JSON.stringify({
                left: toggle.style.left,
                bottom: toggle.style.bottom
            }));
        }

        function onMouseMove(e) { onMove(e.clientX, e.clientY); }
        function onMouseUp() { onEnd(); }
        function onTouchMove(e) { e.preventDefault(); onMove(e.touches[0].clientX, e.touches[0].clientY); }
        function onTouchEnd() { onEnd(); }

        toggle.addEventListener('mousedown', function(e) {
            dragged = false;
            const pos = getPos();
            startX = e.clientX; startY = e.clientY;
            startLeft = pos.left; startBottom = pos.bottom;
            toggle.classList.add('dragging');
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
        });

        toggle.addEventListener('touchstart', function(e) {
            dragged = false;
            const pos = getPos();
            startX = e.touches[0].clientX; startY = e.touches[0].clientY;
            startLeft = pos.left; startBottom = pos.bottom;
            toggle.classList.add('dragging');
            document.addEventListener('touchmove', onTouchMove, { passive: false });
            document.addEventListener('touchend', onTouchEnd);
        }, { passive: true });

        // Restore saved position
        try {
            const saved = JSON.parse(localStorage.getItem('sep_chat_pos'));
            if (saved && saved.left && saved.bottom) {
                toggle.style.left = saved.left;
                toggle.style.right = 'auto';
                toggle.style.bottom = saved.bottom;
            }
        } catch(e) {}
    })();

    function positionPanel() {
        const rect = toggle.getBoundingClientRect();
        const panelW = Math.min(380, window.innerWidth - 16);
        const panelH = Math.min(520, window.innerHeight - 100);

        let left = rect.left;
        // flip left if near right edge
        if (left + panelW > window.innerWidth - 8) {
            left = rect.right - panelW;
        }
        left = Math.max(8, left);

        let bottom = window.innerHeight - rect.top + 8;
        if (bottom + panelH > window.innerHeight - 8) {
            bottom = window.innerHeight - rect.bottom + rect.height + 8;
        }

        panel.style.left = left + 'px';
        panel.style.right = 'auto';
        panel.style.bottom = bottom + 'px';
        panel.style.top = 'auto';
        panel.style.width = panelW + 'px';
    }
    // ────────────────────────────────────────────────────────────────

    // Load session from storage
    function loadSession() {
        try {
            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
            if (saved && saved.sessionId) {
                sessionId = saved.sessionId;
            }
        } catch (e) { }
    }

    function saveSession() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ sessionId }));
        } catch (e) { }
    }

    // Open/close the panel
    function openPanel() {
        panel.classList.remove('d-none');
        isOpen = true;
        chatIcon.classList.add('d-none');
        closeIcon.classList.remove('d-none');
        toggle.style.animation = 'none';
        positionPanel();

        if (messagesEl.children.length === 0) {
            showWelcome();
        }
        scrollBottom();
    }

    function closePanel() {
        panel.classList.add('d-none');
        isOpen = false;
        chatIcon.classList.remove('d-none');
        closeIcon.classList.add('d-none');
        toggle.style.animation = '';
    }

    function showWelcome() {
        const name = USER_NAME ? `, ${USER_NAME}` : '';
        addBotMessage(
            `Hi${name}! 👋 I'm SEP Bot, your AI assistant for the Student Economy Platform. How can I help you today?`,
            true
        );
    }

    // Toggle
    toggle.addEventListener('click', (e) => {
        if (toggle.classList.contains('dragging')) return; // was a drag, not a tap
        if (isOpen) {
            closePanel();
        } else {
            openPanel();
        }
    });

    if (minimizeBtn) minimizeBtn.addEventListener('click', closePanel);
    if (closeBtn) closeBtn.addEventListener('click', closePanel);

    // Add bot message bubble
    function addBotMessage(text, showQuickActions) {
        const div = document.createElement('div');
        div.className = 'chatbot-msg bot';
        div.innerHTML = `
            <div class="chatbot-msg-avatar">🤖</div>
            <div class="chatbot-msg-bubble">${formatMessage(text)}</div>
        `;
        messagesEl.appendChild(div);
        scrollBottom();

        if (showQuickActions && quickActions) {
            quickActions.style.display = 'flex';
        }
    }

    // Add user message bubble
    function addUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'chatbot-msg user';
        div.innerHTML = `
            <div class="chatbot-msg-bubble">${escapeHtml(text)}</div>
        `;
        messagesEl.appendChild(div);
        scrollBottom();
    }

    // Add report option buttons (quick select)
    function addReportOptions(options) {
        const div = document.createElement('div');
        div.className = 'chatbot-msg bot';
        const bubble = document.createElement('div');
        bubble.className = 'chatbot-msg-bubble';
        bubble.style.padding = '8px';

        options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'report-option-btn';
            btn.textContent = opt;
            btn.addEventListener('click', () => {
                bubble.remove();
                sendMessage(opt);
            });
            bubble.appendChild(btn);
        });

        div.appendChild(bubble);
        messagesEl.appendChild(div);
        scrollBottom();
    }

    // Add ticket created message
    function addTicketMessage(ticketData) {
        const div = document.createElement('div');
        div.className = 'chatbot-msg bot';
        div.innerHTML = `
            <div class="chatbot-msg-avatar">🤖</div>
            <div class="ticket-created-msg">
                <strong>✅ Ticket Created!</strong><br>
                Ticket Number: <strong>${ticketData.ticket_number}</strong><br>
                <a href="/support/tickets/${ticketData.ticket_number}/" class="text-success">View your ticket →</a>
            </div>
        `;
        messagesEl.appendChild(div);
        scrollBottom();
    }

    // Show/hide typing
    function showTyping() {
        typingEl.classList.remove('d-none');
        isTyping = true;
        scrollBottom();
        setInputEnabled(false);
    }

    function hideTyping() {
        typingEl.classList.add('d-none');
        isTyping = false;
        setInputEnabled(true);
    }

    function setInputEnabled(enabled) {
        if (inputEl) inputEl.disabled = !enabled;
        if (sendBtn) sendBtn.disabled = !enabled;
        if (!enabled) {
            sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        } else {
            sendBtn.innerHTML = '<i class="bi bi-send-fill"></i>';
        }
    }

    function scrollBottom() {
        setTimeout(() => {
            if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
        }, 50);
    }

    // Format message text (basic markdown-like)
    function formatMessage(text) {
        return escapeHtml(text)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // Send a message
    async function sendMessage(text) {
        if (!text || isTyping) return;

        // Hide quick actions
        if (quickActions) quickActions.style.display = 'none';

        addUserMessage(text);
        showTyping();

        const payload = {
            message: text,
            session_id: sessionId || '',
            page_url: window.location.pathname,
            context: reportContext || {}
        };

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            // Save session ID
            if (data.session_id) {
                sessionId = data.session_id;
                saveSession();
            }

            hideTyping();

            if (data.reply) {
                addBotMessage(data.reply, false);
            }

            // Handle report options
            if (data.quick_actions && data.quick_actions.length) {
                addReportOptions(data.quick_actions);
            }

            // Handle ticket created
            if (data.ticket_created) {
                addTicketMessage(data.ticket_created);
                reportContext = null;
            }

        } catch (err) {
            hideTyping();
            addBotMessage("Sorry, I'm having connection issues. Please try again.", false);
        }
    }

    // Form submit
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const msg = inputEl.value.trim();
            if (!msg) return;
            inputEl.value = '';
            sendMessage(msg);
        });
    }

    // Quick action buttons
    if (quickActions) {
        quickActions.addEventListener('click', (e) => {
            const btn = e.target.closest('.quick-action-btn');
            if (btn) {
                const msg = btn.dataset.msg;
                if (msg) sendMessage(msg);
            }
        });
    }

    // Public API for Report button integration
    window.sepChatbot = {
        open: openPanel,
        close: closePanel,
        openWithReport: function (context) {
            reportContext = { action: 'report', ...context };
            openPanel();
            // Clear messages and start report flow
            if (messagesEl) messagesEl.innerHTML = '';
            if (quickActions) quickActions.style.display = 'none';
            showTyping();

            const payload = {
                message: '',
                session_id: '',
                page_url: window.location.pathname,
                context: reportContext
            };

            fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                hideTyping();
                if (data.session_id) {
                    sessionId = data.session_id;
                    saveSession();
                }
                if (data.reply) addBotMessage(data.reply, false);
                if (data.quick_actions) addReportOptions(data.quick_actions);
            })
            .catch(() => {
                hideTyping();
                addBotMessage("I'll help you report this. What is the issue?", false);
            });
        }
    };

    // Global function for report buttons on listing/skill pages
    window.openChatbotWithReport = function (type, id, title, seller) {
        const ctx = { action: 'report' };
        if (type === 'listing') {
            ctx.listing_id = id;
            ctx.listing_title = title;
            ctx.seller = seller;
        } else {
            ctx.skill_id = id;
            ctx.skill_title = title;
            ctx.seller = seller;
        }
        window.sepChatbot.openWithReport(ctx);
    };

    loadSession();

})();
