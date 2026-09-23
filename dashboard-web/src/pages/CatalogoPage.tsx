import { useState, type FormEvent } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { dashboardApi } from '@/api/endpoints';
import { Pagination } from '@/components/Pagination';
import { QueryView } from '@/components/QueryView';
import { BoxIcon } from '@/components/icons';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { formatCurrency } from '@/lib/format';
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

  const query = useQuery({
    queryKey: ['products', search, page],
    queryFn: () => dashboardApi.products({ search: search || undefined, page }),
    placeholderData: keepPreviousData,
  });
  const { refetch, isFetching } = query;

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

      <QueryView
        query={query}
        loading={<TableSkeleton columns={5} rows={8} />}
        isEmpty={(data) => data.items.length === 0}
        empty={
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
        }
      >
        {(data) => (
          <>
            <div className="table-wrap">
              <table className="table table--stack">
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
                        <td data-label="Producto">
                          <div className="table__cell-main" title={product.name}>
                            {product.name}
                          </div>
                          <div className="table__cell-sub">{product.sku}</div>
                        </td>
                        <td data-label="Categoría">{product.category ?? '—'}</td>
                        <td className="table__num" data-label="Precio">
                          {formatCurrency(product.price)}
                        </td>
                        <td className="table__num" data-label="Stock">
                          {product.stock}
                          <div className="table__cell-sub">mínimo {product.stock_min}</div>
                        </td>
                        <td data-label="Estado">
                          <Badge tone={stock.tone}>{stock.label}</Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <p className="tabla-leyenda">
              El <strong>mínimo</strong> es el punto de reposición: cuando el stock llega a ese
              número, el producto se marca «Stock bajo» y el sistema avisa.
            </p>

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
