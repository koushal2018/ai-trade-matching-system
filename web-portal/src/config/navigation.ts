import type { SideNavigationProps } from '@cloudscape-design/components'

export const navigationItems: SideNavigationProps.Item[] = [
  {
    type: 'section',
    text: 'Dashboard',
    items: [
      {
        type: 'link',
        text: 'Overview',
        href: '/dashboard',
      },
      {
        type: 'link',
        text: 'Real-time Monitor',
        href: '/monitor',
      },
    ],
  },
  {
    type: 'section',
    text: 'Trade Processing',
    items: [
      {
        type: 'link',
        text: 'Upload Confirmations',
        href: '/upload',
      },
      {
        type: 'link',
        text: 'Matching Queue',
        href: '/queue',
      },
      {
        type: 'link',
        text: 'Exceptions',
        href: '/exceptions',
      },
    ],
  },
  {
    type: 'section',
    text: 'Review',
    items: [
      {
        type: 'link',
        text: 'HITL Panel',
        href: '/hitl',
      },
      {
        type: 'link',
        text: 'Audit Trail',
        href: '/audit',
      },
    ],
  },
]
