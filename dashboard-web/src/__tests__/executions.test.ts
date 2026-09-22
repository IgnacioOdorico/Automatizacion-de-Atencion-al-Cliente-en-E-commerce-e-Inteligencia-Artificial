import { describe, expect, it } from 'vitest';

import {
  EXECUTION_STATUS_FILTERS,
  executionModeLabel,
  executionStatusMeta,
  mergeExecutionPages,
  pickDefaultWorkflow,
  traceStatusMeta,
  workflowStats,
} from '@/lib/executions';

import { makeExecution, makeWorkflowSummary } from './helpers/workflowFixtures';

describe('executionStatusMeta', () => {
  it('cada estado tiene etiqueta en español, tono e ícono (nunca solo color)', () => {
    expect(executionStatusMeta('success')).toEqual({ label: 'Correcta', tone: 'success', icon: 'check' });
    expect(executionStatusMeta('error')).toMatchObject({ label: 'Con error', tone: 'danger', icon: 'error' });
    expect(executionStatusMeta('crashed')).toMatchObject({ label: 'Interrumpida', tone: 'danger', icon: 'error' });
    expect(executionStatusMeta('running')).toMatchObject({ label: 'En curso', tone: 'brand' });
    expect(executionStatusMeta('waiting')).toMatchObject({ label: 'En espera', tone: 'warning' });
    expect(executionStatusMeta('canceled')).toMatchObject({ label: 'Cancelada', tone: 'neutral' });
    expect(executionStatusMeta('new')).toMatchObject({ label: 'En cola', tone: 'neutral' });
  });

  it('un estado desconocido se muestra tal cual, en neutro', () => {
    expect(executionStatusMeta('rara')).toEqual({ label: 'rara', tone: 'neutral', icon: 'info' });
    expect(executionStatusMeta('constructor').icon).toBe('info');
  });
});

describe('traceStatusMeta (estado de un nodo en una ejecución)', () => {
  it('etiquetas legibles', () => {
    expect(traceStatusMeta('success').label).toBe('Correcto');
    expect(traceStatusMeta('error').label).toBe('Con error');
    expect(traceStatusMeta('skipped').label).toBe('No se ejecutó');
    expect(traceStatusMeta('running').label).toBe('En curso');
    expect(traceStatusMeta('waiting').label).toBe('En espera');
    expect(traceStatusMeta('canceled').label).toBe('Cancelado');
    expect(traceStatusMeta('missing').label).toBe('Sin datos en esta ejecución');
  });

  it('cada uno con su ícono y tono', () => {
    expect(traceStatusMeta('success')).toMatchObject({ tone: 'success', icon: 'check' });
    expect(traceStatusMeta('error')).toMatchObject({ tone: 'danger', icon: 'error' });
    expect(traceStatusMeta('skipped')).toMatchObject({ tone: 'neutral', icon: 'skip' });
  });

  it('un estado raro cae en "No se ejecutó" en vez de afirmar un éxito', () => {
    expect(traceStatusMeta('otra-cosa')).toMatchObject({ label: 'No se ejecutó', icon: 'skip' });
  });
});

describe('executionModeLabel', () => {
  it('traduce los modos de ejecución a palabras del cliente', () => {
    expect(executionModeLabel('webhook')).toBe('Entrada de datos');
    expect(executionModeLabel('trigger')).toBe('Disparador');
    expect(executionModeLabel('manual')).toBe('Manual');
    expect(executionModeLabel('retry')).toBe('Reintento');
  });

  it('un modo desconocido o vacío no rompe', () => {
    expect(executionModeLabel('otro')).toBe('otro');
    expect(executionModeLabel('')).toBe('—');
  });
});

describe('EXECUTION_STATUS_FILTERS', () => {
  it('"Todas" primero, con valor vacío, y los estados con sus nombres', () => {
    expect(EXECUTION_STATUS_FILTERS[0]).toEqual({ value: '', label: 'Todas' });
    const values = EXECUTION_STATUS_FILTERS.map((f) => f.value);
    expect(values).toEqual(expect.arrayContaining(['success', 'error', 'crashed', 'running']));
    const labels = EXECUTION_STATUS_FILTERS.map((f) => f.label);
    expect(new Set(labels).size).toBe(labels.length);
  });
});

