/**
 * Sidebar logic for EMS.
 * Handles mobile toggle and desktop collapse state.
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('open-sidebar');
    const closeBtn = document.getElementById('close-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    // --- Mobile Behavior ---
    
    function openSidebar() {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        // Small delay to allow display:block to apply before animating opacity
        setTimeout(() => overlay.classList.remove('opacity-0'), 10);
        document.body.classList.add('overflow-hidden');
    }

    function closeSidebar() {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        document.body.classList.remove('overflow-hidden');
    }

    if (openBtn) openBtn.addEventListener('click', openSidebar);
    if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // --- Desktop Collapse Behavior ---
    // In Phase 1 we'll keep it simple: sidebar is always expanded on desktop.
    // Full collapse logic requires layout adjustments handled in CSS.
});
