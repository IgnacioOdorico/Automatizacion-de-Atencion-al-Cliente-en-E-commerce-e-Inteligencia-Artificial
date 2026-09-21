import { CheckIcon } from '@/components/icons';
import { Select, type SelectOption } from '@/components/ui/Select';
import { CHANNEL_LABELS } from '@/lib/format';
import { EVENT_TYPE_OPTIONS } from '@/lib/monitoring';
import type { Channel } from '@/types/api';
import type { EventType } from '@/types/monitoring';

const CHANNEL_OPTIONS: SelectOption[] = [
  { value: '', label: 'Todos los canales' },
  ...(['whatsapp', 'telegram', 'email'] as const).map((value) => ({
    value,
    label: CHANNEL_LABELS[value],
  })),
];

interface EventFiltersProps {
  types: readonly EventType[];
  onTypesChange: (types: EventType[]) => void;
  channel: Channel | '';
  onChannelChange: (channel: Channel | '') => void;
}

function FilterChip({
  pressed,
  onClick,
  children,
}: {
  pressed: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button type="button" className="mon-chip" aria-pressed={pressed} onClick={onClick}>
      {pressed && <CheckIcon width={13} height={13} aria-hidden="true" />}
      {children}
    </button>
  );
}

/**
 * Filtros del feed: chips de tipo (multi-selección; "Todos" los limpia) y canal.
 * Los chips encendidos llevan una tilde además del color.
 */
export function EventFilters({ types, onTypesChange, channel, onChannelChange }: EventFiltersProps) {
  const toggle = (type: EventType) => {
    onTypesChange(types.includes(type) ? types.filter((t) => t !== type) : [...types, type]);
  };

  return (
    <>
      <div className="mon-filters">
        <div className="mon-chips" role="group" aria-label="Filtrar por tipo de evento">
          <FilterChip pressed={types.length === 0} onClick={() => onTypesChange([])}>
            Todos
          </FilterChip>
          {EVENT_TYPE_OPTIONS.map((option) => (
            <FilterChip
              key={option.value}
              pressed={types.includes(option.value)}
              onClick={() => toggle(option.value)}
            >
              {option.label}
            </FilterChip>
          ))}
        </div>
        <Select
          label="Canal"
          value={channel}
          options={CHANNEL_OPTIONS}
          onChange={(e) => onChannelChange(e.target.value as Channel | '')}
        />
      </div>
      {channel && (
        <p className="mon-hint">
          Los pedidos y las alertas de stock no tienen canal, por eso no aparecen al filtrar por
          canal.
        </p>
      )}
    </>
  );
}
