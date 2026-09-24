import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/AuthContext';
import { Brand } from '@/components/Brand';
import { CheckIcon } from '@/components/icons';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { validateLogin, type FieldErrors } from '@/lib/validate';
import { friendlyApiError } from '@/lib/messages';

interface LocationState {
  from?: string;
  reason?: string;
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state ?? {}) as LocationState;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const registered = new URLSearchParams(location.search).get('registrado');
  const sessionExpired = state.reason === 'expired';

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);

    const errors = validateLogin({ email, password });
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await login(email, password);
      navigate(state.from ?? '/dashboard', { replace: true });
    } catch (error) {
      setServerError(friendlyApiError(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Brand />
        <div>
          <p className="auth-brand__headline">
            Toda la operación post-venta de tu tienda, en un solo lugar.
          </p>
          <p className="auth-brand__sub">
            Pedidos, reclamos, métricas de atención y canales de contacto
            integrados con tu proceso de venta online.
          </p>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-wrap">
          <h1>Iniciá sesión</h1>
          <p className="auth-form__caption">Ingresá a tu portal de atención.</p>

          {registered && (
            <Alert variant="success" role="alert">
              <CheckIcon />
              Tu cuenta se creó correctamente. Ya podés iniciar sesión.
            </Alert>
          )}
          {sessionExpired && (
            <Alert variant="error" role="alert">
              Tu sesión expiró. Volvé a iniciar sesión.
            </Alert>
          )}
          {serverError && (
            <Alert variant="error" role="alert">
              {serverError}
            </Alert>
          )}

          <form className="auth-card card" onSubmit={handleSubmit} noValidate>
            <Field
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="tu@negocio.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={fieldErrors.email}
            />
            <Field
              label="Contraseña"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={fieldErrors.password}
            />
            <Button type="submit" block loading={submitting}>
              {submitting ? 'Ingresando…' : 'Ingresar'}
            </Button>
          </form>

          <p className="auth-switch">
            ¿Todavía no tenés cuenta? <Link to="/registro">Creá una</Link>
          </p>
        </div>
      </div>
    </div>
  );
}