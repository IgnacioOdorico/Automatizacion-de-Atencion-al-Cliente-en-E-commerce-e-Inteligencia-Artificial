import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';

import {
  gmailReturnNotice,
  parseGmailReturn,
  type ChannelCardModel,
  type ConnectionNotice,
  type GmailReturn,
} from '@/lib/connections';

/**
 * Vuelta desde Google: lee `?gmail=` una sola vez, limpia el query de la URL
 * (para que un refresh no repita el aviso) y arma el aviso apenas llegan los
 * datos de GET /connections. El aviso queda fijo hasta que el usuario actúa.
 */
export function useGmailReturn(gmailCard: ChannelCardModel, dataLoaded: boolean) {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [returned] = useState<GmailReturn | null>(() => parseGmailReturn(location.search));
  const [notice, setNotice] = useState<ConnectionNotice | null>(null);
  const [resolved, setResolved] = useState(false);

  useEffect(() => {
    if (returned && location.search) {
      navigate('/conexiones', { replace: true });
    }
  }, [returned, location.search, navigate]);

  useEffect(() => {
    if (!returned || resolved) return;
    const next = gmailReturnNotice(returned, gmailCard, dataLoaded);
    if (next) {
      setNotice(next);
      setResolved(true);
      // Perfil y sidebar leen los canales desde /me.
      void queryClient.invalidateQueries({ queryKey: ['me'] });
    }
  }, [returned, resolved, gmailCard, dataLoaded, queryClient]);

  const dismiss = useCallback(() => setNotice(null), []);

  return { notice, dismiss };
}
