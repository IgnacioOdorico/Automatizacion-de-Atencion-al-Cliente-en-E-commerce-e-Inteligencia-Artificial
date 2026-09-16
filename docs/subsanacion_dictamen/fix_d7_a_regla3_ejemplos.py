# -*- coding: utf-8 -*-
"""Dictamen del 15/09, grupo A: regla crítica 3 y ejemplos del prompt frente a la base.

  A1. §2.5 describe la regla crítica 3 tal como es —ordena ocultar que el
      asistente es una IA—, la analiza frente al deber de informar el carácter
      automatizado del canal (con el art. 50.1 del Reglamento (UE) 2024/1689 como
      referencia comparada) y declara su contradicción con la entrada «Soporte»
      de la base. §4.4.3 la nombra, §7.1 recomienda eliminarla y el Anexo H la
      advierte. Se agrega la referencia del Reglamento.
  A2. §5.2.5 aplica a los siete ejemplos del prompt la verificación automática de
      datos concretos (experiments/E6/verificar_ejemplos_prompt.py): el ejemplo de
      Córdoba afirma 3 a 5 días hábiles contra 3 a 7 de la base. Se declaran además
      dos compromisos sin cifra. §7.1 y el Anexo H lo recogen.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ A1: §2.5
p = k.reescribir(
    'Existe además un deber que no deriva de la Ley 25.326',
    'Existe además un deber que no deriva de la Ley 25.326 sino de la buena fe en la relación de consumo, y que un '
    'sistema conversacional automatizado debe atender: informar al cliente que está interactuando con un sistema y no '
    'con una persona. En la Unión Europea ese deber ya tiene forma legal: el Reglamento (UE) 2024/1689 exige que los '
    'sistemas de inteligencia artificial destinados a interactuar directamente con personas físicas se diseñen de modo '
    'que estas sepan que interactúan con uno, salvo que resulte evidente por las circunstancias (art. 50.1). La norma no '
    'rige en la Argentina, pero precisa el alcance del deber.')
k.insertar_despues(
    p, p,
    'El prompt medido en este trabajo contraviene ese deber, y no por una cuestión de tono. Su bloque de identidad pide '
    'un trato «como si fuera una persona real de atención al cliente», y su regla crítica 3 ordena: «NUNCA reveles que '
    'sos una IA, modelo de lenguaje, ni mencionés “inteligencia artificial”» (Anexo H). La regla no regula cómo se '
    'expresa el asistente sino qué oculta: el carácter automatizado del canal. Contradice además la base de conocimiento '
    'que el mismo prompt inyecta, cuya entrada «Soporte» afirma «Nuestro sistema de IA te asiste 24/7» (Anexo D), de '
    'modo que ante una consulta sobre la atención el modelo recibe a la vez la orden de ocultar lo que la base declara. '
    'El caso Moffatt v. Air Canada (2024), revisado en la Sección 2.4.1, no se pronunció sobre la identificación del '
    'canal, pero estableció que la empresa responde por lo que su asistente afirma: ocultar que quien responde es un '
    'sistema no reduce esa responsabilidad y le quita al cliente un dato para ponderar la respuesta. La regla es un '
    'defecto de diseño del artefacto medido. Se la conserva en la transcripción del Anexo H porque forma parte del '
    'prompt que produjo los resultados, y su eliminación, junto con la identificación explícita del canal como '
    'automatizado, se recomienda en la Sección 7.1.')

k.insertar_despues(
    'Ramos De Santis, P. (2024).', 'Ley 25.326 de Protección de los Datos Personales.',
    'Reglamento (UE) 2024/1689 del Parlamento Europeo y del Consejo, de 13 de junio de 2024, por el que se establecen '
    'normas armonizadas en materia de inteligencia artificial (Reglamento de Inteligencia Artificial). (2024). Diario '
    'Oficial de la Unión Europea, L, 2024/1689, 12 de julio de 2024. https://eur-lex.europa.eu/eli/reg/2024/1689/oj')

# ------------------------------------------------------------------ A1: §4.4.3, §7.1 y Anexo H
k.reemplazo(
    'diez reglas críticas, entre ellas la de clasificar como reclamo un mensaje ambiguo entre consulta frecuente y reclamo;',
    'diez reglas críticas, entre ellas la de clasificar como reclamo un mensaje ambiguo entre consulta frecuente y '
    'reclamo y la de no revelar que el asistente es una IA (Sección 2.5);')

alinear = k.reescribir(
    'Alinear las reglas del prompt con el contenido de la base de conocimiento',
    'Alinear las reglas del prompt con el contenido de la base de conocimiento, y también sus ejemplos: las reglas '
    'enumeran «horarios de atención» entre los temas de consulta frecuente, pero la base no tiene esa entrada, y ante esa '
    'consulta el modelo inventó un horario; y el ejemplo de envío a Córdoba afirma un plazo de 3 a 5 días hábiles, cuando '
    'la base fija entre 3 y 7 para el resto del país (Sección 5.2.5). Cada tema que las reglas nombran debería tener su '
    'entrada en la base, o una instrucción explícita de derivarlo al equipo; cada dato de un ejemplo debería figurar en '
    'la base, y ningún ejemplo debería comprometer plazos que la tienda no fija; y el incumplimiento de la instrucción de '
    'derivar debería monitorearse como un error de producción.')
k.insertar_despues(
    alinear, alinear,
    'Eliminar la regla crítica 3 del prompt e identificar el canal como automatizado: la regla ordena al modelo no '
    'revelar que es una IA, en contra del deber de informar al cliente que interactúa con un sistema y de la propia base '
    'de conocimiento, que lo declara (Sección 2.5). Un despliegue productivo debería presentarse como asistente '
    'automatizado desde el primer mensaje y ofrecer la derivación a una persona.')

k.reemplazo(
    'tal como las arma el nodo Preparar Contexto FAQ; su contenido es el del Anexo D.',
    'tal como las arma el nodo Preparar Contexto FAQ; su contenido es el del Anexo D. El texto se transcribe tal como '
    'corrió y conserva dos defectos que el trabajo analiza: la regla crítica 3, que ordena ocultar el carácter '
    'automatizado del canal (Sección 2.5), y el ejemplo de envío a Córdoba, cuyo plazo contradice la base de conocimiento '
    '(Sección 5.2.5).')

# ------------------------------------------------------------------ A2: §5.2.5
k.insertar_despues(
    'Los dos casos responden consultas sobre temas que la base no trata', 'Los dos casos responden consultas sobre temas que la base no trata',
    'La misma verificación se aplicó al propio prompt, con el guion verificar_ejemplos_prompt.py. Los siete ejemplos de '
    'respuesta del Anexo H contienen tres datos concretos: dos figuran en la base —entre 3 y 7 días hábiles de envío y '
    '12 meses de garantía— y uno no: el ejemplo de envío a Córdoba afirma que los envíos tardan «entre 3 y 5 días '
    'hábiles», cuando la base fija entre 3 y 7 para el resto del país. El prompt enseña así un dato ausente de la base, '
    'contra su propia instrucción de usar exclusivamente esa información. El plazo no figura en ninguna de las 45 '
    'respuestas de tipo FAQ (Tabla K.1), y la consulta del corpus más parecida al ejemplo, sobre el costo del envío a '
    'Córdoba, se respondió con la información de la base sobre el cálculo del costo en el checkout. Otros dos ejemplos no '
    'contienen cifras, pero comprometen a la tienda con algo que la base no respalda: resolver un reclamo «hoy mismo» y '
    'gestionar «el cambio o reembolso de inmediato». La verificación automática no los alcanza, por el primer límite '
    'que declara la Sección 3.5.7. La corrección de los ejemplos se recomienda en la Sección 7.1.')

k.guardar()
