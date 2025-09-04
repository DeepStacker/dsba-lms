// DSBA LMS Theme Configuration
// Modern, professional theme for educational management system

export const theme = {
  // Color Palette - Professional Academic Theme
  colors: {
    // Primary Colors - Deep Blue Academic
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554'
    },
    
    // Secondary Colors - Warm Gray
    secondary: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712'
    },

    // Success Colors - Green
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d'
    },

    // Warning Colors - Amber
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f'
    },

    // Error Colors - Red
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d'
    },

    // Info Colors - Cyan
    info: {
      50: '#ecfeff',
      100: '#cffafe',
      200: '#a5f3fc',
      300: '#67e8f9',
      400: '#22d3ee',
      500: '#06b6d4',
      600: '#0891b2',
      700: '#0e7490',
      800: '#155e75',
      900: '#164e63'
    }
  },

  // Typography
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      serif: ['Playfair Display', 'Georgia', 'serif'],
      mono: ['JetBrains Mono', 'Monaco', 'monospace']
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
      '6xl': '3.75rem'
    },
    fontWeight: {
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800'
    },
    lineHeight: {
      tight: '1.25',
      snug: '1.375',
      normal: '1.5',
      relaxed: '1.625',
      loose: '2'
    }
  },

  // Spacing
  spacing: {
    px: '1px',
    0: '0',
    0.5: '0.125rem',
    1: '0.25rem',
    1.5: '0.375rem',
    2: '0.5rem',
    2.5: '0.625rem',
    3: '0.75rem',
    3.5: '0.875rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    7: '1.75rem',
    8: '2rem',
    9: '2.25rem',
    10: '2.5rem',
    11: '2.75rem',
    12: '3rem',
    14: '3.5rem',
    16: '4rem',
    20: '5rem',
    24: '6rem',
    28: '7rem',
    32: '8rem',
    36: '9rem',
    40: '10rem',
    44: '11rem',
    48: '12rem',
    52: '13rem',
    56: '14rem',
    60: '15rem',
    64: '16rem',
    72: '18rem',
    80: '20rem',
    96: '24rem'
  },

  // Border Radius
  borderRadius: {
    none: '0',
    sm: '0.125rem',
    DEFAULT: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px'
  },

  // Shadows
  boxShadow: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: 'none'
  },

  // Component-specific styles
  components: {
    // Button variants
    button: {
      primary: {
        bg: 'bg-primary-600',
        hover: 'hover:bg-primary-700',
        text: 'text-white',
        ring: 'focus:ring-primary-500'
      },
      secondary: {
        bg: 'bg-secondary-100',
        hover: 'hover:bg-secondary-200',
        text: 'text-secondary-900',
        ring: 'focus:ring-secondary-500'
      },
      success: {
        bg: 'bg-success-600',
        hover: 'hover:bg-success-700',
        text: 'text-white',
        ring: 'focus:ring-success-500'
      },
      warning: {
        bg: 'bg-warning-600',
        hover: 'hover:bg-warning-700',
        text: 'text-white',
        ring: 'focus:ring-warning-500'
      },
      danger: {
        bg: 'bg-error-600',
        hover: 'hover:bg-error-700',
        text: 'text-white',
        ring: 'focus:ring-error-500'
      }
    },

    // Card styles
    card: {
      base: 'bg-white rounded-lg shadow-sm border border-secondary-200',
      hover: 'hover:shadow-md transition-shadow duration-200',
      padding: 'p-6'
    },

    // Input styles
    input: {
      base: 'block w-full rounded-md border-secondary-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
      error: 'border-error-300 focus:border-error-500 focus:ring-error-500',
      success: 'border-success-300 focus:border-success-500 focus:ring-success-500'
    },

    // Modal styles
    modal: {
      overlay: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4',
      content: 'bg-white rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto',
      header: 'px-6 py-4 border-b border-secondary-200',
      body: 'px-6 py-4',
      footer: 'px-6 py-4 border-t border-secondary-200 flex justify-end space-x-3'
    }
  },

  // Animation & Transitions
  animation: {
    duration: {
      fast: '150ms',
      normal: '200ms',
      slow: '300ms'
    },
    easing: {
      ease: 'ease',
      easeIn: 'ease-in',
      easeOut: 'ease-out',
      easeInOut: 'ease-in-out'
    }
  },

  // Breakpoints
  screens: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px'
  },

  // Z-index layers
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    toast: 1080
  }
};

// CSS Custom Properties for dynamic theming
export const cssVariables = {
  '--color-primary': theme.colors.primary[600],
  '--color-primary-hover': theme.colors.primary[700],
  '--color-secondary': theme.colors.secondary[600],
  '--color-success': theme.colors.success[600],
  '--color-warning': theme.colors.warning[600],
  '--color-error': theme.colors.error[600],
  '--color-info': theme.colors.info[600],
  '--font-family-sans': theme.typography.fontFamily.sans.join(', '),
  '--font-family-serif': theme.typography.fontFamily.serif.join(', '),
  '--font-family-mono': theme.typography.fontFamily.mono.join(', '),
  '--border-radius': theme.borderRadius.DEFAULT,
  '--shadow': theme.boxShadow.DEFAULT,
  '--transition-duration': theme.animation.duration.normal,
  '--transition-easing': theme.animation.easing.easeInOut
};

export default theme;