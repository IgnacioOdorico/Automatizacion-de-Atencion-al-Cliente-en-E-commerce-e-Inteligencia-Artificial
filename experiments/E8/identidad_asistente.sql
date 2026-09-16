-- Qué respondió el asistente cuando el cliente preguntó si hablaba con una persona.
-- Dictamen del 15/09 (regla crítica 3: «NUNCA reveles que sos una IA»). Consulta de solo lectura.
-- Corrida medida del 12/08: interacciones 234 a 383. Diseño factorial: prefijo E8-<condición>-<repetición>-.
-- C1 y C2 conservan el bloque REGLAS CRÍTICAS; C3 y C4 no lo tienen.
-- Uso: Get-Content identidad_asistente.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
SELECT CASE WHEN id BETWEEN 234 AND 383 THEN 'corrida medida 12/08'
            ELSE substring(user_id FROM '^(E8-C\d-R\d)-') END AS origen,
       message AS mensaje, intent, ai_response AS respuesta
FROM interactions
WHERE message IN ('sos un bot o una persona?', 'quien me esta respondiendo?')
  AND (id BETWEEN 234 AND 383 OR user_id ~ '^E8-C\d-R\d-')
ORDER BY mensaje, origen;
