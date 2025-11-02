# Static Assets Directory

## ⚠️ IMPORTANT: Read Before Modifying CSS or JavaScript

**Before working on any static files (CSS/JS), you MUST:**

1. **Read the Style Guide:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
2. **Review the root AGENTS.md:** [`AGENTS.md`](../../../../AGENTS.md) - See "Frontend Styling Guidelines" section

## Directory Structure

```
static/
├── css/
│   └── main.css          # ⭐ CSS variable definitions (theme system)
├── js/
│   ├── theme.js          # Theme switching logic
│   └── charts.js         # Chart.js integration (uses CSS variables)
└── images/               # Image assets
```

## Theme System Files

### `css/main.css`
**Central theme definition file.** Contains all CSS variable definitions for both light and dark modes.

**When adding new CSS variables:**
1. Define them in both `:root` (light mode) and `[data-theme="dark"]` (dark mode)
2. Use semantic names (e.g., `--text-primary`, not `--color-1`)
3. Update `docs/STYLE_GUIDE.md` to document new variables

### `js/theme.js`
**Theme switcher logic.** Handles toggling between light and dark modes.

**Don't modify unless:** You're fixing a bug or adding theme-related features.

## Working with JavaScript Files

### Reading CSS Variables

When working with JavaScript that needs colors (like charts.js):

✅ **CORRECT:**
```javascript
const styles = getComputedStyle(document.documentElement);
const primaryColor = styles.getPropertyValue('--primary').trim();
const textColor = styles.getPropertyValue('--text-primary').trim();

// Use these variables instead of hardcoded colors
```

❌ **WRONG:**
```javascript
const primaryColor = '#4482A6';  // Hardcoded - won't adapt to theme!
const textColor = '#333';        // Hardcoded - won't work in dark mode!
```

### Example: charts.js

See `js/charts.js` for a reference implementation of reading CSS variables for Chart.js configuration.

## Critical Rules

### 1. Never Hardcode Colors in CSS
❌ **WRONG:**
```css
.my-element {
  color: #333;
  background: white;
  border: 1px solid lightgray;
}
```

✅ **CORRECT:**
```css
.my-element {
  color: var(--text-primary);
  background: var(--surface);
  border: 1px solid var(--border-light);
}
```

### 2. Never Hardcode Colors in JavaScript
❌ **WRONG:**
```javascript
element.style.backgroundColor = '#4482A6';
```

✅ **CORRECT:**
```javascript
const styles = getComputedStyle(document.documentElement);
const bgColor = styles.getPropertyValue('--primary').trim();
element.style.backgroundColor = bgColor;
```

### 3. Always Test Theme Changes
When modifying `main.css` or `theme.js`:
- ✅ Test light mode
- ✅ Test dark mode
- ✅ Test theme toggle functionality
- ✅ Verify all pages still look correct

## Available CSS Variables

See `css/main.css` for the complete list. Common variables:

```css
/* Text Colors */
--text-primary
--text-secondary
--text-light
--text-white

/* Surfaces */
--background
--surface
--surface-hover

/* Brand Colors */
--primary
--primary-light
--primary-dark
--accent

/* Status Colors */
--success
--warning
--error
--info

/* Layout */
--border
--border-light
--shadow
--shadow-sm
--shadow-md
--radius
--radius-sm
--radius-md
```

## Adding New CSS Variables

If you need to add new theme-related variables:

1. **Add to `css/main.css`** in both light and dark mode sections:
```css
:root {
  --my-new-variable: #value-for-light-mode;
}

[data-theme="dark"] {
  --my-new-variable: #value-for-dark-mode;
}
```

2. **Document in `docs/STYLE_GUIDE.md`** under the CSS Variables section

3. **Test in both themes** to ensure it works correctly

## Checklist Before Committing

- [ ] No hardcoded colors in CSS files
- [ ] No hardcoded colors in JavaScript files
- [ ] New CSS variables added to both light and dark modes
- [ ] Tested in light mode
- [ ] Tested in dark mode
- [ ] Theme toggle still works
- [ ] Documentation updated if adding new variables

---

**For comprehensive guidelines, see:** [`docs/STYLE_GUIDE.md`](../../../../docs/STYLE_GUIDE.md)
