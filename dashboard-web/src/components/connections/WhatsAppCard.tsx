import { useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';

import { connectionsApi } from '@/api/endpoints';
import { ChannelCard } from '@/components/connections/ChannelCard';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import {
  channelActions,
  connectionActionError,
  whatsappStatusNote,
  type ChannelCardModel,
} from '@/lib/connections';
import { normalizePhone, validatePhone } from '@/lib/validate';

interface WhatsAppCardProps {
  model: ChannelCardModel;
  /** Refresca GET /connections y /me tras una solicitud. */
  onChanged: () => void;
}

/**
 * WhatsApp Business: la aprobación la resuelve Meta (1-3 días hábiles), así que
 * "Solicitar aprobación" deja el canal en `pending` — el estado honesto de
 * producción, no una conexión simulada. La cuenta seed llega ya `connected`.
 */
export function WhatsAppCard({ model, onChanged }: WhatsAppCardProps) {
  const [formOpen, setFormOpen] = useState(false);
  const [phone, setPhone] = useState('');
  const [fieldError, setFieldError] = useState<string | null>(null);
  const { canConnect } = channelActions(model.channel, model.status);

  const request = useMutation({
    mutationFn: connectionsApi.whatsappRequestApproval,
    onSuccess: () => {
      setFormOpen(false);
      setPhone('');
      onChanged();
    },
  });

  const closeForm = () => {
    setFormOpen(false);
    setFieldError(null);
    request.reset();
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const error = validatePhone(phone);
    setFieldError(error);
    if (error) return;
    request.mutate(normalizePhone(phone));
  };

  const note = whatsappStatusNote(model.status);

  return (
    <ChannelCard
      model={model}
      actions={
        canConnect && !formOpen ? (
          <Button onClick={() => setFormOpen(true)}>Solicitar aprobación</Button>
        ) : null
      }
    >
      {note && !formOpen && (
        <p className="conn-card__note" role="status">
          {note}
        </p>
      )}

      {formOpen && (
        <form className="conn-form" onSubmit={submit} noValidate>
          <Field
            label="Número de WhatsApp"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="+54 9 261 555 1234"
            value={phone}
            error={fieldError}
            onChange={(e) => {
              setPhone(e.target.value);
              if (fieldError) setFieldError(null);
            }}
            autoFocus
          />
          <p className="conn-card__note">
            Usá el formato internacional, con + y código de país. Meta revisa la solicitud y la
            aprueba en 1-3 días hábiles.
          </p>
          {request.isError && (
            <Alert variant="error" role="alert">
              {connectionActionError(request.error, 'whatsapp-request')}
            </Alert>
          )}
          <div className="conn-card__actions">
            <Button type="submit" loading={request.isPending}>
              Enviar solicitud
            </Button>
            <Button variant="ghost" onClick={closeForm} disabled={request.isPending}>
              Cancelar
            </Button>
          </div>
        </form>
      )}
    </ChannelCard>
  );
}
