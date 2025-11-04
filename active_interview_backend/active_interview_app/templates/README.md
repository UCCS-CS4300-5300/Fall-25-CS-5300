# Templates Directory

## ⚠️ IMPORTANT: Read Before Creating or Modifying Templates

**Before working on any HTML template in this directory, you MUST:**

1. **Read the Style Guide:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
2. **Review the root AGENTS.md:** [`AGENTS.md`](../../../../AGENTS.md) - See "Frontend Styling Guidelines" section

## Using the Hierarchical Class System

**⭐ NEW!** AIS now uses a hierarchical class system for easier maintenance and site-wide changes.

### Quick Start

Use **base classes + modifiers** instead of standalone classes:

```html
<!-- OLD approach -->
<div class="chat-card">
  <h3>Title</h3>
  <p>Content</p>
</div>

<!-- NEW approach (preferred) -->
<div class="box box-chat">
  <h3>Title</h3>
  <p>Content</p>
</div>
```

### Common Patterns for Templates

**1. Content Sections**
```html
<div class="box box-section">
  <h2>Section Title</h2>
  <p>Section content...</p>
</div>
```

**2. List of Items**
```html
<ul class="list-clean list-items">
  <li class="box box-item">
    <span>Item Name</span>
    <button class="btn btn-primary">Action</button>
  </li>
</ul>
```

**3. Info Cards/Notices**
```html
<div class="box box-info">
  <p class="text-bold">Important Information</p>
  <p class="text-sm">Additional details...</p>
</div>
```

**4. Button Groups**
```html
<div style="display: flex; gap: 1rem;">
  <button class="btn btn-primary">Save</button>
  <button class="btn btn-secondary">Cancel</button>
</div>
```

**5. Score/Stats Grid**
```html
<div class="list-grid list-grid-2">
  <div class="box box-score">
    <h3 class="text-secondary-color text-sm">Total Users</h3>
    <div class="text-brand" style="font-size: 2rem; font-weight: bold;">1,234</div>
  </div>
  <div class="box box-score">
    <h3 class="text-secondary-color text-sm">Active Today</h3>
    <div class="text-brand" style="font-size: 2rem; font-weight: bold;">567</div>
  </div>
</div>
```

**6. Page Container**
```html
<div class="container-page container-standard">
  <div class="box box-section">
    <h1>Page Title</h1>
    <!-- content -->
  </div>
</div>
```

### Available Classes

**Boxes:** `.box` + `.box-chat`, `.box-button`, `.box-section`, `.box-info`, `.box-score`, `.box-item`

**Buttons:** `.btn` + `.btn-primary`, `.btn-secondary`, `.btn-card`, `.btn-minimal`, `.btn-danger`

**Containers:** `.container-page` + `.container-narrow`, `.container-standard`, `.container-centered`

**Lists:** `.list-clean`, `.list-items`, `.list-grid`, `.list-grid-2`, `.list-grid-3`

**Text:** `.text-brand`, `.text-sm`, `.text-lg`, `.text-bold`, `.text-primary-color`, etc.

**See `docs/STYLE_GUIDE.md` for complete documentation.**

## Critical Rules

### Never Hardcode Colors
❌ **WRONG:**
```css
color: #333;
background-color: white;
border: 1px solid #ddd;              /* Wrong: hardcoded AND thin border */
box-shadow: 5px 5px 5px black;
```

✅ **CORRECT:**
```css
color: var(--text-primary);
background-color: var(--surface-hover);  /* Outer containers - lighter */
border: 2px solid var(--border);         /* Always use 2px borders */
box-shadow: var(--shadow-md);
```

### Visual Hierarchy
Use proper nesting hierarchy for visual clarity:
```css
/* Outer containers (sections, cards) */
.outer-section {
  background: var(--surface-hover);  /* Lighter background */
  border: 2px solid var(--border);
}

/* Inner/nested elements (list items, info cards) */
.inner-item {
  background: var(--surface);        /* Darker for contrast */
  border: 2px solid var(--border);
}
```

### Always Override Bootstrap Classes
Bootstrap uses hardcoded colors. Override them in your template's `<style>` block:

```css
.card {
  background-color: var(--surface-hover) !important;  /* Outer container - lighter */
  border: 2px solid var(--border) !important;         /* 2px border */
  color: var(--text-primary) !important;
}

.card-header, .card-body {
  background-color: var(--surface) !important;        /* Nested - darker */
  color: var(--text-primary) !important;
}

.text-muted {
  color: var(--text-secondary) !important;
}

.form-control {
  background-color: var(--surface) !important;
  color: var(--text-primary) !important;
}

/* ⚠️ CRITICAL: Always include placeholder styling with form controls! */
.form-control::placeholder,
.form-select::placeholder,
textarea::placeholder {
  color: var(--text-light) !important;
  opacity: 1 !important;
}
```

**⚠️ Common Mistake:** Forgetting to include placeholder styling when overriding `.form-control` will cause placeholder text to appear dark in dark mode. **Always** include the `::placeholder` selectors above when you override form control styles.

### Always Test Both Themes
- ✅ Test in light mode
- ✅ Test in dark mode (toggle in navbar)
- ✅ Verify all text is readable
- ✅ Check all backgrounds adapt properly

## Reference Examples

**Excellent examples to follow:**
- `documents/document-list.html` - Theme-aware design
- `profile.html` - Two-column layout
- `candidates/search.html` - Bootstrap overrides

## Quick CSS Variables Reference

```css
/* Text */
var(--text-primary)      /* Main text */
var(--text-secondary)    /* Muted text */
var(--text-white)        /* White text */

/* Surfaces - Visual Hierarchy */
var(--surface-hover)     /* Outer containers - lighter background */
var(--surface)           /* Inner/nested elements - darker background */
var(--background)        /* Page background */

/* Brand & Status */
var(--primary)           /* Primary brand color */
var(--primary-light)     /* Light variant */
var(--accent)            /* Accent color */
var(--success)           /* Success state */
var(--warning)           /* Warning state */
var(--error)             /* Error state */

/* Layout */
var(--border)            /* Border color - use with 2px solid */
var(--border-light)      /* ⚠️ DEPRECATED - use var(--border) instead */
var(--shadow)            /* Box shadow */
var(--shadow-sm)         /* Small shadow */
var(--shadow-md)         /* Medium shadow */
var(--radius)            /* Border radius */
var(--radius-sm)         /* Small radius */
var(--radius-md)         /* Medium radius */
```

## Checklist Before Committing

- [ ] **Consider using hierarchical classes** (`.box box-chat`, `.btn btn-primary`, etc.)
- [ ] **Use text utilities** (`.text-brand`, `.text-lg`, etc.) for typography
- [ ] All colors use CSS variables (no hex/rgb/named colors)
- [ ] Outer containers use `var(--surface-hover)` background
- [ ] Inner/nested elements use `var(--surface)` background
- [ ] All borders use `2px solid var(--border)` (not 1px or border-light)
- [ ] Visual hierarchy is clear (lighter outer, darker inner)
- [ ] Bootstrap classes overridden where needed
- [ ] Placeholder styling included if form controls are overridden
- [ ] Tested in light mode
- [ ] Tested in dark mode
- [ ] Tested placeholder text visibility in dark mode
- [ ] Responsive on mobile
- [ ] No hardcoded colors anywhere

---

**For comprehensive guidelines, see:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
