# Templates Directory

## ⚠️ IMPORTANT: Read Before Creating or Modifying Templates

**Before working on any HTML template in this directory, you MUST:**

1. **Read the Style Guide:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
2. **Review the root AGENTS.md:** [`AGENTS.md`](../../../../AGENTS.md) - See "Frontend Styling Guidelines" section

## Critical Rules

### Never Hardcode Colors
❌ **WRONG:**
```css
color: #333;
background-color: white;
border: 1px solid #ddd;
box-shadow: 5px 5px 5px black;
```

✅ **CORRECT:**
```css
color: var(--text-primary);
background-color: var(--surface);
border: 1px solid var(--border-light);
box-shadow: var(--shadow-md);
```

### Always Override Bootstrap Classes
Bootstrap uses hardcoded colors. Override them in your template's `<style>` block:

```css
.card {
  background-color: var(--surface) !important;
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

/* Surfaces */
var(--surface)           /* Cards, panels */
var(--surface-hover)     /* Hover states */
var(--background)        /* Page background */

/* Brand & Status */
var(--primary)           /* Primary brand color */
var(--primary-light)     /* Light variant */
var(--accent)            /* Accent color */
var(--success)           /* Success state */
var(--warning)           /* Warning state */
var(--error)             /* Error state */

/* Layout */
var(--border)            /* Border color */
var(--border-light)      /* Light border */
var(--shadow)            /* Box shadow */
var(--shadow-sm)         /* Small shadow */
var(--shadow-md)         /* Medium shadow */
var(--radius)            /* Border radius */
var(--radius-sm)         /* Small radius */
var(--radius-md)         /* Medium radius */
```

## Checklist Before Committing

- [ ] All colors use CSS variables (no hex/rgb/named colors)
- [ ] Bootstrap classes overridden where needed
- [ ] Placeholder styling included if form controls are overridden
- [ ] Tested in light mode
- [ ] Tested in dark mode
- [ ] Tested placeholder text visibility in dark mode
- [ ] Responsive on mobile
- [ ] No hardcoded colors anywhere

---

**For comprehensive guidelines, see:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
