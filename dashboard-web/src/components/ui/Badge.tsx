import type { HTMLAttributes } from 'react';

type Tone = 'brand' | 'neutral' | 'success' | 'warning' | 'danger' | 'computed';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = 'neutral', children, className, ...rest }: BadgeProps) {
  return (
    <span className={`badge badge--${tone} ${className ?? ''}`.trim()} {...rest}>
      {children}
    </span>
  );
}