# AIS Frontend Style Guide

This document provides comprehensive styling guidelines for the Active Interview Service (AIS) application. All new pages and components should follow these guidelines to maintain consistency across the application.

## Table of Contents
1. [Theme System](#theme-system)
2. [CSS Variables](#css-variables)
3. **[Hierarchical Class System](#hierarchical-class-system)** ⭐ NEW
4. [Page Layout Patterns](#page-layout-patterns)
5. [Component Styling](#component-styling)
6. [Typography](#typography)
7. [Colors and Theming](#colors-and-theming)
8. [Examples](#examples)

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
var(--border)           /* Border color - use for all borders (2px solid) */
var(--border-light)     /* Lighter border (deprecated - use var(--border) instead) */
var(--shadow)           /* Box shadow */
var(--shadow-sm)        /* Small shadow */
var(--shadow-md)        /* Medium shadow */
var(--radius)           /* Border radius */
var(--radius-sm)        /* Small border radius */
var(--radius-md)        /* Medium border radius */
```

**Note:** Use `2px solid var(--border)` for all borders to maintain consistent, prominent visual hierarchy.

---

## Hierarchical Class System

**NEW!** AIS now uses a hierarchical class system that makes styling easier to maintain and update site-wide.

### Concept

Instead of creating standalone classes with all properties duplicated, we use **BASE CLASSES + MODIFIER CLASSES**.

**Before (old approach):**
```html
<div class="chat-card">Content</div>
```
Each class defined all properties independently, making site-wide changes difficult.

**After (new approach):**
```html
<div class="box box-chat">Content</div>
```
Base class (`.box`) defines shared properties, modifier (`.box-chat`) adds specific styling.

### Benefits

1. **Easy site-wide changes** - Edit `.box` to change ALL boxes at once
2. **Smaller, focused modifiers** - Only define what's different
3. **Easy to add variants** - Just create a new modifier class
4. **Clear, predictable naming** - `.base-modifier` pattern

### Available Hierarchies

#### Boxes & Cards - Base: `.box`

All boxes/cards/sections can use the `.box` base class:

```css
/* Base - shared by all boxes */
.box {
  border-radius: var(--radius);
  transition: all 0.2s ease;
  padding: 1.5rem;
}
```

**Modifiers:**
- `.box-chat` - White background, border, subtle shadow (for content cards)
- `.box-button` - Primary colored, no border (for clickable cards)
- `.box-section` - Large sections with extra padding
- `.box-info` - Highlighted background for notices
- `.box-score` - Centered content for stats/scores
- `.box-item` - List items with flex layout

**Usage:**
```html
<!-- Content card -->
<div class="box box-chat">
  <h3>Card Title</h3>
  <p>Content here</p>
</div>

<!-- Clickable action card -->
<a href="/action" class="box box-button">
  <h4>Take Action</h4>
</a>

<!-- Info notice -->
<div class="box box-info">
  <p class="text-bold">Important Information</p>
</div>

<!-- List item -->
<div class="box box-item">
  <span>Item Name</span>
  <button class="btn btn-primary">Action</button>
</div>
```

#### Buttons - Base: `.btn`

All buttons should use the `.btn` base class:

**Modifiers:**
- `.btn-primary` - Primary action (blue background)
- `.btn-secondary` - Secondary action (white with border)
- `.btn-card` - For use in cards/lists
- `.btn-minimal` - Subtle, transparent background
- `.btn-danger` - Destructive actions (red)

**Usage:**
```html
<button class="btn btn-primary">Save</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-danger">Delete</button>
```

#### Containers - Base: `.container-page`

Page-level containers for consistent layouts:

**Modifiers:**
- `.container-narrow` - Max width 700px (forms, auth pages)
- `.container-standard` - Max width 1200px (most content)
- `.container-full` - Full width, no max
- `.container-centered` - Flex centered, min-height 60vh

**Usage:**
```html
<!-- Narrow centered form page -->
<div class="container-page container-narrow container-centered">
  <div class="box box-section">
    <h2>Login</h2>
    <form>...</form>
  </div>
</div>

<!-- Standard content page -->
<div class="container-page container-standard">
  <div class="box box-section">
    <h2>Dashboard</h2>
    <!-- content -->
  </div>
</div>
```

#### Lists - Base: `.list-clean` or `.list-items`

For lists and collections:

**Base Classes:**
- `.list-clean` - Removes default list styling
- `.list-items` - Vertical stack with gap
- `.list-grid` - Grid layout with gap

**Grid Modifiers:**
- `.list-grid-2` - 2-column auto-fit grid
- `.list-grid-3` - 3-column auto-fit grid

**Usage:**
```html
<!-- Vertical list of items -->
<ul class="list-clean list-items">
  <li class="box box-item">Item 1</li>
  <li class="box box-item">Item 2</li>
</ul>

<!-- Grid of score cards -->
<div class="list-grid list-grid-2">
  <div class="box box-score">
    <h3>Score 1</h3>
    <div class="text-brand" style="font-size: 2rem;">95</div>
  </div>
  <div class="box box-score">
    <h3>Score 2</h3>
    <div class="text-brand" style="font-size: 2rem;">87</div>
  </div>
</div>
```

#### Typography Utilities

Utility classes for text styling:

**Color:**
- `.text-primary-color` - Main text color
- `.text-secondary-color` - Secondary text color
- `.text-light-color` - Light/muted text
- `.text-brand` - Brand primary color
- `.text-accent` - Accent color

**Size:**
- `.text-sm` - Small text (0.9rem)
- `.text-lg` - Large text (1.25rem)
- `.text-xl` - Extra large text (1.5rem)

**Weight:**
- `.text-bold` - Bold weight (600)
- `.text-normal` - Normal weight (400)

**Usage:**
```html
<p class="text-brand text-lg text-bold">Important Headline</p>
<p class="text-secondary-color">Supporting text</p>
<p class="text-light-color text-sm">Fine print</p>
```

### Making Site-Wide Changes

The hierarchical system makes site-wide changes simple:

**Want to change all boxes?**
```css
.box {
  border-radius: var(--radius-lg);  /* Make all boxes rounder */
  padding: 2rem;                     /* Make all boxes bigger */
}
```

**Want to change just chat cards?**
```css
.box-chat {
  background-color: var(--surface-hover);  /* Slightly darker */
}
```

**Want to change all primary buttons?**
```css
.btn-primary {
  background-color: var(--accent) !important;  /* Use accent color instead */
}
```

### Creating New Variants

Need a custom variant? Just create a modifier:

```css
/* Define only what's DIFFERENT from the base */
.box-warning {
  background-color: var(--warning);
  color: var(--text-white);
  border: 2px solid var(--accent);
}
```

**Usage:**
```html
<div class="box box-warning">Warning message</div>
```

### Migration Path

**Legacy classes still work!** All existing classes (`.chat-card`, `.button-card`, etc.) remain functional. You can:

1. **Start using new classes immediately** in new code
2. **Migrate gradually** - update as you touch existing pages
3. **Mix approaches** - Both work simultaneously

**Note:** See `static/css/main.css` lines 70-171 for complete documentation and lines 2160-2276 for common usage patterns.

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

**Visual Hierarchy:**
- **Outer containers** use `var(--surface-hover)` with `2px solid var(--border)` - lighter, prominent borders
- **Inner/nested elements** use `var(--surface)` with `2px solid var(--border)` - darker for contrast

```css
/* Outer Section Container */
.section-container {
  background: var(--surface-hover);  /* Lighter background for outer container */
  border: 2px solid var(--border);   /* Prominent 2px border */
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

/* Nested Inner Elements */
.inner-item {
  background: var(--surface);        /* Darker background for nested items */
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 0.75rem;
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
  background-color: var(--surface-hover) !important;  /* Outer container - lighter */
  border: 2px solid var(--border) !important;         /* Prominent 2px border */
  color: var(--text-primary) !important;
}

.card-header {
  background-color: var(--surface) !important;        /* Nested element - darker */
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

.card-body {
  background-color: var(--surface) !important;        /* Nested element - darker */
  color: var(--text-primary) !important;
}
```

### List Items

```css
.list-item {
  padding: 1rem;
  background: var(--surface);            /* Nested element - darker background */
  border: 2px solid var(--border);       /* Prominent 2px border */
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
  border: 1px solid #ddd;  /* Wrong: hardcoded color AND thin border */
}

.btn {
  color: white;  /* Won't adapt to theme */
}

/* Don't use deprecated border-light or thin borders */
.section {
  background: var(--surface);
  border: 1px solid var(--border-light);  /* ❌ Deprecated */
}
```

### ✅ DO THIS
```css
/* Always use CSS variables */
.my-element {
  color: var(--text-primary);
  background: var(--surface-hover);      /* Lighter for outer containers */
  border: 2px solid var(--border);       /* Always use 2px borders */
}

.btn {
  color: var(--text-white);  /* Adapts to theme */
}

/* Use proper hierarchy */
.outer-section {
  background: var(--surface-hover);  /* Lighter background */
  border: 2px solid var(--border);
}

.inner-item {
  background: var(--surface);        /* Darker for contrast */
  border: 2px solid var(--border);
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
- [ ] **Consider using hierarchical classes** (`.box box-chat`, `.btn btn-primary`, etc.)
- [ ] Bootstrap classes are overridden where necessary
- [ ] Headings use `var(--text-primary)`
- [ ] Outer containers use `var(--surface-hover)` background
- [ ] Inner/nested elements use `var(--surface)` background
- [ ] All borders use `2px solid var(--border)` (not 1px or border-light)
- [ ] Visual hierarchy is clear (lighter outer, darker inner)
- [ ] Forms use proper theme-aware styling
- [ ] Modals have theme-aware backgrounds
- [ ] Page is responsive (test at different screen sizes)
- [ ] `.text-muted` is overridden to use `var(--text-secondary)`
- [ ] Buttons use `var(--text-white)` for text on colored backgrounds
- [ ] **Leverage text utilities** (`.text-brand`, `.text-lg`, etc.) for consistent typography

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
  background: var(--surface);            /* Nested element - darker background */
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

### Loading Indicators

**Issue #130:** Visual feedback for long-running operations.

#### Button Spinner Pattern

For operations that take 2+ seconds (file uploads, report generation, etc.):

```html
<button type="submit" class="btn btn-primary" id="uploadBtn">
  <span class="loading-spinner-button"
        id="uploadSpinner"
        role="status"
        aria-hidden="true"
        style="display:none;"></span>
  <span id="uploadBtnText">Upload</span>
</button>

<script>
function showSpinner() {
  const button = document.getElementById('uploadBtn');
  const spinner = document.getElementById('uploadSpinner');
  const buttonText = document.getElementById('uploadBtnText');

  // Show spinner
  spinner.style.display = 'inline-block';

  // Update button text
  buttonText.textContent = 'Uploading...';

  // Disable button to prevent double-submit
  button.disabled = true;

  return true; // Allow form submission
}
</script>
```

**CSS Classes Available:**
```css
/* Button spinner (white, for colored buttons) */
.loading-spinner-button

/* General spinners (uses --primary color) */
.loading-spinner           /* Base class */
.loading-spinner-sm        /* 1rem - for buttons */
.loading-spinner-md        /* 2rem - for inline content */
.loading-spinner-lg        /* 3rem - for modals */

/* Button loading state */
.btn-loading               /* Disabled appearance */
```

**Implementation Examples:**

1. **Form Submit (Synchronous)** - Resume upload
   - Location: `templates/upload.html`
   - Pattern: Show spinner on form submit, disable button
   - See: [upload.html:150-199](../active_interview_backend/active_interview_app/templates/upload.html#L150-L199)

2. **AJAX Download (Asynchronous)** - PDF/CSV reports
   - Location: `templates/reports/export-report.html` + `static/js/reports.js`
   - Pattern: Fetch API download with spinner, button re-enabled after
   - See: [reports.js](../active_interview_backend/active_interview_app/static/js/reports.js)

**Best Practices:**
- ✅ Always disable button when showing spinner
- ✅ Update button text to describe action ("Uploading...", "Generating...")
- ✅ Hide spinner and re-enable button on success/error
- ✅ Use `aria-hidden="true"` on spinner elements
- ✅ Use `role="status"` for accessibility
- ❌ Don't use spinners for instant operations (< 1 second)

---

## Support

For questions or clarifications about styling, refer to:
- `static/css/main.css` - Theme variable definitions
- `static/js/theme.js` - Theme switching logic
- Example pages listed in the Examples section above
