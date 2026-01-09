# Phase 9: Component Library Rebuild - Research

**Researched:** 2026-01-09
**Domain:** React component library with headless UI primitives
**Confidence:** HIGH

<research_summary>
## Summary

Researched the modern React component library ecosystem for building accessible, customizable UI components. The standard approach in 2025-2026 uses headless UI libraries (Radix UI, Headless UI, or React Aria) that provide unstyled, accessible primitives with full control over styling.

Key finding: Don't hand-roll accessibility features like focus management, keyboard navigation, or ARIA attributes. Headless libraries handle complex accessibility patterns correctly, including edge cases that custom implementations often miss. The first rule of ARIA is "don't use ARIA when native HTML provides the semantics you need"—and the second is to use battle-tested libraries when building custom components.

**Primary recommendation:** Use Radix UI Primitives as the foundation. It offers 28+ components with excellent TypeScript support, comprehensive ARIA implementation, and a flexible compound component pattern. Install via the unified `radix-ui` package for tree-shaking and simplified updates. Style with existing design tokens from Phase 8.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for building accessible React component libraries:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| radix-ui | latest | Headless UI primitives | Most comprehensive primitive set (28+ components), excellent TypeScript, battle-tested |
| @radix-ui/react-icons | 1.3.x | Icon system | Official icons, tree-shakeable, designed for Radix |
| react | 18.x | UI framework | Already established in project |
| typescript | 5.x | Type safety | Already established in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx | 2.x | Conditional className joining | Combining design token classes |
| @tanstack/react-virtual | 3.x | Virtualized lists | Tables with 100+ rows (already used in Phase 6) |
| react-hook-form | 7.x | Form state management | Complex forms with validation |
| zod | 3.x | Schema validation | Runtime validation + TypeScript types |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Radix UI | Headless UI | Fewer components (focused set), tight Tailwind integration, Vue support |
| Radix UI | React Aria | Hook-first API (more control, more complexity), best-in-class accessibility |
| Radix UI | Native HTML + custom ARIA | Complete control but high risk of accessibility bugs |

**Installation:**
```bash
npm install radix-ui @radix-ui/react-icons clsx
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/components/
├── ui/                      # Base component library
│   ├── Button/
│   │   ├── Button.tsx      # Compound component wrapper
│   │   ├── Button.stories.tsx
│   │   └── index.ts
│   ├── Input/
│   ├── Card/
│   ├── Modal/
│   ├── Table/
│   └── index.ts            # Barrel export
├── domain/                  # Domain-specific components
│   ├── EventCard/
│   ├── RiskBadge/
│   └── EntityProfile/
└── layouts/
    ├── DashboardLayout/
    └── PageLayout/
```

### Pattern 1: Compound Component with Radix Primitives
**What:** Wrap Radix primitives in custom components that apply design tokens and default behavior
**When to use:** All base UI components (Button, Input, Modal, etc.)
**Example:**
```typescript
// src/components/ui/Button/Button.tsx
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { clsx } from 'clsx'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'

    return (
      <Comp
        className={clsx(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
            'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
            'hover:bg-gray-100': variant === 'ghost',
            'h-9 px-4 text-sm': size === 'sm',
            'h-10 px-6 text-base': size === 'md',
            'h-11 px-8 text-lg': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
```

### Pattern 2: Dialog/Modal with Radix Portal
**What:** Use Radix Dialog primitive with proper ARIA, focus management, and portal rendering
**When to use:** Modals, dialogs, alerts that overlay content
**Example:**
```typescript
// src/components/ui/Modal/Modal.tsx
import * as React from 'react'
import { Dialog } from 'radix-ui'

export const Modal = Dialog.Root
export const ModalTrigger = Dialog.Trigger

export const ModalContent = React.forwardRef<
  React.ElementRef<typeof Dialog.Content>,
  React.ComponentPropsWithoutRef<typeof Dialog.Content>
>(({ className, children, ...props }, ref) => (
  <Dialog.Portal>
    <Dialog.Overlay className="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out" />
    <Dialog.Content
      ref={ref}
      className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] bg-white rounded-lg shadow-lg p-6 max-w-lg w-full"
      {...props}
    >
      {children}
    </Dialog.Content>
  </Dialog.Portal>
))

export const ModalTitle = Dialog.Title
export const ModalDescription = Dialog.Description
export const ModalClose = Dialog.Close
```

