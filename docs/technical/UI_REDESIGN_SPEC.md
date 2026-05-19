# Calma — UI Redesign Specification
**Version:** 1.1  
**Status:** Active  
**Scope:** `client/src/App.jsx` · `client/src/index.css`

> **Implementation note:** Phases 0–1 are pre-requisites for all later phases.  
> Each phase leaves the application in a fully working state.  
> Copy-paste every code block verbatim — no mental interpolation required.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Design Principles](#2-design-principles)
3. [Current State Audit](#3-current-state-audit)
4. [Design Token System](#4-design-token-system)
5. [Phase 0 — Token Foundation](#phase-0--token-foundation)
6. [Phase 1 — Chat Interface](#phase-1--chat-interface)
7. [Phase 2 — Sidebar & Navigation](#phase-2--sidebar--navigation)
8. [Phase 3 — Welcome & Authentication](#phase-3--welcome--authentication)
9. [Phase 4 — Intake & Screening](#phase-4--intake--screening)
10. [Phase 5 — Profile & Settings](#phase-5--profile--settings)
11. [Phase 6 — Motion & Micro-interactions](#phase-6--motion--micro-interactions)
12. [Acceptance Criteria](#12-acceptance-criteria)
13. [File Change Map](#13-file-change-map)

---

## 1. Executive Summary

Calma is a psychoeducational mental health assistant. Its interface must communicate **calm, safety, and clinical credibility** without feeling cold or overwhelming. The current implementation has accumulated design debt across six areas:

| Issue | Severity | Affected Screens |
|---|---|---|
| Hardcoded colors that break the light theme | Critical | Sidebar, context menus |
| 8+ non-tokenized shadow values | High | All components |
| 12+ border-radius values with no scale | High | All components |
| Clinical UI language ("CLINICAL SOURCES", "conf 1.00") | High | Chat |
| No visual hierarchy in the chat bubble | High | Chat |
| Inconsistent error color system (4 different red shades) | Medium | Forms, alerts |
| Toggle switch uses hardcoded Twitter blue (`#1d9bf0`) | Medium | Settings |
| `Lightbulb` icon imported but unused after Phase 1 | Low | — |

This document specifies the complete remediation in six ordered phases. Every code block is ready to copy-paste with zero additional interpolation.

---

## 2. Design Principles

### 2.1 Emotional Safety Over Information Density
Every data point shown has a cognitive cost. In a mental health context, cognitive load generates anxiety. When in doubt, hide; make discovery opt-in.

> **Rule:** If a piece of information can be placed behind a toggle without hurting comprehension, place it there.

### 2.2 One Visual Priority Per View
Each screen section may have exactly one primary focal element.

> **Rule:** No two elements in the same view may use the accent color at full opacity simultaneously.

### 2.3 Whitespace as Structure
Generous spacing (line-height 1.65+, padding 1rem+) gives content room to breathe.

> **Rule:** Adjacent card elements must have at minimum `0.75rem` gap.

### 2.4 Warm Restraint
Deep navy (not pure black). De-saturated teal/indigo (not high-vibrancy). No saturated reds or oranges in non-critical UI.

### 2.5 Transparency Without Jargon
Show the AI label and sources — but through human language, not technical labels.

> **Rule:** Replace `CLINICAL SOURCES · conf 1.00` with `3 kaynak` and an expand toggle. Never show raw confidence scores.

---

## 3. Current State Audit

### 3.1 Design Token Inventory

**Existing `:root` variables (33 tokens — all kept)**

| Token | Light | Dark |
|---|---|---|
| `--bg-color` | `#f4f7fb` | `#0b0d12` |
| `--bg-image` | gradient | gradient |
| `--panel-bg` | `rgba(255,255,255,0.84)` | `rgba(18,22,29,0.84)` |
| `--sidebar-bg` | `rgba(255,255,255,0.74)` | `rgba(11,14,19,0.84)` |
| `--surface-bg` | `rgba(255,255,255,0.9)` | `rgba(255,255,255,0.03)` |
| `--surface-border` | `rgba(15,23,42,0.08)` | `rgba(255,255,255,0.07)` |
| `--input-bg` | `rgba(255,255,255,0.92)` | `rgba(18,22,29,0.95)` |
| `--input-border` | `rgba(15,23,42,0.1)` | `rgba(255,255,255,0.08)` |
| `--control-bg` | `rgba(255,255,255,0.78)` | `rgba(255,255,255,0.04)` |
| `--control-border` | `rgba(15,23,42,0.08)` | — |
| `--chip-bg` | `rgba(255,255,255,0.82)` | `rgba(255,255,255,0.04)` |
| `--text-primary` | `#0f172a` | `#eef2ff` |
| `--text-secondary` | `#475569` | `#a3b0c2` |
| `--text-muted` | `#64748b` | `#7c8aa0` |
| `--accent` | `#4f5dff` | `#6d86ff` |
| `--accent-soft` | `rgba(79,93,255,0.08)` | `rgba(109,134,255,0.11)` |
| `--accent-hover` | `#3447ff` | `#5773ff` |
| `--danger` | `#b91c1c` | `#f87171` |
| `--success` | `#15803d` | `#34d399` |
| `--warn` | `#b45309` | `#fbbf24` |
| `--shadow` | `0 24px 48px rgba(15,23,42,0.08)` | `0 22px 50px rgba(0,0,0,0.28)` |
| `--sidebar-width` | `320px` | — |
| `--header-height` | `64px` | — |
| `--transition-speed` | `0.3s` | — |

**New tokens to be added in Phase 0**

| Token | Light value | Dark value |
|---|---|---|
| `--radius-sm` | `0.5rem` | same |
| `--radius-md` | `0.875rem` | same |
| `--radius-lg` | `1.25rem` | same |
| `--radius-xl` | `1.75rem` | same |
| `--radius-full` | `999px` | same |
| `--shadow-sm` | `0 2px 8px rgba(15,23,42,0.06)` | `0 2px 8px rgba(0,0,0,0.18)` |
| `--shadow-md` | `0 8px 24px rgba(15,23,42,0.08)` | `0 8px 24px rgba(0,0,0,0.22)` |
| `--shadow-lg` | `0 24px 48px rgba(15,23,42,0.10)` | `0 24px 48px rgba(0,0,0,0.28)` |
| `--insight-border` | `rgba(16,185,129,0.45)` | `rgba(16,185,129,0.40)` |
| `--menu-bg` | `#ffffff` | `#1e2433` |
| `--menu-text` | `#0f172a` | `#e2e8f0` |
| `--menu-danger` | `#dc2626` | `#f87171` |
| `--toggle-on` | `var(--accent)` | `var(--accent)` |
| `--danger-bg` | `rgba(185,28,28,0.08)` | `rgba(248,113,113,0.10)` |
| `--danger-border` | `rgba(185,28,28,0.20)` | `rgba(248,113,113,0.25)` |

> **Why `--danger-bg` / `--danger-border` instead of `rgba(var(--danger), ...)`?**  
> CSS `rgba()` does not accept a `var()` containing a full hex color. The workaround is pre-computing the rgba values as separate tokens, one per theme. This keeps all color logic in `:root` and avoids invalid CSS.

### 3.2 Hardcoded Color Violations (6 confirmed)

```css
/* 1 — history hover/active — breaks light theme */
.history-item:hover, .history-item.active { background: #2f2f2f; }

/* 2 — context menu background */
.history-item__menu { background: #1e1e1e; }

/* 3 — context menu text */
.history-item__menu-item { color: #ececec; }

/* 4 — danger item */
.history-item__menu-item.is-danger { color: #ff9b9b; }

/* 5 — toggle switch (Twitter blue) */
.locked-toggle.is-on { background: #1d9bf0; }

/* 6 — profile avatar */
.profile-editor-hero__avatar { background: linear-gradient(180deg, #2dd4bf 0%, #14b8a6 100%); }
```

### 3.3 Border Radius — Current vs Target

| Current (12 values) | Target token |
|---|---|
| `0.5rem` | `--radius-sm` |
| `0.65rem–0.95rem` (7 values) | `--radius-md` (0.875rem) |
| `1rem–1.4rem` (5 values) | `--radius-lg` (1.25rem) |
| `1.5rem–1.75rem` | `--radius-xl` (1.75rem) |
| `999px` | `--radius-full` |

### 3.4 Shadow — Current vs Target

| Current (9 custom values) | Replace with |
|---|---|
| `0 4px 12px …` | `--shadow-sm` |
| `0 10px 25px …` · `0 12px 26px …` · `0 12px 28px …` | `--shadow-md` |
| `0 18px 40px …` · `0 18px 48px …` · `0 20px 40px …` · `0 24px 48px …` · `0 30px 90px …` | `--shadow-lg` |

### 3.5 `FileText` Icon — Do NOT Remove

`FileText` is imported and used in **three places unrelated to the chat bubble**:
- Line 1279 — Terms of service link (profile panel)
- Line 2144 — Release notes link (settings)
- Line 2194 — Help section

Remove only `Lightbulb` (confirmed unused after Phase 1 removes the nugget card header).

### 3.6 Z-Index Layer Map (reference only — no changes needed)

| Value | Component |
|---|---|
| `9999` | Context menus (fixed) |
| `1000` | User dropdown panel |
| `220` | Profile/settings modal |
| `200` | Sidebar |
| `180` | Auth overlay |
| `100` | Welcome, screening |
| `60` | Sidebar open button |
| `30–50` | Dropdowns, select panels |

---

## 4. Design Token System

### 4.1 Semantic Color Roles

| Role | Token | Use |
|---|---|---|
| Surface background | `--surface-bg` | All floating cards |
| Surface border | `--surface-border` | Card borders |
| Primary action | `--accent` | Buttons, links, focus rings |
| Primary action hover | `--accent-hover` | Button hover |
| Primary action soft bg | `--accent-soft` | Chip backgrounds |
| Body text | `--text-primary` | All readable content |
| Secondary text | `--text-secondary` | Labels, metadata |
| Muted / disabled | `--text-muted` | Placeholders, captions |
| Error / destructive | `--danger` | Text color |
| Error background | `--danger-bg` | Alert backgrounds |
| Error border | `--danger-border` | Alert borders |
| Success | `--success` | Confirmations |
| Warning | `--warn` | Cautionary states |
| Clinical insight accent | `--insight-border` | Blockquote left border |
| Context menu bg | `--menu-bg` | Replaces `#1e1e1e` |
| Context menu text | `--menu-text` | Replaces `#ececec` |
| Context menu danger | `--menu-danger` | Replaces `#ff9b9b` |
| Toggle active | `--toggle-on` | Replaces `#1d9bf0` |

### 4.2 Typography Scale

| Role | Font | Size | Weight | Line Height |
|---|---|---|---|---|
| Page title | Outfit | `clamp(2rem, 2.5vw, 2.5rem)` | 600 | 1.2 |
| Section heading | Outfit | `1.25rem` | 600 | 1.3 |
| Body / chat | Inter | `1rem` | 400 | 1.65 |
| Secondary | Inter | `0.9rem` | 400 | 1.5 |
| Label | Inter | `0.75rem` | 500 | 1.4 |
| Micro label | Inter | `0.7rem` | 600 | 1.3 |

---

## Phase 0 — Token Foundation

**Goal:** Add missing tokens, fix all 6 hardcoded color violations.  
**Files:** `client/src/index.css`  
**Estimated lines changed:** ~65  
**Visual impact:** Light theme sidebar and context menu become legible. Toggle color changes.

### 0.1 Add Tokens to `:root` (light theme)

Find the closing `}` of the existing `:root {` block and insert **before** it:

```css
  /* Radius scale */
  --radius-sm:   0.5rem;
  --radius-md:   0.875rem;
  --radius-lg:   1.25rem;
  --radius-xl:   1.75rem;
  --radius-full: 999px;

  /* Shadow scale */
  --shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 24px 48px rgba(15, 23, 42, 0.10);

  /* Semantic additions */
  --insight-border: rgba(16, 185, 129, 0.45);
  --menu-bg:        #ffffff;
  --menu-text:      #0f172a;
  --menu-danger:    #dc2626;
  --toggle-on:      var(--accent);
  --danger-bg:      rgba(185, 28, 28, 0.08);
  --danger-border:  rgba(185, 28, 28, 0.20);
```

### 0.2 Add Tokens to `:root[data-theme='dark']`

Find the closing `}` of `:root[data-theme='dark'] {` and insert **before** it:

```css
  /* Shadow scale (dark overrides) */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.18);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.22);
  --shadow-lg: 0 24px 48px rgba(0, 0, 0, 0.28);

  /* Semantic additions (dark overrides) */
  --insight-border: rgba(16, 185, 129, 0.40);
  --menu-bg:        #1e2433;
  --menu-text:      #e2e8f0;
  --menu-danger:    #f87171;
  --danger-bg:      rgba(248, 113, 113, 0.10);
  --danger-border:  rgba(248, 113, 113, 0.25);
```

### 0.3 Fix Violation 1 — History Item Hover/Active

**Find and replace** in `index.css`:

```css
/* FIND */
.history-item:hover,
.history-item.active {
  background: #2f2f2f;
}

/* REPLACE WITH */
.history-item:hover {
  background: var(--control-bg);
}

.history-item.active {
  background: var(--accent-soft);
}
```

Also find the separate `.history-item.active` block (if it exists) and ensure it only has:

```css
.history-item.active {
  background: var(--accent-soft);
}

.history-item.active .history-item__title {
  color: var(--text-primary);
}
```

### 0.4 Fix Violation 2 & 3 & 4 — Context Menu

**Find and replace** in `index.css`:

```css
/* FIND */
.history-item__menu {
  background: #1e1e1e;
  /* (other properties unchanged) */
}

/* REPLACE the background line only */
.history-item__menu {
  background: var(--menu-bg);
  border: 1px solid var(--surface-border);
  box-shadow: var(--shadow-lg);
  /* keep existing border-radius, width, padding unchanged */
}
```

```css
/* FIND */
.history-item__menu-item {
  color: #ececec;
  /* other props... */
}

/* REPLACE color line only */
.history-item__menu-item {
  color: var(--menu-text);
  /* keep other properties unchanged */
}
```

```css
/* FIND */
.history-item__menu-item.is-danger {
  color: #ff9b9b;
}

/* REPLACE */
.history-item__menu-item.is-danger {
  color: var(--menu-danger);
}
```

### 0.5 Fix Violation 5 — Toggle Switch

```css
/* FIND */
.locked-toggle.is-on {
  background: #1d9bf0;
}

/* REPLACE */
.locked-toggle.is-on {
  background: var(--toggle-on);
}
```

### 0.6 Fix Violation 6 — Profile Avatar Gradient

```css
/* FIND */
.profile-editor-hero__avatar {
  background: linear-gradient(180deg, #2dd4bf 0%, #14b8a6 100%);
}

/* REPLACE */
.profile-editor-hero__avatar {
  background: linear-gradient(135deg, var(--accent), var(--success));
}
```

---

## Phase 1 — Chat Interface

**Goal:** Redesign the AI message bubble to eliminate clinical jargon, reduce visual noise.  
**Files:** `client/src/App.jsx`, `client/src/index.css`  
**Dependency:** Phase 0

### Phase 1 — Implementation Status

The following items have already been applied to the current codebase in a prior session. Verify each before re-applying:

| Item | Applied? | How to verify |
|---|---|---|
| `expandedSources` state | Check | `grep "expandedSources" App.jsx` → should return a result |
| `toggleSources` callback | Check | `grep "toggleSources" App.jsx` → should return a result |
| `BookOpen`, `ChevronUp` imports | Check | `grep "BookOpen" App.jsx` |
| Bubble JSX (`.msg-label`, `.ai-insight`, `.sources-footer`) | Check | `grep "msg-label" App.jsx` |
| Typing indicator JSX | Check | `grep "typing-indicator" App.jsx` |
| `.ai-insight` CSS | Check | `grep "ai-insight" index.css` |
| `.sources-footer` CSS | Check | `grep "sources-footer" index.css` |
| `.typing-indicator` CSS | Check | `grep "typing-bounce" index.css` |
| `.clinical-nugget-card` CSS deleted | Check | `grep "clinical-nugget-card" index.css` → should return **nothing** |
| `.source-tag` CSS deleted | Check | `grep "\.source-tag" index.css` → should return **nothing** |
| `Lightbulb` import removed | Check | `grep "Lightbulb" App.jsx` → should return **nothing** |

If any item is missing, apply the corresponding block below.

### 1.1 Icon Import Changes

In `App.jsx`, at the lucide-react import block:

```jsx
/* ADD these two (if not already present) */
BookOpen,
ChevronUp,

/* REMOVE this one (only if not used anywhere else — confirmed: it is not) */
Lightbulb,

/* DO NOT remove FileText — it is used in profile/settings sections */
```

### 1.2 State & Handler (add once, if not present)

```jsx
/* Inside function App(), with the other useState declarations */
const [expandedSources, setExpandedSources] = useState(new Set());

/* After the refs block, before useEffect calls */
const toggleSources = useCallback((idx) => {
  setExpandedSources((prev) => {
    const next = new Set(prev);
    next.has(idx) ? next.delete(idx) : next.add(idx);
    return next;
  });
}, []);
```

### 1.3 Assistant Message Bubble JSX

Find the assistant message render block (search for `message-row assistant` in App.jsx). Replace the entire block with:

```jsx
) : (
  <div key={idx} className="message-row assistant">
    <div className="avatar avatar-assistant" aria-hidden="true">
      <Sparkles size={18} />
    </div>
    <div className="message-content">
      <div className="msg-label">{APP_NAME}</div>

      {msg.data?.status === 'crisis' && (
        <div className="crisis-alert">
          <div className="flex items-center gap-2 mb-2 font-bold">
            <AlertTriangle size={16} />
            Acil Destek
          </div>
          {msg.content}
        </div>
      )}

      {msg.data?.status !== 'crisis' && (
        <div className="prose prose-invert max-w-none">{msg.content}</div>
      )}

      {msg.data?.clinical_nugget && (
        <blockquote className="ai-insight animate-slide-up">
          {msg.data.clinical_nugget}
        </blockquote>
      )}

      {msg.data?.sources?.length > 0 && (
        <div className="sources-footer">
          <button
            className="sources-footer__toggle"
            onClick={() => toggleSources(idx)}
            aria-expanded={expandedSources.has(idx)}
          >
            <BookOpen size={11} />
            {expandedSources.has(idx) ? 'Kaynakları gizle' : `${msg.data.sources.length} kaynak`}
            {expandedSources.has(idx) ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          </button>
          {expandedSources.has(idx) && (
            <ul className="sources-footer__list">
              {msg.data.sources.map((src, sidx) => (
                <li key={sidx}>
                  <span className="sources-footer__title">{src.title}</span>
                  {src.section && (
                    <span className="sources-footer__section"> · {src.section}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  </div>
)
```

### 1.4 Loading Indicator JSX

Find the loading `isLoading` block (search for `Searching clinical index`). Replace:

```jsx
/* BEFORE */
<div className="message-content text-muted italic flex items-center gap-2">
  {intakePhase ? 'PhD Assistant is reflecting...' : 'Searching clinical index...'}
</div>

/* AFTER */
<div className="message-content">
  <div className="typing-indicator">
    <span /><span /><span />
  </div>
</div>
```

### 1.5 CSS — Bubble Background

Find `.message-row.assistant .message-content` in `index.css`. Replace its `background` and `border-color` properties:

```css
.message-row.assistant .message-content {
  text-align: left;
  border-color: var(--surface-border);
  background: var(--surface-bg);
  /* keep all other properties (border-radius, padding, etc.) unchanged */
}
```

### 1.6 CSS — New Components (add if not present)

```css
/* AI sender label */
.msg-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

/* Clinical insight — left-border blockquote */
.ai-insight {
  margin: 0.875rem 0 0;
  padding: 0.45rem 0.75rem;
  border-left: 2px solid var(--insight-border);
  font-size: 0.85rem;
  color: var(--text-muted);
  font-style: italic;
  line-height: 1.55;
}

/* Sources footer */
.sources-footer {
  margin-top: 0.875rem;
  padding-top: 0.625rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.sources-footer__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
  color: var(--text-muted);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: color 0.15s;
}

.sources-footer__toggle:hover {
  color: var(--text-secondary);
}

.sources-footer__list {
  margin-top: 0.5rem;
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  animation: slideUp 0.2s ease both;
}

.sources-footer__list li { font-size: 0.72rem; line-height: 1.4; }
.sources-footer__title   { color: var(--text-secondary); }
.sources-footer__section { color: var(--text-muted); }

/* Typing indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing-bounce 1.2s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30%           { transform: translateY(-5px); opacity: 1; }
}
```

### 1.7 CSS — Delete Obsolete Blocks

Find and **delete entirely** (do not comment out):

```
.clinical-nugget-card { … }        ← entire block
.clinical-nugget-card::before { … } ← entire block
.source-tag { … }                  ← entire block
```

---

## Phase 2 — Sidebar & Navigation

**Goal:** Fix light-theme compatibility, context menu theming.  
**Files:** `client/src/index.css`  
**Dependency:** Phase 0 (tokens must exist)

### 2.1 History Item Active State

```css
/* FIND and REPLACE the combined hover+active rule */

/* BEFORE */
.history-item:hover,
.history-item.active {
  background: #2f2f2f;
}

/* AFTER */
.history-item:hover {
  background: var(--control-bg);
}

.history-item.active {
  background: var(--accent-soft);
}

.history-item.active .history-item__title {
  color: var(--text-primary);
}
```

### 2.2 Context Menu

```css
/* REPLACE the background and border-radius in .history-item__menu */
.history-item__menu {
  background: var(--menu-bg);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  /* keep: z-index, width, position, padding */
}

.history-item__menu-item {
  color: var(--menu-text);
  /* keep: padding, font-size, border-radius, transition */
}

.history-item__menu-item.is-danger {
  color: var(--menu-danger);
}

.history-item__menu-item.is-danger:hover {
  background: var(--danger-bg);
  color: var(--menu-danger);
}
```

### 2.3 Sidebar Brand Icon

The brand icon (sidebar logo) must be accent-colored, not green. Green is reserved exclusively for the AI message avatar.

```css
/* Find .sidebar-brand or .sidebar-brand__icon and add/replace */
.sidebar-brand__icon {
  background: linear-gradient(135deg, var(--accent), var(--accent-hover));
  /* keep: width, height, border-radius, display, align/justify */
}

/* AI avatar stays green — do not touch */
.avatar-assistant {
  background: linear-gradient(135deg, #10b981, #34d399);
}
```

### 2.4 Sidebar Search Input

```css
/* Find .sidebar-search input or .sidebar-search */
.sidebar-search {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-md);
  /* keep: padding, font-size, color */
}
```

---

## Phase 3 — Welcome & Authentication

**Goal:** Simplify welcome screen hierarchy, fix auth error colors.  
**Files:** `client/src/App.jsx`, `client/src/index.css`  
**Dependency:** Phase 0

### 3.1 Welcome Screen — JSX

**Current structure** (find this block, starting at `className="glass-card welcome-card"`):

```jsx
<div className="glass-card welcome-card animate-fade-in text-center">
  <div className="welcome-icon">
    <Brain className="text-accent" size={30} />
  </div>
  <p className="welcome-kicker">{APP_NAME}</p>
  <h2>Let&apos;s begin.</h2>
  <p className="welcome-copy">
    Let&apos;s get to know each other...
  </p>
  <div className="welcome-consent">
    <input id="welcome-consent" type="checkbox" ... />
    <label htmlFor="welcome-consent" className="welcome-consent__label">
      I consent to the intake questions and PHQ-9 / GAD-7 assessments...
    </label>
  </div>
  {sessionError && <div className="screening-inline-error">{sessionError}</div>}
  <button type="button" className="btn-primary w-full mt-6 py-4" onClick={handleWelcomeContinue}>
    Continue
  </button>
</div>
```

**Replace with:**

```jsx
<div className="glass-card welcome-card animate-fade-in">
  <div className="welcome-brand">
    <div className="welcome-brand__icon">
      <Brain size={28} />
    </div>
    <h2 className="welcome-brand__name">{APP_NAME}</h2>
    <p className="welcome-brand__tagline">
      Güvenli, kanıta dayalı psikolojik destek.
    </p>
  </div>

  <div className="welcome-divider" />

  <label className="welcome-consent" htmlFor="welcome-consent">
    <input
      id="welcome-consent"
      type="checkbox"
      className="screening-consent__checkbox"
      checked={welcomeConsent}
      onChange={(event) => setWelcomeConsent(event.target.checked)}
    />
    <span>
      Kısa tanışma sorularına ve isteğe bağlı klinik taramalara onay veriyorum.
    </span>
  </label>

  {sessionError && <div className="screening-inline-error">{sessionError}</div>}

  <button
    type="button"
    className="btn-primary welcome-cta"
    onClick={handleWelcomeContinue}
  >
    Başla
  </button>
</div>
```

### 3.2 Welcome Screen — CSS

**Delete** these old rules:

```
.welcome-kicker { … }
.welcome-card h2 { … }
.welcome-copy { … }
.welcome-icon { … }
```

**Add** these new rules:

```css
.welcome-card {
  /* keep existing width, padding, border-radius */
  text-align: left; /* override text-center if it was in className */
}

.welcome-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.5rem;
  margin-bottom: 0;
}

.welcome-brand__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.25rem;
}

.welcome-brand__name {
  font-family: 'Outfit', sans-serif;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.welcome-brand__tagline {
  font-size: 0.9rem;
  color: var(--text-secondary);
  max-width: 260px;
  line-height: 1.5;
  margin: 0;
}

.welcome-divider {
  width: 100%;
  height: 1px;
  background: var(--surface-border);
  margin: 1.5rem 0;
}

.welcome-consent {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
  cursor: pointer;
}

.welcome-cta {
  width: 100%;
  margin-top: 1rem;
  padding: 0.875rem;
}
```

### 3.3 Authentication — Error Messages

Find `.auth-error` in `index.css` and replace its color properties:

```css
/* BEFORE — likely uses hardcoded red */
.auth-error {
  /* some background, border, color */
}

/* AFTER */
.auth-error {
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  color: var(--danger);
  border-radius: var(--radius-md);
  padding: 0.65rem 0.875rem;
  font-size: 0.85rem;
}
```

### 3.4 Authentication — Ambient Blobs

```css
/* Find these three selectors and reduce opacity */
.auth-stage__ambient--one,
.auth-stage__ambient--two,
.auth-stage__ambient--three {
  opacity: 0.22; /* reduce from current value — less visual noise */
}
```

---

## Phase 4 — Intake & Screening

**Goal:** Remove misleading "PhD" label, add intake progress indicator, improve screening option states.  
**Files:** `client/src/App.jsx`, `client/src/index.css`  
**Dependency:** Phase 0

### 4.1 Remove "PhD Clinical Psychologist" Label

This label is **already removed** if Phase 1 was applied (the msg-label now always shows `{APP_NAME}`).

Verify by searching: `grep "PhD Clinical" App.jsx` — should return nothing.

If it still appears in the loading indicator or elsewhere:

```jsx
/* FIND anywhere in App.jsx */
{intakePhase ? 'PhD Clinical Psychologist' : `${APP_NAME} (AI)`}
{intakePhase ? 'PhD Assistant is reflecting...' : 'Searching clinical index...'}

/* REPLACE all variants with simply */
{APP_NAME}
/* and loading: already replaced by typing indicator in Phase 1 */
```

### 4.2 Intake Progress Indicator — JSX

Define the phase order as a frontend constant at the top of `App.jsx` (outside the component, below the imports):

```jsx
/* Add near other constants (e.g. near APP_NAME, after line ~65) */
const INTAKE_PHASES = ['name', 'concern', 'timeline', 'support', 'narrative'];
```

Then find the `chat-max-width` container in the chat view and add the progress bar **as the first child inside the scrollable messages area**:

```jsx
{/* Add immediately above the messages.map(...) call */}
{intakePhase && (
  <div className="intake-progress">
    <div className="intake-progress__steps">
      {INTAKE_PHASES.map((phase, i) => (
        <div
          key={phase}
          className={`intake-progress__dot${
            INTAKE_PHASES.indexOf(intakePhase) >= i ? ' is-done' : ''
          }`}
        />
      ))}
    </div>
    <span className="intake-progress__label">
      Tanışma {INTAKE_PHASES.indexOf(intakePhase) + 1} / {INTAKE_PHASES.length}
    </span>
  </div>
)}
```

### 4.3 Intake Progress Indicator — CSS

```css
.intake-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.5rem 0 0.875rem;
  border-bottom: 1px solid var(--surface-border);
  margin-bottom: 1.25rem;
}

.intake-progress__steps {
  display: flex;
  gap: 0.35rem;
}

.intake-progress__dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--surface-border);
  transition: background 0.3s ease;
}

.intake-progress__dot.is-done {
  background: var(--accent);
}

.intake-progress__label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
```

### 4.4 Screening Options — Selected State

Find `.screening-option` in `index.css`. Add or replace the selected state:

```css
.screening-option.is-selected {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: 0 0 0 1px var(--accent);
}

.screening-option.is-selected .screening-option__label {
  color: var(--text-primary);
  font-weight: 500;
}
```

### 4.5 Screening Grid — Mobile

Add inside the existing `@media (max-width: 768px)` block:

```css
@media (max-width: 768px) {
  /* Add this inside the existing 768px block */
  .screening-question-list {
    grid-template-columns: 1fr;
  }
}
```

---

## Phase 5 — Profile & Settings

**Goal:** Fix avatar gradient, toggle color, settings nav active state, profile notice.  
**Files:** `client/src/index.css`  
**Dependency:** Phase 0

### 5.1 Profile Avatar Gradient

```css
/* FIND */
.profile-editor-hero__avatar {
  background: linear-gradient(180deg, #2dd4bf 0%, #14b8a6 100%);
}

/* REPLACE */
.profile-editor-hero__avatar {
  background: linear-gradient(135deg, var(--accent), var(--success));
}
```

### 5.2 Settings Toggle — Already Fixed in Phase 0

The `--toggle-on` token (set to `var(--accent)`) was applied in Phase 0, Step 0.5. Verify:

```
grep "locked-toggle" index.css
```

Should show `background: var(--toggle-on)`.

### 5.3 Settings Nav Active State

```css
/* FIND */
.profile-menu-section.is-active {
  background: rgba(255, 255, 255, 0.12);
}

/* REPLACE */
.profile-menu-section.is-active {
  background: var(--accent-soft);
  color: var(--accent);
}
```

### 5.4 Profile Notice

```css
/* FIND .profile-notice and replace its color properties */
.profile-notice {
  background: var(--accent-soft);
  border: 1px solid rgba(109, 134, 255, 0.20);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  padding: 0.6rem 0.875rem;
  font-size: 0.85rem;
}
```

---

## Phase 6 — Motion & Micro-interactions

**Goal:** Consolidate duplicate animations, add reduced-motion support, optional stagger.  
**Files:** `client/src/index.css`, optionally `client/src/App.jsx`

### 6.1 Consolidate Duplicate `slideUp`

Search `index.css` for `@keyframes slideUp` — there are currently two definitions with slightly different translateY values (`10px` and `12px`). Delete both and add one canonical version:

```css
@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.animate-slide-up {
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}
```

### 6.2 Reduced Motion Support

Add at the very end of `index.css`:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 6.3 Message Stagger (Optional)

In `App.jsx`, on the message row `div`, add an inline `animationDelay`:

```jsx
<div
  key={idx}
  className="message-row assistant"
  style={{ animationDelay: `${Math.min(idx * 0.04, 0.24)}s` }}
>
```

This creates a subtle cascade effect when a conversation is first loaded. Cap at 6 messages worth of delay (`0.24s`) to avoid feeling slow on long histories.

---

## 12. Acceptance Criteria

### Phase 0
- [ ] `grep "#2f2f2f" index.css` → no results
- [ ] `grep "#1e1e1e" index.css` → no results
- [ ] `grep "#ececec" index.css` → no results
- [ ] `grep "#ff9b9b" index.css` → no results
- [ ] `grep "#1d9bf0" index.css` → no results
- [ ] `grep "#2dd4bf" index.css` → no results
- [ ] Sidebar history items are legible in light theme
- [ ] Context menu renders correctly in both themes
- [ ] All 16 new tokens appear in `:root`

### Phase 1
- [ ] `grep "CLINICAL SOURCES" App.jsx` → no results
- [ ] `grep "conf " App.jsx` → no results (was `conf ${src.confidence.toFixed(2)}`)
- [ ] `grep "PhD Clinical" App.jsx` → no results
- [ ] `grep "Lightbulb" App.jsx` → no results
- [ ] `grep "clinical-nugget-card" index.css` → no results
- [ ] `grep "\.source-tag" index.css` → no results
- [ ] Sources section is collapsed by default; expands and collapses on click
- [ ] Loading state shows three-dot animation, not text
- [ ] `grep "BookOpen" App.jsx` → result found (icon is imported)

### Phase 2
- [ ] Sidebar history items: hover uses `--control-bg`, active uses `--accent-soft`
- [ ] Context menu dark background comes from `var(--menu-bg)` (not `#1e1e1e`)
- [ ] Brand icon (logo) is accent-colored; AI avatar stays green — they are visually distinct

### Phase 3
- [ ] `grep "Let.s begin" App.jsx` → no results (removed)
- [ ] `grep "welcome-kicker" index.css` → no results (deleted)
- [ ] Welcome screen shows brand block, divider, consent, CTA — in that order
- [ ] Auth error message uses `var(--danger-bg)` and `var(--danger-border)`

### Phase 4
- [ ] `grep "PHASE_ORDER" App.jsx` → no results
- [ ] `grep "INTAKE_PHASES" App.jsx` → results found (new constant)
- [ ] Progress dots appear during intake, highlight completed steps in accent
- [ ] `grep "PhD" App.jsx` → no results

### Phase 5
- [ ] `grep "#2dd4bf" index.css` → no results (avatar fixed)
- [ ] `grep "#1d9bf0" index.css` → no results (toggle fixed, also covered by Phase 0)
- [ ] Profile avatar uses accent/success gradient
- [ ] Active settings nav item uses `var(--accent-soft)`

### Phase 6
- [ ] `@keyframes slideUp` appears exactly once in `index.css`
- [ ] `prefers-reduced-motion` media query exists at end of `index.css`

---

## 13. File Change Map

| Phase | File | Operation | Lines (est.) |
|---|---|---|---|
| 0 | `index.css` | Add 16 tokens to `:root` and `[data-theme='dark']` | 34 |
| 0 | `index.css` | Fix 6 hardcoded color violations | 20 |
| 1 | `App.jsx` | Icon imports (add 2, remove 1) | 3 |
| 1 | `App.jsx` | Add state + callback | 10 |
| 1 | `App.jsx` | Replace assistant message bubble JSX | 45 |
| 1 | `App.jsx` | Replace loading indicator JSX | 6 |
| 1 | `index.css` | Replace bubble background | 4 |
| 1 | `index.css` | Add `.msg-label`, `.ai-insight`, `.sources-footer`, `.typing-indicator` | 65 |
| 1 | `index.css` | Delete `.clinical-nugget-card`, `.source-tag` | −25 |
| 2 | `index.css` | Fix history item, context menu, brand icon, search | 28 |
| 3 | `App.jsx` | Replace welcome screen JSX | 28 |
| 3 | `index.css` | Delete old welcome rules, add new | 40 |
| 3 | `index.css` | Auth error + blob opacity | 12 |
| 4 | `App.jsx` | Add `INTAKE_PHASES` constant | 1 |
| 4 | `App.jsx` | Add progress indicator JSX | 18 |
| 4 | `index.css` | Progress indicator CSS | 28 |
| 4 | `index.css` | Screening option + mobile grid | 16 |
| 5 | `index.css` | Avatar, nav active, profile notice | 18 |
| 6 | `index.css` | Consolidate slideUp, add reduced-motion | 20 |
| 6 | `App.jsx` | Optional message stagger | 3 |
| **Total** | | | **~393 lines** |

---

*Maintained alongside the codebase. Update version number and check acceptance criteria after completing each phase.*
