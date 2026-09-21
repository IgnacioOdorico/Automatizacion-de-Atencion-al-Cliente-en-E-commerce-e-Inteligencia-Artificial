import type { FC, SVGProps } from 'react';

import { MailIcon, MessengerIcon, SendIcon } from '@/components/icons';
import type { Channel } from '@/types/api';

/** Un solo ícono por canal, el mismo en Conexiones y en Perfil. */
export const CHANNEL_ICONS: Record<Channel, FC<SVGProps<SVGSVGElement>>> = {
  whatsapp: MessengerIcon,
  telegram: SendIcon,
  email: MailIcon,
};