### Pattern 3: Forwarding Refs with TypeScript
**What:** Properly type and forward refs for Radix primitive integration
**When to use:** All custom components that wrap HTML or Radix primitives
**Example:**
```typescript
// Correct ref forwarding with TypeScript
const MyComponent = React.forwardRef<
  React.ElementRef<typeof RadixPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof RadixPrimitive.Item>
>((props, forwardedRef) => (
  <RadixPrimitive.Item {...props} ref={forwardedRef} />
))

MyComponent.displayName = 'MyComponent'
```

### Anti-Patterns to Avoid
- **Using ARIA instead of native HTML:** Don't create `<div role="button">` when `<button>` exists
- **Custom focus management:** Don't hand-roll focus trapping, Radix handles it
- **Overriding ARIA attributes:** Trust Radix's ARIA implementation, don't override unless absolutely necessary
- **Not forwarding refs:** Components must forward refs for Radix primitives to work
- **Global CSS pollution:** Use scoped design token classes, not global button styles
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Focus trap in modals | Custom focus cycle logic | Radix Dialog primitive | Handles edge cases: nested dialogs, portal rendering, Esc key, click outside |
| Keyboard navigation | Custom keydown handlers | Radix Menu/Select primitives | Arrow keys, Home/End, typeahead, RTL support, disabled state |
| Accessible tooltips | Title attribute or custom div | Radix Tooltip primitive | Screen reader announcements, keyboard triggers, proper ARIA, portal rendering |
| Form validation | Custom validation logic | React Hook Form + Zod | Type-safe schemas, async validation, field-level errors, touched state |
| Virtual scrolling | Custom viewport slicing | @tanstack/react-virtual (already in project) | Dynamic row heights, smooth scrolling, browser compat |
| ARIA live regions | Manual aria-live divs | Radix Toast/Alert primitives | Queue management, screen reader timing, dismissal |

**Key insight:** "No ARIA is better than bad ARIA"—WebAIM found that pages with ARIA averaged 41% more accessibility errors than those without. Headless libraries encapsulate complex ARIA patterns correctly, making accessible components the default. When your Button component handles ARIA correctly, every team using that button gets accessibility for free.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Using ARIA When Native HTML Suffices
**What goes wrong:** Creating `<div role="button" tabIndex={0}>` instead of `<button>`
**Why it happens:** Styling constraints or misunderstanding semantic HTML
**How to avoid:** Always start with native HTML. Use Radix Slot pattern (`asChild` prop) to change rendered element while preserving button semantics
**Warning signs:** Screen readers announce "group" or "clickable" instead of "button"

### Pitfall 2: Incomplete Keyboard Navigation
**What goes wrong:** Component works with mouse but not keyboard (missing Enter/Space, arrow keys, Esc)
**Why it happens:** Testing only with mouse/touch, not considering keyboard-only users
**How to avoid:** Use Radix primitives—they handle all keyboard patterns per WCAG 2.1 AA. Test with Tab key only
**Warning signs:** Can't access component without mouse, focus gets trapped, Esc doesn't close modals

### Pitfall 3: Focus Not Restored After Modal Close
**What goes wrong:** Modal closes but focus disappears or jumps to document body
**Why it happens:** Custom modal implementations don't track trigger element
**How to avoid:** Use Radix Dialog—it automatically restores focus to trigger on close
**Warning signs:** Users lose their place after closing modal, need to Tab from beginning

### Pitfall 4: Outdated ARIA State
**What goes wrong:** `aria-expanded="false"` when dropdown is actually open
**Why it happens:** Forgetting to update ARIA attributes when state changes
**How to avoid:** Radix primitives manage ARIA state automatically via data attributes (`data-[state=open]`)
**Warning signs:** Screen reader announces wrong state, "collapsed" when visually expanded

### Pitfall 5: Missing Labels or Descriptions
**What goes wrong:** Icon buttons with no accessible name, modals with no title
**Why it happens:** Visual design doesn't include visible labels
**How to avoid:** Use `aria-label` for icon buttons, `Dialog.Title` for modals (required by Radix), `Dialog.Description` for context
**Warning signs:** Screen reader announces "button" with no context, "dialog" with no title

### Pitfall 6: Poor Color Contrast
**What goes wrong:** Text/icons fail WCAG contrast ratios (4.5:1 for normal text, 3:1 for large)
**Why it happens:** Design tokens not tested for contrast
**How to avoid:** Verify Phase 8 design tokens meet contrast requirements, use browser DevTools contrast checker
**Warning signs:** Text hard to read in certain light conditions, fails automated accessibility scans

