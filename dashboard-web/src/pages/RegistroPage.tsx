import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/AuthContext';
import { Brand } from '@/components/Brand';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { validateRegister, type FieldErrors } from '@/lib/validate';
import { friendlyApiError } from '@/lib/messages';

export function RegistroPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [businessName, setBusinessName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);

    const errors = validateRegister({ business_name: businessName, email, password });
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await register({ business_name: businessName, email, password });
      navigate('/login?registrado=1', { replace: true });
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
            Creá tu cuenta y empezá a seguir tu atención al cliente.
          </p>
          <p className="auth-brand__sub">
            Accedé a métricas en tiempo real, pedidos, reclamos y la conexión de
            tus canales de contacto.
          </p>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-wrap">
          <h1>Creá tu cuenta</h1>
          <p className="auth-form__caption">Es gratis y lleva menos de un minuto.</p>

          {serverError && (
            <Alert variant="error" role="alert">
              {serverError}
            </Alert>
          )}

          <form className="auth-card card" onSubmit={handleSubmit} noValidate>
            <Field
              label="Nombre del negocio"
              autoComplete="organization"
              placeholder="ej. TecnoShop Mendoza"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              error={fieldErrors.business_name}
            />
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
              autoComplete="new-password"
              placeholder="Mínimo 8 caracteres"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={fieldErrors.password}
            />
            <Button type="submit" block loading={submitting}>
              {submitting ? 'Creando cuenta…' : 'Crear cuenta'}
            </Button>
          </form>

          <p className="auth-switch">
            ¿Ya tenés cuenta? <Link to="/login">Iniciá sesión</Link>
          </p>
        </div>
      </div>
    </div>
  );
}