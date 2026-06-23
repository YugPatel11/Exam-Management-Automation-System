/**
 * Main JavaScript utilities for EMS.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. User Menu Dropdown
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');

    if (userMenuButton && userMenuDropdown) {
        userMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenuDropdown.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!userMenuDropdown.contains(e.target) && !userMenuButton.contains(e.target)) {
                userMenuDropdown.classList.add('hidden');
            }
        });
    }

    // 2. Auto-hide messages after 5 seconds
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        setTimeout(() => {
            const alerts = messageContainer.querySelectorAll('[role="alert"]');
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                alert.style.transition = 'all 0.3s ease-out';
                setTimeout(() => alert.remove(), 300);
            });
        }, 5000);
    }
});

/**
 * Get CSRF token for AJAX requests.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
