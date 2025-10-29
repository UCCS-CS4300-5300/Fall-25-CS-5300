// Theme Toggle Functionality
(function() {
    'use strict';

    const THEME_KEY = 'theme-preference';
    const THEME_ATTR = 'data-theme';

    // Get all theme toggle buttons (for authenticated and guest)
    const themeToggleButtons = document.querySelectorAll('#theme-toggle');

    // Get all theme icons
    const lightIcons = document.querySelectorAll('[id^="theme-icon-light"]');
    const darkIcons = document.querySelectorAll('[id^="theme-icon-dark"]');

    // Get current theme from localStorage or default to 'light'
    function getTheme() {
        return localStorage.getItem(THEME_KEY) || 'light';
    }

    // Save theme to localStorage
    function saveTheme(theme) {
        localStorage.setItem(THEME_KEY, theme);
    }

    // Update icon visibility based on current theme
    function updateIcons(theme) {
        if (theme === 'dark') {
            // In dark mode, show sun icon (to switch to light)
            lightIcons.forEach(icon => icon.style.display = 'block');
            darkIcons.forEach(icon => icon.style.display = 'none');
        } else {
            // In light mode, show moon icon (to switch to dark)
            lightIcons.forEach(icon => icon.style.display = 'none');
            darkIcons.forEach(icon => icon.style.display = 'block');
        }
    }

    // Apply theme to document
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute(THEME_ATTR, 'dark');
        } else {
            document.documentElement.removeAttribute(THEME_ATTR);
        }
        updateIcons(theme);
        saveTheme(theme);
    }

    // Toggle theme
    function toggleTheme() {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    }

    // Initialize theme on page load
    function initTheme() {
        const savedTheme = getTheme();
        applyTheme(savedTheme);
    }

    // Add event listeners to all toggle buttons
    themeToggleButtons.forEach(button => {
        button.addEventListener('click', toggleTheme);
    });

    // Initialize on page load
    initTheme();
})();
