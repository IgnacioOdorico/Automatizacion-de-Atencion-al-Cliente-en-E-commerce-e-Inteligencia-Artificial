import { MessengerIcon } from '@/components/icons';
import { EmptyState } from '@/components/ui/EmptyState';

export function MonitoreoConversacionesPage() {
  return (
    <EmptyState
      icon={<MessengerIcon width={24} height={24} />}
      title="El bot todavía no atendió mensajes"
      text="Cuando llegue el primero por WhatsApp, Telegram o email lo vas a ver acá."
    />
  );
}
