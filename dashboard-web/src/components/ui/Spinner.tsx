import type { SVGProps } from 'react';

interface SpinnerProps extends SVGProps<SVGSVGElement> {
  size?: number;
}

export function Spinner({ size = 18, ...rest }: SpinnerProps) {
  return (
    <svg
      className="spinner"
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
      {...rest}
    >
      <circle cx="10" cy="10" r="8" stroke="currentColor" strokeOpacity="0.18" strokeWidth="2.5" />
      <path
        d="M10 2a8 8 0 0 1 8 8"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}