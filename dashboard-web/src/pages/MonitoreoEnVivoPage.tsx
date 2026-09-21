import { ActivityIcon } from '@/components/icons';
import { EmptyState } from '@/components/ui/EmptyState';

export function MonitoreoEnVivoPage() {
  return (
    <EmptyState
      icon={<ActivityIcon width={24} height={24} />}
      title="El bot todavía no tiene actividad"
      text="Cuando llegue un pedido o un mensaje de un cliente, lo vas a ver acá en el momento."
    />
  );
}
