import type { FC, SVGProps } from 'react';

import {
  ActivityIcon,
  BoxIcon,
  GridIcon,
  PackageIcon,
  PlugIcon,
  TicketIcon,
  UserIcon,
} from '@/components/icons';

export interface NavItem {
  path: string;
  label: string;
  icon: FC<SVGProps<SVGSVGElement>>;
}

export const NAV_ITEMS: NavItem[] = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: GridIcon,
  },
  {
    path: '/pedidos',
    label: 'Pedidos',
    icon: PackageIcon,
  },
  {
    path: '/tickets',
    label: 'Tickets',
    icon: TicketIcon,
  },
  {
    path: '/catalogo',
    label: 'Catálogo',
    icon: BoxIcon,
  },
  {
    path: '/monitoreo',
    label: 'Monitoreo',
    icon: ActivityIcon,
  },
  {
    path: '/conexiones',
    label: 'Conexiones',
    icon: PlugIcon,
  },
  {
    path: '/perfil',
    label: 'Perfil',
    icon: UserIcon,
  },
];

export function navItemForPath(pathname: string): NavItem | undefined {
  // Las secciones con pestañas (/monitoreo/en-vivo) siguen perteneciendo a su ítem.
  return NAV_ITEMS.find((item) => pathname === item.path || pathname.startsWith(`${item.path}/`));
}