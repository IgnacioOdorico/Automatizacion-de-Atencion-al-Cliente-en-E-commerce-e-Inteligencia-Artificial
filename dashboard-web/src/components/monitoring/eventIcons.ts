import type { FC, SVGProps } from 'react';

import {
  ActivityIcon,
  BotIcon,
  BoxIcon,
  CheckCircleIcon,
  GearIcon,
  InfoIcon,
  MailIcon,
  MessengerIcon,
  PackageIcon,
  TicketIcon,
  WarningIcon,
  XCircleIcon,
} from '@/components/icons';
import type { EventIconKey, SeverityIconKey } from '@/lib/monitoring';

type Icon = FC<SVGProps<SVGSVGElement>>;

/** Ícono de cada tipo de evento (las claves las define lib/monitoring, sin React). */
export const EVENT_ICONS: Record<EventIconKey, Icon> = {
  package: PackageIcon,
  gear: GearIcon,
  mail: MailIcon,
  message: MessengerIcon,
  bot: BotIcon,
  ticket: TicketIcon,
  stock: BoxIcon,
  activity: ActivityIcon,
};

/** Un ícono distinto por severidad: el color nunca es lo único que la distingue. */
export const SEVERITY_ICONS: Record<SeverityIconKey, Icon> = {
  info: InfoIcon,
  check: CheckCircleIcon,
  warning: WarningIcon,
  error: XCircleIcon,
};
