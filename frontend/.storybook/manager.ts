import { addons } from 'storybook/manager-api';
import { create } from 'storybook/theming';

/**
 * Custom Storybook theme using VenezuelaWatch design tokens
 * Matches the risk-first color palette and typography scale
 */
const venezuelaWatchTheme = create({
  base: 'light',

  // Branding
  brandTitle: 'VenezuelaWatch Design System',
  brandUrl: '/',
  brandTarget: '_self',

  // Colors from design tokens (OKLCH converted to hex for Storybook compatibility)
  colorPrimary: '#dc2626',   // --color-risk-high
  colorSecondary: '#16a34a', // --color-risk-low

  // UI colors (neutral palette)
  appBg: '#fafafa',           // --color-neutral-50
  appContentBg: '#ffffff',    // white
  appBorderColor: '#e5e5e5',  // --color-neutral-200
  appBorderRadius: 6,         // --radius-md

  // Typography colors
  textColor: '#171717',       // --color-neutral-900
  textInverseColor: '#fafafa', // --color-neutral-50
  textMutedColor: '#737373',  // --color-neutral-500

  // Toolbar colors
  barTextColor: '#737373',
  barSelectedColor: '#dc2626',
  barBg: '#ffffff',

  // Form colors
  inputBg: '#ffffff',
  inputBorder: '#e5e5e5',
  inputTextColor: '#171717',
  inputBorderRadius: 6,

  // Typography (system font stack)
  fontBase: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontCode: 'ui-monospace, "SF Mono", "Fira Code", "Cascadia Code", "Roboto Mono", monospace',
});

addons.setConfig({
  theme: venezuelaWatchTheme,
});