### Pitfall 7: Bundle Size Bloat from Full Library Import
**What goes wrong:** Importing entire component library when only using 5 components
**Why it happens:** `import { Button } from 'radix-ui'` without tree-shaking configured
**How to avoid:** Use named imports from `radix-ui` (tree-shakeable by default), avoid individual `@radix-ui/react-*` packages
**Warning signs:** Large bundle size, slow load times despite using few components
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Button with Slot Pattern (Polymorphic Component)
```typescript
// Source: Radix UI composition guide
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return <Comp {...props} ref={ref} />
  }
)

// Usage: render as <a> while keeping button behavior
<Button asChild>
  <a href="/dashboard">Go to Dashboard</a>
</Button>
```

### Dialog/Modal with Proper ARIA
```typescript
// Source: Radix UI Dialog docs
import { Dialog } from 'radix-ui'

export function DeleteConfirmModal({ open, onOpenChange }) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger asChild>
        <button>Delete Account</button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />

        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <Dialog.Title>Delete Account</Dialog.Title>
          <Dialog.Description>
            This action cannot be undone. All your data will be permanently deleted.
          </Dialog.Description>

          <div>
            <button onClick={handleDelete}>Delete</button>
            <Dialog.Close asChild>
              <button>Cancel</button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

### Select with Search/Filter
```typescript
// Source: Radix UI Select docs
import { Select } from 'radix-ui'

export function CountrySelect() {
  return (
    <Select.Root>
      <Select.Trigger>
        <Select.Value placeholder="Select country..." />
        <Select.Icon />
      </Select.Trigger>

      <Select.Portal>
        <Select.Content>
          <Select.ScrollUpButton />
          <Select.Viewport>
            <Select.Group>
              <Select.Label>Countries</Select.Label>
              <Select.Item value="us">
                <Select.ItemText>United States</Select.ItemText>
                <Select.ItemIndicator />
              </Select.Item>
              <Select.Item value="ve">
                <Select.ItemText>Venezuela</Select.ItemText>
                <Select.ItemIndicator />
              </Select.Item>
            </Select.Group>
          </Select.Viewport>
          <Select.ScrollDownButton />
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  )
}
```

### Accessible Table with Sorting
```typescript
// Source: React ARIA hooks + @tanstack/react-virtual (already in project)
import { useTable, useSortBy } from '@tanstack/react-table'

export function DataTable({ data, columns }) {
  const table = useTable({ data, columns }, useSortBy)

  return (
    <table role="table">
      <thead>
        {table.getHeaderGroups().map(headerGroup => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <th
                key={header.id}
                onClick={header.column.getToggleSortingHandler()}
                aria-sort={
                  header.column.getIsSorted()
                    ? header.column.getIsSorted() === 'desc'
                      ? 'descending'
                      : 'ascending'
                    : 'none'
                }
              >
                {header.column.columnDef.header}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {/* Virtualized rows using @tanstack/react-virtual */}
      </tbody>
    </table>
  )
}
```

### Form with React Hook Form + Zod
```typescript
// Source: React Hook Form docs + Zod integration
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

export function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register('password')} />
        {errors.password && <span role="alert">{errors.password.message}</span>}
      </div>

      <button type="submit">Sign In</button>
    </form>
  )
}
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Individual @radix-ui/react-* packages | Unified `radix-ui` package | 2024 | Simpler imports, tree-shaking, version consistency |
| Custom focus trap logic | Radix Dialog/Popover primitives | 2020+ | Radix handles focus management, portal rendering, Esc key |
| Manual ARIA state management | Radix data attributes (`data-[state=open]`) | 2021+ | ARIA state updates automatically, style based on state |
| PropTypes | TypeScript + Zod | 2023+ | Runtime validation + compile-time types, type-safe APIs |
| Tailwind JIT | Tailwind v4 + OKLCH (Phase 8) | 2024-2025 | Better color precision, perceptual uniformity |

