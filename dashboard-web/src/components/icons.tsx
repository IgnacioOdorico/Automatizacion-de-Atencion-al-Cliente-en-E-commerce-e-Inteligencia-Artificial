import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

const base = (props: IconProps) => ({
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  ...props,
});

export const GridIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);

export const PackageIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z" />
    <path d="M3 7.5 12 12l9-4.5" />
    <path d="M12 12v9" />
  </svg>
);

export const TicketIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2 2 2 0 0 0 0 6 2 2 0 0 1-2 2H5a2 2 0 0 1-2-2 2 2 0 0 0 0-6z" />
    <rect x="10.5" y="7" width="3" height="10" rx="0.5" />
  </svg>
);

export const BoxIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M21 8 12 3 3 8v8l9 5 9-5z" />
    <path d="M3 8l9 5 9-5" />
    <path d="M12 13v8" />
    <path d="M7 5.5l10 5.5" />
  </svg>
);

export const PlugIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M9 7V3" />
    <path d="M15 7V3" />
    <path d="M5 11h14" />
    <path d="M6 11v3a6 6 0 0 0 12 0v-3" />
  </svg>
);

export const UserIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-3.5 3.6-6 8-6s8 2.5 8 6" />
  </svg>
);

export const LogoutIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <path d="M16 17l5-5-5-5" />
    <path d="M21 12H9" />
  </svg>
);

export const AlertIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v4" />
    <path d="M12 16h.01" />
  </svg>
);

export const CheckIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

export const MessengerIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M21 12a8 8 0 0 1-8 8H4l2.2-2.6A8 8 0 1 1 21 12z" />
    <path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" />
  </svg>
);

export const SendIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M21 3 10.5 13.5" />
    <path d="M21 3l-6.5 18-4-7.5L3 9.5z" />
  </svg>
);

export const MailIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="m3.5 6.5 8.5 6.5 8.5-6.5" />
  </svg>
);

export const RefreshIcon = (props: IconProps) => (
  <svg {...base(props)}>
    <path d="M3 12a9 9 0 0 1 15.4-6.4" />
    <path d="M21 12a9 9 0 0 1-15.4 6.4" />
    <path d="M4 2v4h4" />
    <path d="M20 22v-4h-4" />
  </svg>
);

/** Marca "TS" del portal */
export const BrandMark = ({ size = 34 }: { size?: number }) => (
  <span className="brand__mark" style={{ width: size, height: size }}>
    <svg
      width={size * 0.52}
      height={size * 0.52}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M6 19V5h2.6l6.8 8V5H18v14h-2.6L8.6 11v8z" />
    </svg>
  </span>
);