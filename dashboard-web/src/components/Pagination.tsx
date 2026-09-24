import { Button } from '@/components/ui/Button';

interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

/** Paginado simple (offset) compartido por Pedidos/Tickets/Catálogo. */
export function Pagination({ page, totalPages, total, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <span className="pagination__info">
        {total} registro{total === 1 ? '' : 's'} · Página {page} de {totalPages}
      </span>
      <div className="pagination__controls">
        <Button variant="ghost" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          ← Anterior
        </Button>
        <Button variant="ghost" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
          Siguiente →
        </Button>
      </div>
    </div>
  );
}