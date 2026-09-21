/**
 * Qué es cada nodo de n8n para quien mira el diagrama: un ícono y un tipo en
 * palabras del cliente. Se decide por `short_type` (webhook, postgres, if...).
 * Lógica pura: las claves de ícono las resuelve components/workflow/nodeIcons.
 */

export type NodeIconKey =
  | 'webhook'
  | 'trigger'
  | 'database'
  | 'branch'
  | 'switch'
  | 'mail'
  | 'send'
  | 'globe'
  | 'code'
  | 'reply'
  | 'edit'
  | 'merge'
  | 'clock'
  | 'ai'
  | 'node';

export interface NodeKind {
  label: string;
  icon: NodeIconKey;
}

const KINDS: Record<string, NodeKind> = {
  webhook: { label: 'Webhook (entrada de datos)', icon: 'webhook' },
  postgres: { label: 'Base de datos (PostgreSQL)', icon: 'database' },
  if: { label: 'Condición (Sí / No)', icon: 'branch' },
  switch: { label: 'Bifurcación (Switch)', icon: 'switch' },
  emailSend: { label: 'Envío de email', icon: 'mail' },
  gmail: { label: 'Gmail', icon: 'mail' },
  telegram: { label: 'Mensaje de Telegram', icon: 'send' },
  httpRequest: { label: 'Llamada HTTP', icon: 'globe' },
  code: { label: 'Código', icon: 'code' },
  function: { label: 'Código (función)', icon: 'code' },
  functionItem: { label: 'Código (función por item)', icon: 'code' },
  respondToWebhook: { label: 'Respuesta al webhook', icon: 'reply' },
  set: { label: 'Asignar datos', icon: 'edit' },
  merge: { label: 'Unir ramas', icon: 'merge' },
  wait: { label: 'Espera', icon: 'clock' },
  noOp: { label: 'Sin operación', icon: 'node' },
  chainLlm: { label: 'Cadena de IA (modelo de lenguaje)', icon: 'ai' },
  agent: { label: 'Agente de IA', icon: 'ai' },
  lmChatOpenAi: { label: 'Modelo de lenguaje (OpenAI)', icon: 'ai' },
};

const TRIGGERS: Record<string, string> = {
  telegramTrigger: 'Disparador de Telegram',
  gmailTrigger: 'Disparador de Gmail',
  scheduleTrigger: 'Disparador programado',
  manualTrigger: 'Disparador manual',
};

const GENERIC: NodeIconKey = 'node';

/** Ícono y etiqueta legible de un nodo; un tipo desconocido o inexistente no rompe nada. */
export function nodeKind(shortType: string | null | undefined): NodeKind {
  if (!shortType) return { label: 'Nodo que ya no existe en el workflow', icon: GENERIC };
  if (Object.prototype.hasOwnProperty.call(KINDS, shortType)) return KINDS[shortType];
  if (shortType.endsWith('Trigger')) {
    const label = Object.prototype.hasOwnProperty.call(TRIGGERS, shortType)
      ? TRIGGERS[shortType]
      : `Disparador (${shortType})`;
    return { label, icon: 'trigger' };
  }
  return { label: `Nodo (${shortType})`, icon: GENERIC };
}
