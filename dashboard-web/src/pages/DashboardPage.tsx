import { NAV_ITEMS } from '@/lib/nav';
import { PlaceholderPage } from '@/components/PlaceholderPage';

export function DashboardPage() {
  const item = NAV_ITEMS[0];
  return <PlaceholderPage item={item} />;
}