import { NAV_ITEMS } from '@/lib/nav';
import { PlaceholderPage } from '@/components/PlaceholderPage';

export function CatalogoPage() {
  const item = NAV_ITEMS[3];
  return <PlaceholderPage item={item} />;
}