describe('mergeExecutionPages ("cargar más")', () => {
  it('une la página fresca con lo cargado a pedido, sin duplicados y de la más nueva a la más vieja', () => {
    const first = [makeExecution(20), makeExecution(19), makeExecution(18)];
    const more = [makeExecution(18), makeExecution(17), makeExecution(16)];
    expect(mergeExecutionPages(first, more).map((e) => e.id)).toEqual([20, 19, 18, 17, 16]);
  });

  it('lo más reciente pisa: el estado de una ejecución que estaba en curso se actualiza', () => {
    const first = [makeExecution(20, { status: 'success' })];
    const more = [makeExecution(20, { status: 'running' })];
    expect(mergeExecutionPages(first, more)[0].status).toBe('success');
  });

  it('sin páginas extra devuelve la primera', () => {
    const first = [makeExecution(2), makeExecution(1)];
    expect(mergeExecutionPages(first, [])).toEqual(first);
  });
});

describe('pickDefaultWorkflow (cuál se muestra al entrar)', () => {
  const at = (id: number, startedAt: string) => ({ id, status: 'success', started_at: startedAt, duration_ms: 10 });

  it('el activo con la ejecución más reciente', () => {
    const items = [
      makeWorkflowSummary('a', 'A', { last_execution: at(1, '2026-09-21T10:00:00.000Z') }),
      makeWorkflowSummary('b', 'B', { last_execution: at(2, '2026-09-21T12:00:00.000Z') }),
      makeWorkflowSummary('c', 'C', { last_execution: at(3, '2026-09-21T11:00:00.000Z') }),
    ];
    expect(pickDefaultWorkflow(items)).toBe('b');
  });

  it('prefiere uno activo aunque otro inactivo haya corrido después', () => {
    const items = [
      makeWorkflowSummary('a', 'A', { active: true, last_execution: at(1, '2026-09-21T10:00:00.000Z') }),
      makeWorkflowSummary('b', 'B', { active: false, last_execution: at(2, '2026-09-21T12:00:00.000Z') }),
    ];
    expect(pickDefaultWorkflow(items)).toBe('a');
  });

  it('un activo sin ejecuciones pierde contra uno activo que ya corrió', () => {
    const items = [
      makeWorkflowSummary('a', 'A', { last_execution: null }),
      makeWorkflowSummary('b', 'B', { last_execution: at(2, '2026-09-21T12:00:00.000Z') }),
    ];
    expect(pickDefaultWorkflow(items)).toBe('b');
  });

  it('si ninguno tiene actividad, el primero activo (el orden de la API es por nombre)', () => {
    const items = [
      makeWorkflowSummary('a', 'A', { active: false, last_execution: null }),
      makeWorkflowSummary('b', 'B', { last_execution: null }),
      makeWorkflowSummary('c', 'C', { last_execution: null }),
    ];
    expect(pickDefaultWorkflow(items)).toBe('b');
  });

  it('si ninguno está activo, el de actividad más reciente y, si no, el primero', () => {
    const items = [
      makeWorkflowSummary('a', 'A', { active: false, last_execution: at(1, '2026-09-21T10:00:00.000Z') }),
      makeWorkflowSummary('b', 'B', { active: false, last_execution: at(2, '2026-09-21T12:00:00.000Z') }),
    ];
    expect(pickDefaultWorkflow(items)).toBe('b');
    expect(pickDefaultWorkflow([makeWorkflowSummary('z', 'Z', { active: false, last_execution: null })])).toBe('z');
  });

  it('sin workflows no hay elección', () => {
    expect(pickDefaultWorkflow([])).toBeNull();
  });
});

describe('workflowStats (resumen de las últimas 24 h)', () => {
  it('cuenta ejecuciones y errores', () => {
    expect(workflowStats(makeWorkflowSummary('a', 'A', { executions_24h: 12, errors_24h: 1 }))).toBe(
      '12 ejecuciones en 24 h · 1 con error',
    );
    expect(workflowStats(makeWorkflowSummary('a', 'A', { executions_24h: 3, errors_24h: 2 }))).toBe(
      '3 ejecuciones en 24 h · 2 con error',
    );
  });

  it('en singular y sin errores', () => {
    expect(workflowStats(makeWorkflowSummary('a', 'A', { executions_24h: 1, errors_24h: 0 }))).toBe(
      '1 ejecución en 24 h · sin errores',
    );
  });

  it('sin actividad lo dice', () => {
    expect(workflowStats(makeWorkflowSummary('a', 'A', { executions_24h: 0, errors_24h: 0 }))).toBe(
      'Sin ejecuciones en las últimas 24 h',
    );
  });
});
