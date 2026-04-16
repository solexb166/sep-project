/**
 * SEP — Student Economy Platform
 * Main JavaScript
 */
(function () {
    'use strict';

    // Wishlist toggle via AJAX
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.wishlist-btn');
        if (!btn) return;

        const listingId = btn.dataset.listingId;
        const csrfToken = btn.dataset.csrf || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const icon = btn.querySelector('i');

        fetch(`/marketplace/${listingId}/wishlist/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'added') {
                btn.classList.add('active');
                if (icon) { icon.classList.remove('bi-heart'); icon.classList.add('bi-heart-fill'); }
                showToast('Added to wishlist!', 'success');
            } else {
                btn.classList.remove('active');
                if (icon) { icon.classList.remove('bi-heart-fill'); icon.classList.add('bi-heart'); }
                showToast('Removed from wishlist.', 'info');
            }
        })
        .catch(() => {
            showToast('Please log in to use wishlist.', 'warning');
        });
    });

    // Toast helper
    function showToast(message, type) {
        const container = document.querySelector('.toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast show align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        container.appendChild(toast);
        setTimeout(() => toast.classList.remove('show'), 4000);
        setTimeout(() => toast.remove(), 4500);
    }

    function createToastContainer() {
        const div = document.createElement('div');
        div.className = 'toast-container position-fixed top-0 end-0 p-3';
        div.style.zIndex = '9999';
        document.body.appendChild(div);
        return div;
    }

    // Image gallery on listing detail
    const galleryThumbs = document.querySelectorAll('.gallery-thumb');
    const mainImage = document.querySelector('.main-gallery-image');
    galleryThumbs.forEach(thumb => {
        thumb.addEventListener('click', function () {
            if (mainImage) {
                mainImage.src = this.dataset.src;
                galleryThumbs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Star rating display
    document.querySelectorAll('.star-rating-display').forEach(el => {
        const rating = parseFloat(el.dataset.rating) || 0;
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) stars += '<i class="bi bi-star-fill text-warning"></i>';
            else if (i - 0.5 <= rating) stars += '<i class="bi bi-star-half text-warning"></i>';
            else stars += '<i class="bi bi-star text-muted"></i>';
        }
        el.innerHTML = stars;
    });

    // Auto-resize textarea
    document.querySelectorAll('textarea.auto-resize').forEach(textarea => {
        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Price formatter (UGX)
    function formatUGX(amount) {
        return 'UGX ' + Number(amount).toLocaleString('en-UG');
    }

})();
