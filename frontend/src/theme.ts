import { createTheme } from '@mantine/core'

/**
 * Custom Mantine theme configuration
 *
 * Breakpoints based on responsive design research:
 * - xs: 576px - Mobile devices
 * - sm: 768px - Tablets portrait
 * - md: 992px - Tablets landscape / small laptops
 * - lg: 1200px - Desktops
 * - xl: 1408px - Large desktops
 */
export const theme = createTheme({
  breakpoints: {
    xs: '36em', // 576px
    sm: '48em', // 768px
    md: '62em', // 992px
    lg: '75em', // 1200px
    xl: '88em', // 1408px
  },
})
