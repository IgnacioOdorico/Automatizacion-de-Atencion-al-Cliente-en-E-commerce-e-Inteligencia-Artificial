export type FieldErrors = Record<string, string>;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(value: string): string | null {
  const email = value.trim();
  if (!email) return 'Ingresá tu email.';
  if (!EMAIL_RE.test(email)) return 'El formato del email no es válido.';
  if (email.length > 200) return 'El email es demasiado largo.';
  return null;
}

export function validatePassword(value: string, minLen = 8): string | null {
  if (!value) return 'Ingresá tu contraseña.';
  if (value.length < minLen) return `Debe tener al menos ${minLen} caracteres.`;
  if (value.length > 128) return 'La contraseña es demasiado larga.';
  return null;
}

export function validateBusinessName(value: string): string | null {
  const name = value.trim();
  if (!name) return 'Ingresá el nombre de tu negocio.';
  if (name.length > 200) return 'El nombre es demasiado largo.';
  return null;
}

export function validateLogin(input: { email: string; password: string }): FieldErrors {
  const errors: FieldErrors = {};
  const email = validateEmail(input.email);
  if (email) errors.email = email;
  const password = validatePassword(input.password, 1);
  if (password) errors.password = password;
  return errors;
}

export function validateRegister(input: {
  business_name: string;
  email: string;
  password: string;
}): FieldErrors {
  const errors: FieldErrors = {};
  const businessName = validateBusinessName(input.business_name);
  if (businessName) errors.business_name = businessName;
  const email = validateEmail(input.email);
  if (email) errors.email = email;
  const password = validatePassword(input.password, 8);
  if (password) errors.password = password;
  return errors;
}