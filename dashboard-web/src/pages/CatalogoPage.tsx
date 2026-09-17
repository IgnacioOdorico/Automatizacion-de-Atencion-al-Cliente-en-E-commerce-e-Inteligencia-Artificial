import { useState, type FormEvent } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { Pagination } from '@/components/Pagination';
import { BoxIcon } from '@/components/icons';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCurrency } from '@/lib/format';
import { friendlyApiError } from '@/lib/messages';
import type { Product } from '@/types/api';

function stockBadge(product: Product): { label: string; tone: 'success' | 'warning' | 'danger' } {
  if (product.stock <= 0) return { label: 'Sin stock', tone: 'danger' };
  if (product.stock <= product.stock_min) return { label: 'Stock bajo', tone: 'warning' };
  return { label: 'En stock', tone: 'success' };
}

/**
 * Catálogo (GET /products): búsqueda ILIKE por nombre/SKU en el backend y
 * paginado de 20. Refresco manual (spec metrics: solo Dashboard/Pedidos pollean).
 */
export function CatalogoPage() {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['products', search, page],
    queryFn: () => dashboardApi.products({ search: search || undefined, page }),
    placeholderData: keepPreviousData,
  });

  const submitSearch = (e: FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  };

  const clearSearch = () => {
    setSearchInput('');
    setSearch('');
    setPage(1);
  };

  return (
    <div className="page">
      <header className="page__head page__head--row">
        <div>
          <h1>Catálogo</h1>
          <p className="page__sub">
            Productos activos con stock y precios sincronizados con la tienda.
          </p>
        </div>
        <Button variant="ghost" onClick={() => refetch()} loading={isFetching}>
          Actualizar
        </Button>
      </header>

      <form className="filters" onSubmit={submitSearch}>
        <div className="search-row">
          <input
            className="field__input"
            type="search"
            placeholder="Buscar por nombre o SKU…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Buscar productos"
          />
          <Button type="submit">Buscar</Button>
          {search && (
            <Button type="button" variant="ghost" onClick={clearSearch}>
              Limpiar
            </Button>
          )}
        </div>
      </form>

      {isError && (
        <Alert variant="error" role="alert">
          {friendlyApiError(error)}
        </Alert>
      )}

      {isPending && <div className="skeleton" style={{ height: 320, borderRadius: 16 }} />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<BoxIcon width={24} height={24} />}
          title={search ? `Sin resultados para "${search}"` : 'Catálogo vacío'}
          text={
            search
              ? 'Probá con otro término o limpiá la búsqueda para ver todos los productos.'
              : 'Los productos cargados en la tienda aparecen acá.'
          }
          action={
            search ? (
              <Button variant="ghost" onClick={clearSearch}>
                Limpiar búsqueda
              </Button>
            ) : undefined
          }
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Categoría</th>
                  <th className="table__num">Precio</th>
                  <th className="table__num">Stock</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((product) => {
                  const stock = stockBadge(product);
                  return (
                    <tr key={product.id}>
                      <td>
                        <div className="table__cell-main">{product.name}</div>
                        <div className="table__cell-sub">{product.sku}</div>
                      </td>
                      <td>{product.category ?? '—'}</td>
                      <td className="table__num">{formatCurrency(product.price)}</td>
                      <td className="table__num">
                        {product.stock}
                        <div className="table__cell-sub">mín. {product.stock_min}</div>
                      </td>
                      <td>
                        <Badge tone={stock.tone}>{stock.label}</Badge>
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
    </div>
  );
}