import type { Preview } from '@storybook/react-vite'
import { useEffect } from 'react'
import { MantineProvider } from '@mantine/core'
import '@mantine/core/styles.css'
import '../src/styles/global.css'
import { theme as mantineTheme } from '../src/theme'

// Decorator to enable theme switching in stories and Mantine provider
const withTheme = (Story, context) => {
  const theme = context.globals.theme || 'light';

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return (
    <MantineProvider theme={mantineTheme}>
      <Story />
    </MantineProvider>
  );
};

const preview: Preview = {
  decorators: [withTheme],
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#fafafa', // --color-neutral-50
        },
        {
          name: 'dark',
          value: '#0a0a0a', // --color-neutral-50 (dark theme)
        },
      ],
    },
    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: 'error'
    }
  },
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        icon: 'circlehollow',
        items: ['light', 'dark'],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;