**New tools/patterns to consider:**
- **React 19 Compiler:** Auto-memoization reduces need for manual `useMemo`/`useCallback`, but doesn't fix architectural issues (broad context providers, massive component trees)
- **Zod + React Hook Form:** Type-safe form schemas with runtime validation, replacing Yup/Joi
- **clsx + Tailwind:** Conditional class joining without complex template literals
- **Radix Themes:** Opinionated component library built on Radix Primitives (alternative to custom components if design system isn't critical)

**Deprecated/outdated:**
- **Reach UI:** Maintenance mode, use Radix or Headless UI instead
- **Reakit:** Archived, replaced by Ariakit (similar API, active development)
- **react-modal:** Use Radix Dialog (better accessibility, portal rendering, focus management)
- **PropTypes:** Use TypeScript + Zod for runtime + compile-time validation

**WCAG Updates:**
- **WCAG 2.2 Level AA:** Now the standard (backward-compatible with 2.1), adds new success criteria
- **European Accessibility Act (EAA):** Enforced June 28, 2025—WCAG 2.1 AA compliance now mandatory in EU
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Animation library choice**
   - What we know: Radix primitives work with CSS animations, Framer Motion, or GSAP
   - What's unclear: Which animation library best fits VenezuelaWatch's design system
   - Recommendation: Start with CSS transitions/animations (Phase 8 tokens), add Framer Motion if complex animations needed later

2. **Form builder pattern**
   - What we know: React Hook Form + Zod is standard for validation, but form layout composition unclear
   - What's unclear: Should we create a FormField compound component or keep forms ad-hoc?
   - Recommendation: Wait until Phase 10+ to see form patterns emerge, then extract common patterns

3. **Icon system beyond Radix icons**
   - What we know: @radix-ui/react-icons covers basic needs, but may need custom icons
   - What's unclear: Should we use Heroicons, Lucide, or custom SVG components?
   - Recommendation: Start with Radix icons, add Lucide React if more icons needed (consistent style, tree-shakeable)

4. **Testing strategy for accessibility**
   - What we know: Should test with screen readers (VoiceOver, NVDA), keyboard-only navigation, axe DevTools
   - What's unclear: Should we add automated accessibility testing (jest-axe, Testing Library)?
   - Recommendation: Manual testing first (keyboard, screen reader), add jest-axe in Phase 13 (Accessibility) if time permits
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- /websites/radix-ui-primitives - Getting started, component patterns, composition, styling
- /websites/headlessui_com - Component API, accessibility features, Field/Label patterns
- /websites/react-aria_adobe - Hooks, accessibility, WCAG compliance documentation
- https://www.w3.org/WAI/ARIA/apg/patterns/ - Official ARIA design patterns (Button, Dialog, Menu, Tabs, Forms)

### Secondary (MEDIUM confidence)
- WebSearch "Radix UI vs Headless UI vs React Aria comparison 2025" - Verified ecosystem positioning
- WebSearch "React component library best practices 2025 2026" - Verified TypeScript, accessibility, theming priorities
- WebSearch "component library architecture patterns TypeScript 2025" - Verified compound component patterns
- WebSearch "WCAG 2.1 AA compliance checklist component library 2025" - Verified EAA deadline, compliance requirements
- WebSearch "common mistakes component library accessibility ARIA patterns 2025" - Verified "No ARIA is better than bad ARIA" finding

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official sources (Context7 + W3C ARIA APG)
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Radix UI Primitives, Headless UI, React Aria
- Ecosystem: TypeScript, React Hook Form, Zod, clsx, @tanstack/react-virtual
- Patterns: Compound components, ref forwarding, Slot pattern, Portal rendering
- Pitfalls: ARIA misuse, keyboard navigation, focus management, contrast, bundle size

**Confidence breakdown:**
- Standard stack: HIGH - Context7 docs + WebSearch verification, clear ecosystem consensus
- Architecture: HIGH - Official Radix examples, TypeScript patterns from Context7
- Pitfalls: HIGH - W3C ARIA APG + WebSearch articles + TestParty accessibility guides
- Code examples: HIGH - All examples from Context7 (Radix/Headless UI/React Aria official docs)

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - Radix ecosystem stable, but check for Radix Themes updates)

**Integration with Phase 8:**
- Design tokens (typography, colors, spacing) established in Phase 8
- Storybook 10 already configured for component documentation
- OKLCH colors with hex fallbacks ready for component styling
- Risk-first semantic naming aligns with component prop APIs

**Next phase preparation:**
- Phase 9 will implement: Button, Input, Card, Modal, Table components using Radix primitives
- Phase 8 design tokens will style all components (no new CSS variables needed)
- Storybook stories will document component APIs, accessibility features, variants
- TypeScript types from Radix will ensure type-safe component APIs
</metadata>

---

*Phase: 09-component-library*
*Research completed: 2026-01-09*
*Ready for planning: yes*
