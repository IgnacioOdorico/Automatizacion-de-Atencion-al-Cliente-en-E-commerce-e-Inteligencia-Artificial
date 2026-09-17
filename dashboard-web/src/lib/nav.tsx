import type { FC, SVGProps } from 'react';

import {
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
  description: string;
}

export const NAV_ITEMS: NavItem[] = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: GridIcon,
    description: 'Resumen en vivo de las métricas de atención: pedidos, tiempos de respuesta y tickets abiertos.',
  },
  {
    path: '/pedidos',
    label: 'Pedidos',
    icon: PackageIcon,
    description: 'Órdenes que entran por el pipeline post-venta, con su estado de procesamiento.',
  },
  {
    path: '/tickets',
    label: 'Tickets',
    icon: TicketIcon,
    description: 'Reclamos y consultas derivados del chatbot omnicanal, por estado.',
  },
  {
    path: '/catalogo',
    label: 'Catálogo',
    icon: BoxIcon,
    description: 'Productos activos con stock y precios sincronizados con la tienda.',
  },
  {
    path: '/conexiones',
    label: 'Conexiones',
    icon: PlugIcon,
    description: 'Estado de los canales de atención: WhatsApp, Telegram y Gmail.',
  },
  {
    path: '/perfil',
    label: 'Perfil',
    icon: UserIcon,
    description: 'Datos de tu cuenta y el estado de tus canales conectados.',
  },
];

export function navItemForPath(pathname: string): NavItem | undefined {
  return NAV_ITEMS.find((item) => item.path === pathname);
}