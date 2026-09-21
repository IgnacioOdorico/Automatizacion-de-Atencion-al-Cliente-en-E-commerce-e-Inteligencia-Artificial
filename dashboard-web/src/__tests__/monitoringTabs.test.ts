import { describe, expect, it } from 'vitest';

import { NAV_ITEMS, navItemForPath } from '@/lib/nav';
import {
  DEFAULT_TAB_PATH,
  MONITORING_TABS,
  nextTabIndex,
  tabForPathname,
} from '@/lib/monitoringTabs';

describe('MONITORING_TABS', () => {
  it('En vivo primero (es la pestaña por defecto) y Conversaciones después', () => {
    expect(MONITORING_TABS.map((t) => [t.path, t.label])).toEqual([
      ['en-vivo', 'En vivo'],
      ['conversaciones', 'Conversaciones'],
    ]);
    expect(DEFAULT_TAB_PATH).toBe('en-vivo');
  });
});

describe('tabForPathname (la pestaña vive en la URL)', () => {
  it('reconoce cada sub-ruta', () => {
    expect(tabForPathname('/monitoreo/en-vivo').path).toBe('en-vivo');
    expect(tabForPathname('/monitoreo/conversaciones').path).toBe('conversaciones');
  });

  it('tolera la barra final', () => {
    expect(tabForPathname('/monitoreo/conversaciones/').path).toBe('conversaciones');
  });

  it('/monitoreo a secas o una sub-ruta desconocida caen en la pestaña por defecto', () => {
    expect(tabForPathname('/monitoreo').path).toBe('en-vivo');
    expect(tabForPathname('/monitoreo/otra-cosa').path).toBe('en-vivo');
  });
});

describe('nextTabIndex (teclado del tablist: flechas, Inicio y Fin)', () => {
  it('flecha derecha avanza y da la vuelta al final', () => {
    expect(nextTabIndex(0, 'ArrowRight', 3)).toBe(1);
    expect(nextTabIndex(2, 'ArrowRight', 3)).toBe(0);
  });

  it('flecha izquierda retrocede y da la vuelta al principio', () => {
    expect(nextTabIndex(1, 'ArrowLeft', 3)).toBe(0);
    expect(nextTabIndex(0, 'ArrowLeft', 3)).toBe(2);
  });

  it('Home y End saltan a los extremos', () => {
    expect(nextTabIndex(1, 'Home', 3)).toBe(0);
    expect(nextTabIndex(0, 'End', 3)).toBe(2);
  });

  it('cualquier otra tecla no mueve nada', () => {
    expect(nextTabIndex(0, 'Enter', 3)).toBeNull();
    expect(nextTabIndex(0, 'ArrowDown', 3)).toBeNull();
    expect(nextTabIndex(0, 'a', 3)).toBeNull();
  });

  it('con una sola pestaña, o ninguna, nada se mueve', () => {
    expect(nextTabIndex(0, 'ArrowRight', 1)).toBe(0);
    expect(nextTabIndex(0, 'ArrowRight', 0)).toBeNull();
  });
});

describe('navegación lateral: ítem "Monitoreo"', () => {
  it('está en el menú apuntando a /monitoreo', () => {
    const item = NAV_ITEMS.find((i) => i.path === '/monitoreo');
    expect(item?.label).toBe('Monitoreo');
  });

  it('el título de la barra superior sigue a la sección aunque estés en una pestaña', () => {
    expect(navItemForPath('/monitoreo')?.label).toBe('Monitoreo');
    expect(navItemForPath('/monitoreo/en-vivo')?.label).toBe('Monitoreo');
    expect(navItemForPath('/monitoreo/conversaciones')?.label).toBe('Monitoreo');
  });

  it('no confunde rutas que solo empiezan parecido', () => {
    expect(navItemForPath('/monitoreoextra')).toBeUndefined();
    expect(navItemForPath('/pedidos')?.label).toBe('Pedidos');
    expect(navItemForPath('/')).toBeUndefined();
  });
});
