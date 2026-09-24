import { useQueryClient } from '@tanstack/react-query';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';

import {
  clearSessionExpiredHandler,
  setSessionExpiredHandler,
} from '@/api/client';
import { authApi } from '@/api/endpoints';
import { tokenStorage } from '@/auth/tokenStorage';
import type { RegisterResponse } from '@/types/api';

type SessionStatus = 'loading' | 'ready';

interface AuthContextValue {
  status: SessionStatus;
  hasSession: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    business_name: string;
    email: string;
    password: string;
  }) => Promise<RegisterResponse>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SessionStatus>('loading');
  const [hasSession, setHasSession] = useState<boolean>(
    () => !!tokenStorage.getAccessToken(),
  );

  const handleSessionExpired = useCallback(() => {
    tokenStorage.clear();
    queryClient.clear();
    setHasSession(false);
    setStatus('ready');
    navigate('/login', { replace: true, state: { reason: 'expired' } });
  }, [navigate, queryClient]);

  useEffect(() => {
    setSessionExpiredHandler(handleSessionExpired);
    setStatus('ready');
    return () => clearSessionExpiredHandler();
  }, [handleSessionExpired]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login({ email, password });
      tokenStorage.setTokens(tokens);
      queryClient.clear();
      setHasSession(true);
    },
    [queryClient],
  );

  const register = useCallback(
    async (input: {
      business_name: string;
      email: string;
      password: string;
    }) => {
      const account = await authApi.register(input);
      // register NO devuelve tokens (verificado en backend): no hay auto-login,
      // se redirige a /login con mensaje de éxito (spec auth).
      return account;
    },
    [],
  );

  const logout = useCallback(() => {
    tokenStorage.clear();
    queryClient.clear();
    setHasSession(false);
    navigate('/login', { replace: true });
  }, [navigate, queryClient]);

  const value = useMemo(
    () => ({ status, hasSession, login, register, logout }),
    [status, hasSession, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return ctx;
}