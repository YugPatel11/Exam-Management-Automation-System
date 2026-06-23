/**
 * Dark mode toggle logic.
 * Respects system preference, falls back to localStorage, then cookie (for Django template sync).
 */

document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');

    // Check current state
    const isDark = document.documentElement.classList.contains('dark');

    // Set initial icon
    if (isDark) {
        lightIcon.classList.remove('hidden');
    } else {
        darkIcon.classList.remove('hidden');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            // Toggle icons
            darkIcon.classList.toggle('hidden');
            lightIcon.classList.toggle('hidden');

            // If is dark mode
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
                document.cookie = "darkMode=false; path=/; max-age=31536000"; // 1 year
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
                document.cookie = "darkMode=true; path=/; max-age=31536000"; // 1 year
            }
        });
    }
});

// Run this script immediately in head to avoid FOUC (Flash of Unstyled Content)
// Note: This logic is also handled server-side via cookies in base.html
if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark');
}
