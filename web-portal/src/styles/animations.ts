/**
 * Centralized Keyframe Animations for Glassmorphism UI
 *
 * Usage with MUI sx prop:
 * sx={{ animation: `${animations.slideInUp} 0.6s ease-out` }}
 *
 * Or use the animation helpers:
 * sx={{ ...animationStyles.slideInUp(0.1) }}
 */

// Animation keyframes as CSS strings for use in @keyframes
export const keyframes = {
  // Entry animations
  slideInUp: `
    @keyframes slideInUp {
      0% {
        opacity: 0;
        transform: translateY(30px);
      }
      100% {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,

  slideInDown: `
    @keyframes slideInDown {
      0% {
        opacity: 0;
        transform: translateY(-30px);
      }
      100% {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,

  slideInRight: `
    @keyframes slideInRight {
      0% {
        opacity: 0;
        transform: translateX(30px);
      }
      100% {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,

  slideInLeft: `
    @keyframes slideInLeft {
      0% {
        opacity: 0;
        transform: translateX(-30px);
      }
      100% {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,

  // Exit animations
  slideOutRight: `
    @keyframes slideOutRight {
      0% {
        opacity: 1;
        transform: translateX(0);
      }
      100% {
        opacity: 0;
        transform: translateX(30px);
      }
    }
  `,

  // General animations
  fadeIn: `
    @keyframes fadeIn {
      0% {
        opacity: 0;
      }
      100% {
        opacity: 1;
      }
    }
  `,

  fadeOut: `
    @keyframes fadeOut {
      0% {
        opacity: 1;
      }
      100% {
        opacity: 0;
      }
    }
  `,

  // Status indicator animations
  pulse: `
    @keyframes pulse {
      0% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.7;
        transform: scale(1.1);
      }
      100% {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,

  ripple: `
    @keyframes ripple {
      0% {
        transform: scale(1);
        opacity: 0.4;
      }
      100% {
        transform: scale(2.5);
        opacity: 0;
      }
    }
  `,

  // Button ripple effect
  buttonRipple: `
    @keyframes buttonRipple {
      0% {
        transform: scale(0);
        opacity: 0.5;
      }
      100% {
        transform: scale(4);
        opacity: 0;
      }
    }
  `,

  // Loading animations
  shimmer: `
    @keyframes shimmer {
      0% {
        background-position: -200% 0;
      }
      100% {
        background-position: 200% 0;
      }
    }
  `,

  spin: `
    @keyframes spin {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }
  `,

  // Glow animation
  glow: `
    @keyframes glow {
      0% {
        box-shadow: 0 0 5px rgba(255, 153, 0, 0.2), 0 0 10px rgba(255, 153, 0, 0.1);
      }
      50% {
        box-shadow: 0 0 15px rgba(255, 153, 0, 0.4), 0 0 25px rgba(255, 153, 0, 0.2);
      }
      100% {
        box-shadow: 0 0 5px rgba(255, 153, 0, 0.2), 0 0 10px rgba(255, 153, 0, 0.1);
      }
    }
  `,

  // Scale animations
  scaleIn: `
    @keyframes scaleIn {
      0% {
        opacity: 0;
        transform: scale(0.9);
      }
      100% {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,

  // Bounce effect
  bounce: `
    @keyframes bounce {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-5px);
      }
    }
  `,

  // Checkmark animation for success states
  checkmark: `
    @keyframes checkmark {
      0% {
        stroke-dashoffset: 100;
      }
      100% {
        stroke-dashoffset: 0;
      }
    }
  `,

  // Progress bar animation
  progressFill: `
    @keyframes progressFill {
      0% {
        width: 0%;
      }
    }
  `,

  // Toast progress bar
  progressShrink: `
    @keyframes progressShrink {
      0% {
        width: 100%;
      }
      100% {
        width: 0%;
      }
    }
  `,

  // Sparkle effect for value changes
  sparkle: `
    @keyframes sparkle {
      0%, 100% {
        opacity: 0;
        transform: scale(0.5);
      }
      50% {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,
}

// Animation timing presets
export const timing = {
  // Durations
  instant: '0.1s',
  fast: '0.15s',
  normal: '0.3s',
  slow: '0.6s',
  verySlow: '1s',

  // For continuous animations
  pulse: '2s',
  shimmer: '1.5s',
  ripple: '0.6s',

  // Easing functions
  easeOut: 'ease-out',
  easeIn: 'ease-in',
  easeInOut: 'ease-in-out',
  linear: 'linear',
  // Custom cubic bezier for bouncy feel
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  // Smooth deceleration
  decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
  // Smooth acceleration
  accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
}

// Pre-built animation style objects for MUI sx prop
export const animationStyles = {
  // Entry animations with optional delay
  slideInUp: (delay: number = 0) => ({
    animation: `slideInUp ${timing.slow} ${timing.easeOut} ${delay}s both`,
    '@keyframes slideInUp': {
      '0%': { opacity: 0, transform: 'translateY(30px)' },
      '100%': { opacity: 1, transform: 'translateY(0)' },
    },
  }),

  slideInDown: (delay: number = 0) => ({
    animation: `slideInDown ${timing.slow} ${timing.easeOut} ${delay}s both`,
    '@keyframes slideInDown': {
      '0%': { opacity: 0, transform: 'translateY(-30px)' },
      '100%': { opacity: 1, transform: 'translateY(0)' },
    },
  }),

  slideInRight: (delay: number = 0) => ({
    animation: `slideInRight ${timing.normal} ${timing.easeOut} ${delay}s both`,
    '@keyframes slideInRight': {
      '0%': { opacity: 0, transform: 'translateX(30px)' },
      '100%': { opacity: 1, transform: 'translateX(0)' },
    },
  }),

  slideInLeft: (delay: number = 0) => ({
    animation: `slideInLeft ${timing.normal} ${timing.easeOut} ${delay}s both`,
    '@keyframes slideInLeft': {
      '0%': { opacity: 0, transform: 'translateX(-30px)' },
      '100%': { opacity: 1, transform: 'translateX(0)' },
    },
  }),

  fadeIn: (delay: number = 0) => ({
    animation: `fadeIn ${timing.normal} ${timing.easeInOut} ${delay}s both`,
    '@keyframes fadeIn': {
      '0%': { opacity: 0 },
      '100%': { opacity: 1 },
    },
  }),

  scaleIn: (delay: number = 0) => ({
    animation: `scaleIn ${timing.normal} ${timing.easeOut} ${delay}s both`,
    '@keyframes scaleIn': {
      '0%': { opacity: 0, transform: 'scale(0.9)' },
      '100%': { opacity: 1, transform: 'scale(1)' },
    },
  }),

  // Continuous animations
  pulse: {
    animation: `pulse ${timing.pulse} ${timing.easeInOut} infinite`,
    '@keyframes pulse': {
      '0%': { opacity: 1, transform: 'scale(1)' },
      '50%': { opacity: 0.7, transform: 'scale(1.1)' },
      '100%': { opacity: 1, transform: 'scale(1)' },
    },
  },

  shimmer: {
    backgroundImage: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)',
    backgroundSize: '200% 100%',
    animation: `shimmer ${timing.shimmer} ${timing.linear} infinite`,
    '@keyframes shimmer': {
      '0%': { backgroundPosition: '-200% 0' },
      '100%': { backgroundPosition: '200% 0' },
    },
  },

  spin: {
    animation: `spin 1s ${timing.linear} infinite`,
    '@keyframes spin': {
      '0%': { transform: 'rotate(0deg)' },
      '100%': { transform: 'rotate(360deg)' },
    },
  },

  // Ripple animation for buttons
  rippleEffect: {
    animation: `ripple ${timing.ripple} ${timing.easeOut}`,
    '@keyframes ripple': {
      '0%': { transform: 'scale(1)', opacity: 0.4 },
      '100%': { transform: 'scale(2.5)', opacity: 0 },
    },
  },
}

// Hover transition presets
export const hoverTransitions = {
  lift: {
    transition: `all ${timing.fast} ${timing.easeOut}`,
    '&:hover': {
      transform: 'translateY(-4px)',
    },
  },

  scale: {
    transition: `transform ${timing.fast} ${timing.easeOut}`,
    '&:hover': {
      transform: 'scale(1.02)',
    },
    '&:active': {
      transform: 'scale(0.98)',
    },
  },

  glow: (color: string = '#FF9900') => ({
    transition: `all ${timing.fast} ${timing.easeOut}`,
    '&:hover': {
      boxShadow: `0 4px 20px ${color}30`,
    },
  }),

  border: (color: string = '#FF9900') => ({
    transition: `border-color ${timing.fast} ${timing.easeOut}`,
    '&:hover': {
      borderColor: `${color}60`,
    },
  }),

  all: (color: string = '#FF9900') => ({
    transition: `all ${timing.fast} ${timing.easeOut}`,
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: `0 8px 25px ${color}25`,
      borderColor: `${color}50`,
    },
    '&:active': {
      transform: 'translateY(-2px) scale(0.99)',
    },
  }),
}

// Stagger delay helper for lists
export const staggerDelay = (index: number, baseDelay: number = 0.1): number => {
  return index * baseDelay
}

export default {
  keyframes,
  timing,
  animationStyles,
  hoverTransitions,
  staggerDelay,
}
