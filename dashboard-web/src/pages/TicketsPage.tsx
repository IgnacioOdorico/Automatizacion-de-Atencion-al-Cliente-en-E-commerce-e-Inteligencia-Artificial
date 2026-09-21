import { useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { Pagination } from '@/components/Pagination';
import { QueryView } from '@/components/QueryView';
import { RefreshIcon, TicketIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Select, type SelectOption } from '@/components/ui/Select';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { TICKET_STATUSES, priorityMeta, ticketStatusMeta } from '@/lib/domain';
import { CHANNEL_LABELS, formatDateTime } from '@/lib/format';

const STATUS_OPTIONS: SelectOption[] = [
  { value: '', label: 'Todos los estados' },
  ...TICKET_STATUSES.map((status) => ({ value: status, label: ticketStatusMeta(status).label })),
];

/**
 * Tickets (GET /tickets): el estado "resuelto" se deriva de `status`, nunca de
 * `resolved_at` (el workflow lo deja NULL). Un resolved sin fecha se muestra
 * normal, sin tratarlo como error.
 */
export function TicketsPage() {
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);

  const query = useQuery({
    queryKey: ['tickets', statusFilter, page],
    queryFn: () => dashboardApi.tickets({ status: statusFilter || undefined, page }),
    placeholderData: keepPreviousData,
  });
  const { refetch, isFetching } = query;

  const changeStatus = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const filterMeta = statusFilter ? ticketStatusMeta(statusFilter) : null;

  return (
    <div className="page">
      <header className="page__head page__head--row">
        <div>
          <h1>Tickets</h1>
          <p className="page__sub">
            Reclamos y consultas derivados del chatbot omnicanal, con canal, prioridad y estado.
          </p>
        </div>
        <Button variant="ghost" onClick={() => refetch()} loading={isFetching}>
          <RefreshIcon width={16} height={16} />
          Actualizar
        </Button>
      </header>

      <div className="filters">
        <Select
          label="Estado"
          value={statusFilter}
          options={STATUS_OPTIONS}
          onChange={(e) => changeStatus(e.target.value)}
        />
      </div>

      <QueryView
        query={query}
        loading={<TableSkeleton columns={6} rows={5} />}
        isEmpty={(data) => data.items.length === 0}
        empty={
          <EmptyState
            icon={<TicketIcon width={24} height={24} />}
            title={
              filterMeta ? `Sin tickets en estado "${filterMeta.label}"` : 'Sin tickets todavía'
            }
            text={
              filterMeta
                ? 'Probá con otro estado o quitá el filtro para ver todos los tickets.'
                : 'Los reclamos y consultas que derive el chatbot aparecen acá con su canal y prioridad.'
            }
          />
        }
      >
        {(data) => (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Asunto</th>
                    <th>Canal</th>
                    <th>Prioridad</th>
                    <th>Estado</th>
                    <th>Creado</th>
                    <th>Resuelto</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((ticket) => {
                    const status = ticketStatusMeta(ticket.status);
                    const priority = priorityMeta(ticket.priority);
                    return (
                      <tr key={ticket.id}>
                        <td>
                          <div className="table__cell-main">{ticket.subject ?? '—'}</div>
                          {ticket.user_id && (
                            <div className="table__cell-sub">{ticket.user_id}</div>
                          )}
                        </td>
                        <td>{CHANNEL_LABELS[ticket.channel] ?? ticket.channel}</td>
                        <td>
                          <Badge tone={priority.tone}>{priority.label}</Badge>
                        </td>
                        <td>
                          <Badge tone={status.tone}>{status.label}</Badge>
                        </td>
                        <td className="table__dates">{formatDateTime(ticket.created_at)}</td>
                        <td className="table__dates">
                          {ticket.resolved_at ? (
                            formatDateTime(ticket.resolved_at)
                          ) : ticket.status === 'resolved' ? (
                            <span className="table__cell-sub">Cerrado sin fecha registrada</span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              total={data.total}
              onPageChange={setPage}
            />
          </>
        )}
      </QueryView>
    </div>
  );
}
