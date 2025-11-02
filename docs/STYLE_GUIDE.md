# AIS Frontend Style Guide

This document provides comprehensive styling guidelines for the Active Interview Service (AIS) application. All new pages and components should follow these guidelines to maintain consistency across the application.

## Table of Contents
1. [Theme System](#theme-system)
2. [CSS Variables](#css-variables)
3. [Page Layout Patterns](#page-layout-patterns)
4. [Component Styling](#component-styling)
5. [Typography](#typography)
6. [Colors and Theming](#colors-and-theming)
7. [Examples](#examples)

---

## Theme System

AIS uses a CSS variable-based theme system that automatically adapts to light and dark modes. The theme switcher is located in `static/js/theme.js` and the CSS variables are defined in `static/css/main.css`.

### Key Principles
- **Always use CSS variables** for colors, never hardcode colors
- **Never use hardcoded hex/rgb values** for text or backgrounds
- **Bootstrap classes should be overridden** when they use hardcoded colors

---

## CSS Variables

### Available CSS Variables

#### Text Colors
```css
var(--text-primary)     /* Primary text color - adapts to theme */
var(--text-secondary)   /* Secondary/muted text */
var(--text-light)       /* Light gray text for hints */
var(--text-white)       /* White text (for dark backgrounds) */
```

#### Surface Colors
```css
var(--background)       /* Page background */
var(--surface)          /* Card/section backgrounds */
var(--surface-hover)    /* Hover state for surfaces */
```

#### Brand Colors
```css
var(--primary)          /* Primary brand color (#1F7BA6 / lighter in dark) */
var(--primary-light)    /* Lighter variant of primary */
var(--primary-dark)     /* Darker variant of primary */
var(--accent)           /* Accent color */
```

#### Status Colors
```css
var(--success)          /* Success states */
var(--warning)          /* Warning states */
var(--error)            /* Error states */
var(--info)             /* Info states */
```

#### Layout
```css
var(--border)           /* Border color */
var(--border-light)     /* Lighter border */
var(--shadow)           /* Box shadow */
var(--shadow-sm)        /* Small shadow */
var(--shadow-md)        /* Medium shadow */
var(--radius)           /* Border radius */
var(--radius-sm)        /* Small border radius */
var(--radius-md)        /* Medium border radius */
```

---

## Page Layout Patterns

### Standard Page Container

```html
<div class="page-container">
  <div class="page-header">
    <h1>Page Title</h1>
    <p>Optional description</p>
  </div>

  <div class="content-section">
    <!-- Page content -->
  </div>
</div>
```

```css
.page-container {
  max-width: 900px;  /* Use 1200px for two-column layouts */
  margin: 2rem auto;
  padding: 0 1.5rem;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  color: var(--primary);
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 1rem;
}
```

### Section/Card Pattern

```css
.section-container {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: var(--shadow-sm);
}

.section-container h2 {
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Optional: Add accent stripe */
.section-container h2::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 1.5rem;
  background: var(--primary);
  border-radius: 2px;
}
```

### Two-Column Layout

```css
.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 1.5fr;  /* 40% left, 60% right */
  gap: 2rem;
  align-items: start;
}

@media (max-width: 992px) {
  .two-column-layout {
    grid-template-columns: 1fr;  /* Stack on smaller screens */
  }
}
```

---

## Component Styling

### Buttons

```css
/* Primary Button */
.btn-primary {
  background-color: var(--primary);
  color: var(--text-white);
  border: none;
  padding: 0.75rem 2rem;
  border-radius: var(--radius);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow);
  color: var(--text-white);
}
```

### Form Controls

```css
.form-control, .form-select {
  background-color: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

.form-control:focus, .form-select:focus {
  background-color: var(--surface) !important;
  border-color: var(--primary) !important;
  color: var(--text-primary) !important;
  box-shadow: 0 0 0 0.2rem rgba(31, 123, 166, 0.25) !important;
}

/* IMPORTANT: Always include placeholder styling when overriding form controls */
.form-control::placeholder,
.form-select::placeholder,
textarea::placeholder {
  color: var(--text-light) !important;
  opacity: 1 !important;
}
```

**⚠️ Critical:** When you override `.form-control` styles in a template's `<style>` block, you **MUST** also include the placeholder styling above. Otherwise Bootstrap's default placeholder styles will override the global styles and appear as dark text in dark mode.

### Cards

```css
.card {
  background-color: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

.card-header {
  background-color: var(--surface-hover) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

.card-body {
  background-color: var(--surface) !important;
  color: var(--text-primary) !important;
}
```

### List Items

```css
.list-item {
  padding: 1rem;
  background: var(--surface-hover);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.list-item:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--primary);
}
```

### Modals

```css
.modal-content {
  background-color: var(--surface) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border);
}

.modal-header {
  border-color: var(--border);
}

.modal-footer {
  border-color: var(--border);
}

.modal-body {
  color: var(--text-primary);
}
```

---

## Typography

### Headings

```css
h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary) !important;
}

h1 { font-size: 2rem; font-weight: 700; }
h2 { font-size: 1.5rem; font-weight: 600; }
h3 { font-size: 1.25rem; font-weight: 600; }
```

### Body Text

```css
p {
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.6;
}

.text-muted {
  color: var(--text-secondary) !important;
}

.text-small {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
```

---

## Colors and Theming

### ❌ DON'T DO THIS
```css
/* Never hardcode colors */
.my-element {
  color: #333;
  background: white;
  border: 1px solid #ddd;
}

.btn {
  color: white;  /* Won't adapt to theme */
}
```

### ✅ DO THIS
```css
/* Always use CSS variables */
.my-element {
  color: var(--text-primary);
  background: var(--surface);
  border: 1px solid var(--border-light);
}

.btn {
  color: var(--text-white);  /* Adapts to theme */
}
```

### Bootstrap Override Pattern

When using Bootstrap classes that have hardcoded colors, override them in a `<style>` block:

```html
<style>
  .card {
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
  }

  .text-muted {
    color: var(--text-secondary) !important;
  }

  .form-control {
    background-color: var(--surface) !important;
    color: var(--text-primary) !important;
  }
</style>
```

---

## Examples

### Example 1: Document Management Page
**Reference:** `templates/documents/document-list.html`

This page demonstrates:
- Proper use of CSS variables throughout
- Section-based layout with accent stripes
- Theme-aware form controls
- Responsive design

### Example 2: Profile Page
**Reference:** `templates/profile.html`

This page demonstrates:
- Two-column grid layout
- User info cards with accent borders
- Proper modal styling
- Document list component

### Example 3: Candidate Search
**Reference:** `templates/candidates/search.html`

This page demonstrates:
- Bootstrap overrides for theme support
- Card-based layout
- Form controls with proper theming

---

## Quick Checklist for New Pages

Before creating or updating a page, ensure:

- [ ] All colors use CSS variables (no hardcoded hex/rgb values)
- [ ] Bootstrap classes are overridden where necessary
- [ ] Headings use `var(--text-primary)`
- [ ] Backgrounds use `var(--surface)` or `var(--background)`
- [ ] Borders use `var(--border)` or `var(--border-light)`
- [ ] Forms use proper theme-aware styling
- [ ] Modals have theme-aware backgrounds
- [ ] Page is responsive (test at different screen sizes)
- [ ] `.text-muted` is overridden to use `var(--text-secondary)`
- [ ] Buttons use `var(--text-white)` for text on colored backgrounds

---

## Common Patterns Reference

### Empty State
```html
<div class="empty-state">
  <p>No items found</p>
</div>
```

```css
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}
```

### Section Divider
```html
<hr class="section-divider">
```

```css
.section-divider {
  height: 2px;
  background: linear-gradient(to right, transparent, var(--border), transparent);
  margin: 2rem 0;
  border: none;
}
```

### Info Cards
```html
<div class="info-item">
  <div class="info-label">Label</div>
  <div class="info-value">Value</div>
</div>
```

```css
.info-item {
  padding: 0.75rem;
  background: var(--surface-hover);
  border-radius: var(--radius);
  border-left: 3px solid var(--primary);
}

.info-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 500;
}
```

---

## Support

For questions or clarifications about styling, refer to:
- `static/css/main.css` - Theme variable definitions
- `static/js/theme.js` - Theme switching logic
- Example pages listed in the Examples section above
