# React 19, Next.js 15 & TypeScript Frontend Architecture

This guide details the modern frontend architecture of **QuantWeave**, powered by React 19, Next.js 15 App Router, TypeScript 5.7, Tailwind CSS, and a 4-theme dynamic design token system.

---

## 1. Next.js 15 App Router Architecture

QuantWeave structures routes using the App Router convention under `apps/web/app/`:

```
apps/web/app/
├── (dashboard)/               # Route group sharing the authenticated shell
│   ├── layout.tsx             # Collapsible sidebar, topbar, user profile menu
│   ├── dashboard/page.tsx     # Overview metrics, holdings summary, quick launch
│   ├── equity/page.tsx        # Company search, OHLCV charts, technical indicators
│   ├── equity/compare/        # Side-by-side equity comparison
│   ├── portfolio/page.tsx     # Double-entry ledger, cash deposits, buy/sell modal
│   ├── funds/page.tsx         # Mutual fund screener, NAV charts, SIP calculator
│   ├── market/page.tsx        # News sentiment, macroeconomic indicators
│   ├── quantlab/page.tsx      # Lookahead-free backtesting, equity curves, grid search
│   ├── ai/page.tsx            # Multi-turn Copilot with tool call citations
│   └── profile/page.tsx       # User profile, 6 avatar presets, theme switcher
├── login/page.tsx             # Authentication login screen
├── register/page.tsx          # User registration screen
├── layout.tsx                 # Root HTML shell, ThemeContext provider
├── globals.css                # CSS custom property theme definitions
└── middleware.ts              # Route protection and JWT validation
```

### Route Groups `(dashboard)`
By wrapping internal features in `(dashboard)/`, all financial modules automatically inherit the navigation sidebar, responsive mobile header, and user profile drawer without adding `/(dashboard)` to the browser URL path.

---

## 2. Server vs. Client Components

In React 19 and Next.js 15, components default to **Server Components** unless explicitly marked with `"use client"`.

- **Server Components**: Rendered on the server into static HTML/RSC payloads. Ideal for static headers, SEO metadata, and marketing landing pages.
- **Client Components** (`"use client"`): Required whenever interactive state (`useState`, `useEffect`, `useContext`) or browser APIs (`window`, `localStorage`, `document`) are needed.

### Client Component Example (`apps/web/components/UserProfileMenu.tsx`)

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useTheme } from "@/lib/theme-context";

export function UserProfileMenu({ user }: { user: UserProfile }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { currentTheme, setTheme } = useTheme();

  // Close on Escape key press
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setIsOpen(false);
    }
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={menuRef}>
      <button 
        aria-label="User account menu"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 p-2 rounded-lg hover:bg-[var(--bg-card-hover)]"
      >
        <AvatarIcon avatarId={user.avatarId} />
        <span className="text-sm font-medium text-[var(--text-primary)]">{user.name}</span>
      </button>

      {isOpen && (
        <div 
          role="menu"
          className="absolute bottom-full left-0 mb-2 w-64 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] shadow-2xl z-50"
        >
          {/* Menu contents */}
        </div>
      )}
    </div>
  );
}
```

---

## 3. Four-Theme Dynamic Token System

QuantWeave features 4 distinct visual themes:
1. **Signal Loom**: High-contrast, institutional quantitative terminal (dark charcoal & emerald green).
2. **Daybreak**: Clean, crisp executive daylight interface (light pearl & deep navy).
3. **Nebula**: Deep space quantitative aesthetic (midnight violet & celestial indigo).
4. **Oceanic**: Marine research terminal (deep sea blue & teal accents).

### CSS Custom Properties (`apps/web/app/globals.css`)

Themes are defined as semantic CSS custom properties applied to the `[data-theme]` root attribute:

```css
:root, [data-theme="signal-loom"] {
  --bg-primary: #0a0e14;
  --bg-secondary: #0f1620;
  --bg-card: #141c28;
  --bg-card-hover: #1b2636;
  --border-primary: #1f2d40;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent-primary: #10b981; /* Emerald Green */
  --accent-hover: #059669;
  --color-success: #10b981;
  --color-danger: #ef4444;
}

[data-theme="daybreak"] {
  --bg-primary: #f8fafc;
  --bg-secondary: #f1f5f9;
  --bg-card: #ffffff;
  --bg-card-hover: #e2e8f0;
  --border-primary: #cbd5e1;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --accent-primary: #2563eb; /* Royal Blue */
  --accent-hover: #1d4ed8;
  --color-success: #16a34a;
  --color-danger: #dc2626;
}
```

### Tailwind Token Mapping (`apps/web/tailwind.config.ts`)

Tailwind CSS classes reference these variables directly, allowing dynamic runtime re-theming without regenerating stylesheets:

```typescript
export default {
  theme: {
    extend: {
      colors: {
        background: "var(--bg-primary)",
        card: "var(--bg-card)",
        "card-hover": "var(--bg-card-hover)",
        border: "var(--border-primary)",
        foreground: "var(--text-primary)",
        muted: "var(--text-secondary)",
        primary: "var(--accent-primary)",
      },
    },
  },
};
```

### Dual-Persistence Theme Context (`apps/web/lib/theme-context.tsx`)

Theme selection is persisted both locally in `localStorage` (for instant zero-flicker re-renders upon page reload) and remotely via the backend user preferences API:

```tsx
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("signal-loom");

  useEffect(() => {
    // 1. Read cached theme from localStorage on initial mount
    const saved = localStorage.getItem("qw_theme") as Theme;
    if (saved) {
      setThemeState(saved);
      document.documentElement.setAttribute("data-theme", saved);
    }
  }, []);

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem("qw_theme", newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);

    // 2. Persist to backend database for logged-in user
    try {
      await api.patch("/users/me/preferences", { theme: newTheme });
    } catch {
      // Gracefully fall back to local persistence
    }
  };

  return (
    <ThemeContext.Provider value={{ currentTheme: theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

---

## 4. Type Safety & TypeScript Interfaces

All API requests and responses are strictly typed via shared TypeScript interfaces:

```typescript
// apps/web/lib/types.ts

export interface PortfolioSummary {
  id: string;
  name: string;
  totalValuation: number;
  cashBalance: number;
  investedValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  twrPercent: number;
  xirrPercent: number;
  holdings: HoldingItem[];
}

export interface HoldingItem {
  instrumentId: string;
  ticker: string;
  name: string;
  shares: number;
  averageCost: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  weightPercent: number;
}
```

---

## 5. Viewport-Contained Menus & Accessibility

To prevent clipping on mobile screens (390px) and lower-resolution laptops, the user profile dropdown calculates viewport bounds dynamically before rendering:

- `bottom-full mb-2`: Expands upward from the bottom of the sidebar to prevent cutting off below the screen edge.
- `max-w-[calc(100vw-24px)]`: Prevents horizontal overflow on narrow mobile screens.
- `role="menu"` and `role="menuitem"` ARIA attributes for screen readers.
- Keyboard event listeners ensuring the `Escape` key immediately dismisses open modals and dropdown menus.
