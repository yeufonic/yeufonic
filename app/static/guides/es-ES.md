# Yeufonic — la guía

Esto trata de **usar** la aplicación. La instalación, y todo lo que necesitas antes de que funcione, está en el
[README](https://github.com/yeufonic/yeufonic#readme).

La aplicación escribe canciones con YuE2, un modelo que trabaja en dos pasos: primero escribe un **plan de partitura** —
la melodía, los acordes y las secciones, como texto — y después **renderiza** ese plan en audio.
Casi todo lo que sigue se deriva de esa división. Un plan cuesta segundos y se puede leer, editar y
desechar; un render cuesta minutos. Por eso la aplicación te deja ver el plan primero.

---

## Tu primera canción {#your-first-song}

1. Pulsa **+ Canción** en la parte superior del panel izquierdo. Se abre la ventana del editor.
2. **Escribe un estilo.** Una frase, no una lista de etiquetas: *«warm indie rock, expressive female lead, jangly
   guitars, 96 BPM»*. Es lo que más influye en el resultado.
3. **Añade una letra**, o pulsa **Escribir letra** y deja que Gemma la redacte a partir de una descripción.
4. Pulsa **Escribir plan de partitura**. La ventana se cierra y la toma aparece en el panel izquierdo. Con
   **Renderizar en cuanto el plan esté listo** marcado junto al botón, como está al principio, el plan
   pasa directamente a su render.

Para leer el plan antes de que se renderice nada, desmarca primero **Renderizar en cuanto el plan esté listo**. La
toma se detiene entonces en su plan: ábrela, y en su página **Partitura**, **Escribir un plan nuevo** vuelve a tirar los dados con una melodía que no
te guste por el precio de unos segundos, y **Renderizar esta partitura** la renderiza. Una toma que aún no tiene audio
se completa; una que ya tiene audio se renderiza como una toma nueva a su lado, así que un render nunca
sobrescribe una que quieras conservar.

La toma aparece en la biblioteca a la derecha y suena en la barra inferior.

### El panel de la toma y el editor {#the-take-panel-and-the-editor}

El **panel izquierdo** muestra la última toma en la que hiciste clic, solo para leer: su estilo, sus ajustes de sonido, las
primeras líneas de su letra, y su partitura como tonalidad, tempo, duración y los acordes de cada sección.
**+ Canción**, **+ Versión** y **+ Instrumental** arriba empiezan algo nuevo; el del tipo de
la toma destaca. El chevrón junto al panel lo pliega, para que las tomas tengan el ancho,
y lo trae de vuelta. Teclas sueltas actúan sobre la toma que muestra el panel (M para el rack de masterización, E para
el editor y más): consulta [Atajos de teclado](#hot-keys).

Crear y cambiar una toma se hace en la **ventana del editor**. Su botón principal en el panel dice lo que
corresponde: *Editar y renderizar de nuevo*, o *Revisar el plan y renderizar* cuando hay un plan esperando. Los botones
**Partitura** y **Otra vez** de una tarjeta también lo abren, igual que un doble clic en una tarjeta. Tiene tres
columnas (la canción, la letra y el sonido), todo a la vista, con la partitura en una pestaña propia.

Cerrar la ventana, con **Cerrar**, la cruz o Escape, conserva lo que escribiste.

El botón después de **Cerrar**, en la esquina superior derecha, hace que la ventana ocupe toda la ventana del navegador, y
un segundo clic la devuelve a su tamaño habitual. La ventana se abre como la dejaste la última vez. Al ocupar toda la ventana,
la columna de la letra toma toda su altura: el cuadro de la letra (cuando ya tiene palabras) y la estructura crecen en
el espacio, y el reproductor se queda al pie de la columna.

La fila superior de la ventana tiene, más grandes, los botoncitos de la tarjeta de la toma: Cantar de nuevo, Variaciones,
Probar más, Dentro, Sacar, Normalizar y Mover, cada uno donde lo mostraría la tarjeta. Normalizar está en verde
mientras la toma está normalizada, y un clic la devuelve entonces al nivel con que se renderizó; Dentro
se ilumina mientras la toma contiene otras, y cierra la ventana para mostrarlas bajo la toma.

### Una voz grabada {#a-recorded-voice}

Una toma puede cantarse con una voz entrenada a partir de una **grabación** de alguien cantando: la tuya, o la de un corpus.
Elígela en el campo *Voz grabada* del editor, o entrena una con **Crear una voz…** a partir de un archivo de audio de canto. Bastan unos
minutos; una grabación con acompañamiento se separa primero. Cada tarjeta de corpus también tiene un botón **Crear una voz…**, que
entrena una voz con las canciones del corpus. El campo solo aparece si el servicio de voces opcional está en marcha
("Recorded voices" en el README).

El entrenamiento espera su turno en la GPU y puede tardar una hora; la lista muestra su progreso. Una toma con una voz se
renderiza como siempre; luego su voz se separa, se vuelve a cantar con la voz y se mezcla de nuevo sobre el resto, antes
de medir su nivel.

**Octava** sube o baja una voz una octava entera. Una voz cantada lejos de su registro suena mal, y solo una octava entera
mantiene el canto en la tonalidad del acompañamiento. Se guarda en la voz. **Regenerar** vuelve a entrenar la voz: una voz
de corpus con las canciones del corpus tal como están ahora.

El resultado es un canto convertido sobre un acompañamiento separado, así que es menos uniforme que un canto que el modelo
cantó por sí mismo. Grabaciones más limpias, sin pérdida en lugar de MP3, dan una voz más limpia. La receta de una toma
nombra su voz, y al importarla se usa la voz con ese nombre en esta instalación, si la hay.

### Ajustes avanzados {#advanced-settings}

El botón **Avanzado** en la cabecera del editor abre ajustes solo para esta toma. La mayoría de las canciones
nunca los necesitan. Se guardan con la toma, así que *Editar y renderizar de nuevo* los encuentra como los dejaste.
El botón se ilumina cuando algún ajuste difiere de su valor por defecto, y **Restablecer valores** los devuelve
todos.

Algunos actúan sobre el plan, y otros sobre el render y el archivo final:

- **Pasos de difusión** (16–64, por defecto 32): cuántos pasos da el decodificador de audio. Más pasos tardan
  más en renderizar.
- **Seguir el estilo** (0–100, por defecto 1.0): con cuánta firmeza sigue la música el estilo y la letra, la guía
  de la etapa que convierte la partitura en sonido (CFG). Por encima de 1.0 se acerca más a ellos; por debajo, se aleja. La
  diferencia es sutil con valores pequeños, y un render tarda un poco más. Se puede introducir cualquier valor que acepte el motor:
  una guía muy alta tiende a sonar áspera más que más fiel. Se muestra cuando el motor lo tiene: yue2.cpp, o el motor ComfyUI
  en su versión más reciente (reconstruye un motor Docker antiguo para tenerlo).
- **Evitar:** palabras de las que alejarse, como «drums» o «rap vocals». Se añaden al estilo
  como «avoid: …». Es una pista para el planificador, no una garantía: el renderizador no tiene prompt negativo.
- **Fijar tonalidad:** el plan se traslada a esta tonalidad una vez que el planificador lo ha escrito. El planificador ignora
  una tonalidad nombrada en el estilo, así que esto se hace sobre la propia partitura: cada nota y cada acorde se desplaza el
  mismo intervalo y se reescribe la armadura. Un plan menor sigue siendo menor, y solo se mueve
  la tónica. Un plan que la aplicación no puede leer con certeza, como uno en un modo o con un cambio de tonalidad
  a mitad, se queda en la tonalidad del planificador y el registro lo indica.
- **Fijar tempo** (BPM): el plan se fija a este tempo, que sustituye a cualquier tempo del estilo o de la
  propia partitura del planificador, y el render lo sigue.
- **Límite de tokens de la partitura** (por defecto 8192): lo máximo que puede escribir el planificador. Un límite más bajo impide que el plan de una canción corta
  se alargue.
- **Límite de acorde sostenido** (compases, por defecto 8): el máximo de compases que el planificador se queda en una misma fundamental antes
  de tener que cambiar.
- **Bonificación de armonía fuera de tono** (0–10, por defecto 0): con cuánta fuerza se empuja al planificador hacia acordes
  prestados y fundamentales fuera de la tonalidad principal. Estos dos actúan sobre las elecciones del planificador, así que se ven como
  una diferencia en los acordes del plan más que como una diferencia clara al oído. Compara en la ventana
  Partitura.
- **Las voces siguen las indicaciones** (una casilla bajo el cuadro de la letra, que aparece cuando la letra tiene una indicación de voz como
  `[male voice]`; activada para una toma nueva): la melodía de cada línea indicada se mueve por octavas a donde se canta la voz que
  nombra su indicación. Consulta [La letra](#the-words).
- **Seguir esta estructura exactamente** (una casilla bajo el cuadro de la letra, no en Avanzado; canciones; desactivada por defecto): el plan escribe exactamente las secciones que nombra la letra, en
  orden, y ninguna más. Desactivada, el planificador da forma a la canción por su cuenta y a menudo añade una intro, un outro o un
  interludio, o deja fuera una sección. Un plan puede aun así terminar antes que la lista.
- **Las secciones empiezan distinto** (Seguir la armonía, Siempre, Nunca): si una sección puede empezar con los mismos
  acordes que la anterior. *Seguir la armonía* lo activa a partir de Colorida y lo deja desactivado por debajo; *Siempre* y
  *Nunca* deciden para esta toma en cualquier nivel, para comparar dos planes con y sin.
- **Volumen objetivo:** el nivel al que se normaliza una toma. Solo se aplica cuando la normalización está activada.
- **Fundido final** (segundos, por defecto 3): la duración del fundido cuando una toma se corta en el límite de
  duración.

### Qué poner en el cuadro Estilo {#what-to-put-in-the-style-box}

YuE2 lee esto como la descripción de una grabación, así que describe una grabación. Idioma, género, voz,
instrumentos, ambiente, tempo y producción, más o menos en ese orden, todo en una frase. Las listas de etiquetas sueltas
funcionan peor, y los marcadores de sección como `[Verse]` van en la letra, no aquí.

Los chips **Voz** de debajo escriben en el estilo por ti: femenina, masculina o dúo, y un carácter
como aireada o rasgada. Son un atajo para escribir, y puedes editar el resultado a mano.

### Redactar la letra {#drafting-the-lyrics}

**La estructura.** Encima del cuadro de la letra, mientras no tenga palabras, una canción tiene una **estructura** que construir, como
un instrumental: una lista de secciones que puedes reordenar, quitar y ampliar (intro, estrofa, preestribillo, estribillo, puente,
interludio, outro). **Empezar con…** la llena con una forma habitual, y la descripción emergente de cada forma dice para qué sirve. Un
**interludio** es un pasaje instrumental: el autor pone su etiqueta en una línea propia, y el planificador lo toca con
la voz instrumental. **Poner secciones en el cuadro de la letra** inserta las etiquetas como secciones vacías bajo las que escribir a mano.
En cuanto el cuadro tiene palabras, se canta la letra y la estructura se aparta.

**Escribir letra**, junto al cuadro de la letra, pregunta de qué trata la canción y escribe palabras para las secciones que construiste.
**Versos por estrofa o estribillo** fija lo larga que es cada una: más líneas en una sección dan una canción más larga, porque el
planificador escribe más o menos tanta música como palabras hay. El estilo de arriba marca el ambiente. Gemma escribe el borrador en el mismo
motor, y llega al cuadro con un título si no habías dado uno; un [LLM externo](#external-llm) puede escribirla en su lugar, configurado en Configuración. La ventana se cierra en cuanto empieza el borrador, y el progreso aparece junto al cuadro de la letra.
Los botones del editor de letra también añaden cualquiera de estas secciones, además de indicaciones de voz (+ Hombre, + Mujer, + Ambas).

**Cómo suenan los versos** fija el ritmo y la rima que busca el autor. *Natural* (por defecto) mezcla líneas cortas y largas
con algunas rimas. *Rima regular* es la forma tradicional de líneas iguales que riman de dos en dos, que es lo que
producía el autor antes de que existiera esta opción. *Ritmo hablado* es conversacional, como el habla o el rap; *Rima
suelta* solo hace rimar algunas líneas; *Corto y contundente* y *Largo y fluido* fijan la longitud de las líneas.

Es un primer borrador. Las líneas tienen ritmo y riman, pero un modelo recurre a imágenes conocidas, y nada
comprueba si una línea ya es de otra persona. Léelo y hazlo tuyo antes de planificar.

---

## Escribir una canción a partir de un prompt: todas las opciones {#writing-a-song-from-a-prompt-every-option}

**+ Canción** tiene ya muchas opciones. Ninguna es obligatoria: un estilo y algo de letra bastan, como en
[Tu primera canción](#your-first-song). Este capítulo las recorre todas en el orden en que las muestra el editor,
sus tres columnas (la canción, la letra y el sonido), y después qué hacer tras el plan. Termina con una
tabla de los deseos habituales, como una canción más larga o un estribillo que suene distinto de la estrofa.

### La canción {#the-song}

- **Título.** Opcional. Si se deja en blanco, se usa la primera línea de la letra.
- **Estilo.** La lista **Elegir un estilo…** tiene 200 puntos de partida, del afrobeats al zydeco, por orden alfabético.
  Elegir uno llena el cuadro Estilo con una descripción completa, que luego puedes editar. Los chips de debajo son diez arranques
  rápidos para una canción: warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B y dance pop. Consulta [Qué poner en el cuadro Estilo](#what-to-put-in-the-style-box).
- **Guardar un estilo propio.** **Guardar**, junto a la lista, guarda lo que hay en el cuadro Estilo con un nombre que le
  des. La primera entrada de la lista, **Estilos guardados**, abre los que guardaste; la papelera junto a uno lo borra, y la
  búsqueda de la lista los encuentra junto con los 200. Guardar con un nombre ya usado sustituye ese estilo. La palabra disparadora de una
  LoRA de estilo no se guarda, y se vuelve a poner para la LoRA que esté elegida cuando uses el estilo.
- **Un tempo en el estilo es solo una pista.** El planificador suele elegir el suyo. Para fijar el tempo, usa **Fijar tempo** en
  Avanzado.
- **Voz.** Los chips escriben una voz (femenina, masculina, dúo y un carácter) en el estilo por ti.
- **LoRA de estilo.** Bajo la columna del sonido. Consulta [LoRA de estilo](#style-loras).

### La letra {#the-words}

**La estructura.** Encima del cuadro de la letra, mientras no tenga palabras, hay una lista de secciones: el orden que
seguirá la canción. Cada fila se puede cambiar a otra sección, subir o bajar (o arrastrar), o quitar, y los
chips bajo la lista añaden una sección. Las secciones son intro, estrofa, preestribillo, estribillo, puente, interludio y outro.
Un **interludio** es un pasaje instrumental: no tiene palabras, y el planificador lo toca con la voz instrumental.
(`solo` no es una sección que el planificador conozca; el interludio es la forma de pedir uno.)

**Empezar con…** llena la lista con una forma habitual. Pasa el ratón por una opción para ver a qué se adapta:

| Forma | Secciones | Se adapta a |
|---|---|---|
| Estrofa, estribillo, puente | estrofa, estribillo, estrofa, estribillo, puente, estribillo | la canción clásica: pop, rock, country |
| Corta | estrofa, estribillo, estrofa, estribillo | folk, punk, primer rock and roll |
| Intro y outro | intro, estrofa, estribillo, estrofa, estribillo, outro | baladas, soft rock, cantautores |
| Historia | estrofa, estrofa, estribillo, estrofa, estribillo, outro | canciones narrativas, folk, country |
| Pop con preestribillo | estrofa, preestribillo, estribillo, estrofa, preestribillo, estribillo, puente, estribillo | pop moderno, dance-pop, pop rock |
| Gancho primero | estribillo, estrofa, estribillo, estrofa, estribillo, puente, estribillo | pop de la era del streaming, indie pop |
| Corta y sencilla | estrofa, estribillo, estrofa, estribillo, estribillo | punk, garage rock, rockabilly |
| Hip-hop | intro, estrofa, estribillo, estrofa, estribillo, estrofa, outro | rap, hip-hop, trap, R&B |
| Doble puente | estrofa, estribillo, estrofa, estribillo, puente, puente, estribillo, estribillo | power ballads, rock progresivo y sinfónico |
| Interludio | estrofa, estribillo, interludio, estrofa, estribillo, puente, estribillo | rock, pop rock, indie |
| Todas las partes | intro, estrofa, preestribillo, estribillo, interludio, estrofa, preestribillo, estribillo, outro | pop, dance-pop |

**Cuántas secciones.** El planificador suele escribir de 8 a 10 secciones pida lo que pida la letra, así que una lista de más
de 10 se condensa y las palabras de las secciones que descarta no se cantan. El constructor lo avisa cuando la lista es
así de larga. Una canción no se alarga añadiendo secciones; cada una simplemente se acorta. Consulta
[Alargar la canción](#making-the-song-longer).

**Poner secciones en el cuadro de la letra** inserta las secciones como etiquetas vacías, listas para escribir debajo a mano. En cuanto el cuadro tiene
palabras, se canta la letra, y el constructor se aparta.

**Escribir letra.** Describe de qué trata la canción y un modelo escribe palabras para las secciones que construiste. Pide
tres cosas:

- **Versos por estrofa o estribillo** (4, 6 u 8; 6 por defecto). Más líneas en una sección dan una canción más larga,
  porque el planificador escribe más o menos tanta música como palabras hay. Una intro, un puente o un outro se quedan en 2 a 4 líneas,
  y un interludio no tiene ninguna.
- **Cómo suenan los versos.** La lista muestra las sílabas que busca cada línea. El antiguo autor producía casi siempre las mismas
  líneas rimadas de ocho sílabas, y esto lo cambia:

| Opción | Busca | Lo que obtienes |
|---|---|---|
| Natural (por defecto) | 3-13 sílabas | Una mezcla de líneas cortas y largas, algunas rimas, sin pulso fijo |
| Rima regular | 6-10 sílabas | Líneas iguales que riman de dos en dos: la forma tradicional, y lo que hacía antes el autor |
| Ritmo hablado | 5-14 sílabas | Conversacional y rítmico, como el habla o el rap, con rimas internas |
| Rima suelta | 4-13 sílabas | Algunas rimas, algunas asonantes, algunas ninguna, y líneas de distinta longitud |
| Corto y contundente | 3-6 sílabas | Líneas cortas y frases repetidas |
| Largo y fluido | 10-14 sílabas | Líneas largas que fluyen como un pensamiento |

  Se recuerda la última opción. Son objetivos, no garantías: un modelo de lenguaje los sigue de cerca en los
  extremos (corto y contundente, largo y fluido) y con más holgura en los matices.
- **El encargo** en sí, con tus propias palabras, y el estilo de arriba, que marca el ambiente. El encargo se guarda con la toma,
  así que abrir una toma y pulsar **Escribir letra** muestra de qué se pidió que tratara, listo para cambiarlo y volver a escribir.

El borrador llega al cuadro de la letra, y la ventana se cierra en cuanto empieza. Es un primer borrador: léelo y hazlo
tuyo.

**Seguir esta estructura exactamente** (la casilla bajo el cuadro de la letra, desactivada por defecto). El planificador toma las etiquetas
de sección de la letra como orientación, y a su aire escribe su propia forma: a menudo añade una intro y un outro,
cambia un puente por un interludio y una estrofa, o condensa una lista larga. Con esto activado, el plan escribe exactamente las
secciones que nombra la letra, en ese orden, y ninguna más. No puede añadir una intro o un outro que no
hayas puesto. El planificador sigue decidiendo cómo es la música y cuándo empieza cada sección. Solo se aplica a canciones.

**Quién canta cada línea: indicaciones de voz.** Una línea sola entre corchetes que nombra una voz dice quién canta las
líneas siguientes, hasta la próxima indicación o la próxima sección:

```
[Verse 1]
[male voice]
The ferry leaves at half past nine
I watch the harbour lights go by
[female voice]
I wait beside the ticket line

[Chorus]
[both voices]
Carry me over, carry me home
```

Escribe una indicación como `[male voice]`, `[female voice]` o `[both voices]`, cada una en su propia línea entre corchetes.
El editor de letra ampliado tiene los botones **+ Hombre**, **+ Mujer** y **+ Ambas** en su cabecera para insertarlas en el cursor.
Estas son las formas con las que se probó la función, además de `vocal` por `voice` (`[female vocal]`) y
`[male and female voices]` para ambas. Puedes añadir palabras propias tras una coma, como en
`[female voice, soft and close]`; no cambian quién canta. Una sección sin indicación queda en manos del planificador.

También se leen otras grafías, para que no se ignoren letras escritas en otra parte: `[man]`, `[woman]`, `[duet]`, una indicación
dentro de la etiqueta de una sección como `[Verse 2 - female vocal]`, y una indicación entre paréntesis, `(female voice)`. Los corchetes
son la costumbre más segura: las palabras entre paréntesis suelen ser coros, y pueden cantarse.

Una indicación sola no decide la voz. Quién canta depende sobre todo de lo aguda que esté escrita la melodía: la misma
línea una octava más arriba la canta una mujer, y al planificador le gusta escribir una estrofa en dos octavas, cambiando cada cuatro
líneas más o menos, se haya indicado lo que se haya indicado. **Las voces siguen las indicaciones** (una casilla bajo el cuadro de la letra, que aparece cuando la letra tiene
una indicación; activada para una toma nueva) respeta las indicaciones: cuando se escribe el plan, cada tramo indicado de la melodía se mueve por
octavas enteras a donde canta esa voz, grave para un hombre y aguda para una mujer. Nada más cambia en el plan. Se
vuelve a hacer antes de cada render, así que sigue un cambio en la letra o en la partitura. En la página Partitura,
**Voces según indicaciones** hace lo mismo una vez sobre la partitura del cuadro, para una toma hecha sin la casilla; guarda la partitura
y renderízala.

Tres cosas que conviene saber:

- **Quién canta una línea sigue siendo en parte azar.** Con la melodía en su sitio, la mayoría de las líneas van a la voz
  indicada, pero un render puede aun así dar una a la otra voz. Vuelve a renderizar con otra semilla, o usa
  **Probar más**.
- **Ambas** pone la línea donde canta una mujer y deja la segunda voz al render, que a menudo mete una
  en un estribillo. Pide un dúo más que crearlo: cuánto oyes de la segunda voz varía de un
  render a otro. Aún no hay forma de escribir dos cantantes en una línea sin que la letra sufra.
- Una toma hecha antes de que existiera esta casilla conserva su partitura tal cual; márcala, o usa **Voces según indicaciones**, para ajustarla.

**Escribir a mano.** El botón Expandir abre un editor a tamaño completo con botones para intro, estrofa, preestribillo,
estribillo, puente, interludio, outro e instrumental. Una sección es una línea como `[Verse]` seguida de sus líneas; una
etiqueta sin líneas debajo, como `[Interlude]`, es un pasaje instrumental.

### El sonido {#the-sound}

- **Armonía** (el deslizador): lo atrevidos que son los acordes. Una canción nueva empieza en **Variada**, con la interpretación
  en **Amplia**: en nuestras propias pruebas esa pareja dio las versiones musicalmente más interesantes, así que es un buen punto de partida. Mueve
  cualquiera de los dos a tu gusto. Las tomas existentes conservan aquello con lo que se hicieron. A su aire, el planificador tiende a escribir un bucle de
  cuatro acordes y usarlo en cada sección, y cada nivel lo aleja un poco más de eso. Los niveles se suman unos
  a otros:

  | Nivel | Qué hace con los acordes | Elígelo cuando |
  |---|---|---|
  | Familiar | Nada: los acordes de YuE2, a menudo un solo bucle para toda la canción | Te gusta la primera idea del planificador, o quieres el acompañamiento más sencillo |
  | Variada | Desalienta repetir exactamente los acordes que acaba de usar, así que los recolorea (un F, luego un Fmaj7) pero se queda en la tonalidad | El bucle suena demasiado igual y quieres que la canción siga siendo convencional |
  | Colorida | Lo mismo, con más fuerza: estrofa y estribillo se separan, con acordes más ricos. Una sección tampoco puede empezar con los mismos acordes que la anterior, así que un estribillo ya no empieza como su estrofa | Quieres que el estribillo sea un impulso, no una repetición. Un buen primer paso |
  | Aventurera | Desalienta las *fundamentales* usadas hace poco, no solo las grafías, así que la armonía tiene que viajar, y toma acordes prestados de fuera de la tonalidad | Quieres movimiento y sorpresa, y estarás atento a un acorde que suene raro |
  | Fuera de tono | Atrevida, con una atracción hacia acordes fuera de la tonalidad | Experimentos. Cuenta con descartar algunos planes |

  A partir de Colorida, las elecciones de acordes salen más distintas de una sección a otra: más acordes diferentes en una
  canción, más patrones de cuatro compases que no se repiten, y menos estribillos que copian el comienzo de la estrofa. El plan sigue
  siendo una canción normal, así que vale la pena probar uno o dos niveles más antes de recurrir a una Variedad del plan más salvaje.
  En **Avanzado**, **Las secciones empiezan distinto** se puede poner en *Siempre* o *Nunca* para probar un plan con y sin
  la regla del estribillo; el valor por defecto, *Seguir la armonía*, está activo a partir de Colorida. Un estilo como el trap o el ambient suele
  basarse en bucles por naturaleza, así que espera un cambio menor que en pop o rock. Consulta [Armonía](#harmony) para las mediciones.
- **Variedad del plan.** Con cuánta libertad escribe el planificador todo lo demás. Consulta [Variedad del plan](#plan-variety).
- **Interpretación.** Cómo se interpretan las notas al renderizar. Consulta [Interpretación](#interpretation).
- **Límite de duración.** Lo más tarde que puede terminar la canción. Consulta [Duración](#length).
- **Modo.** *Completo* conserva los acordes del plan; *melodía* deja libre el acompañamiento. *Sin partitura*, para canciones, no escribe
  ningún plan: consulta [Una canción sin partitura](#a-song-with-no-score).
- **Semilla**, y **conservar esta semilla**. Consulta [La semilla, y reproducir una toma](#seed-and-reproducing-a-take).
- **Pulido de producción** y **Normalizar el volumen.** Consulta [Pulido de producción](#production-polish).
- **Renderizar en cuanto el plan esté listo**, junto al botón al pie de la ventana, hace el plan y el render
  sin parar entre medias. Está marcado al principio, y el editor recuerda tu elección. Desmárcalo para leer el
  plan primero.
- **Avanzado** (el botón de la cabecera): pasos de difusión, Seguir el estilo, Evitar, Fijar tonalidad, Fijar tempo, la partitura más larga,
  límite de permanencia en un acorde, bonificación de armonía externa, Secciones que empiezan distinto, sonoridad objetivo y el fundido final. Consulta
  [Ajustes avanzados](#advanced-settings).
- **Masterización** (el botón a su izquierda, cuando la toma tiene sonido) abre el rack de masterización sobre el editor para
  la toma que contiene. El rack es, por orden, un ecualizador estilo 1073, un ecualizador paramétrico, un compresor, un ampliador estéreo y
  un limitador. En la gráfica del ecualizador paramétrico, cada una de las siete bandas es un punto: arrástralo a los lados para su frecuencia
  y arriba o abajo para su ganancia, gira la rueda sobre él para su anchura, haz doble clic para restablecerlo. La franja bajo
  la gráfica fija el tipo de la banda elegida (corte de graves, estante de graves, campana, rechazo de banda, estante de agudos, corte de agudos) y la activa
  o desactiva, **Plano** devuelve cada banda a 0 dB, y el botón en la esquina de la gráfica cambia cuántos decibelios muestra la
  gráfica. El botón está en verde mientras el rack cambia cómo suena la toma. Con el rack abierto, la barra espaciadora reproduce
  y pausa la toma y las flechas se mueven por ella y ajustan el volumen, como en la página principal. Escape cierra
  el rack, y otra vez cierra el editor.

### Alargar la canción {#making-the-song-longer}

La duración de una canción la fija su plan, y el render sigue la duración del plan. Esto es lo que la mueve:

| Para conseguir… | Haz esto |
|---|---|
| Una canción más larga | Da más líneas a cada sección (**Versos por estrofa o estribillo**: 6 u 8) |
| Una canción más lenta y más larga | Pon un **Fijar tempo** en Avanzado. El mismo plan a menos BPM dura más |
| Una canción más larga añadiendo secciones | No funciona: un plan tiene unas 8 a 10 secciones, así que más solo se acortan o se condensan |
| Más de lo que permite el plan | Escribe un plan nuevo; las duraciones varían mucho entre ejecuciones con la misma letra |
| Una canción que termine al final de su letra | Sube el límite de duración solo si se corta; el límite es un tope, no un objetivo |

### Después del plan {#after-the-plan}

- **Renderizar esta partitura** crea una toma nueva siempre que la toma abierta ya tiene audio, así que un render nunca sobrescribe una
  que quieras comparar. Una toma que aún no tiene audio se completa.
- **Conservar esta melodía** (tras cambiar la letra de una toma): canta la partitura de la toma con la nueva letra, como toma nueva. La
  melodía no puede ganar secciones ni notas, así que si tu letra tiene más secciones que la melodía, o muchas más o muchas menos
  sílabas que notas tiene (líneas largas en una melodía hecha para cortas, o cortas en una hecha para largas), la
  casilla se desmarca sola y se escribe un plan nuevo, con una línea que dice por qué. Consulta [Misma melodía, nueva letra](#same-tune-new-words).
- **Filtrar la biblioteca.** Los interruptores **Canción**, **Versión** e **Instrumental** junto a los filtros muestran solo esos
  tipos en el espacio abierto; elige más de uno, o ninguno para todos los tipos.

---

## Leer y corregir el plan {#reading-and-fixing-the-plan}

El plan está escrito en **notación ABC**: música como texto plano, letras en lugar de puntos en un pentagrama.
Chris Walshaw la ideó a principios de los noventa para enviar melodías folk por correo electrónico, y se quedó.

No necesitas leerla. La aplicación muestra el mismo plan como **cifrado de acordes** y como **notación
en pentagrama** real bajo el editor, y **Ampliar** lo abre todo a tamaño completo. Pero el texto es lo que YuE2
escribió y a partir de lo que renderiza, así que vale la pena saber moverse por él.

### Leer un plan {#reading-a-plan}

Un plan empieza con una cabecera, una letra y dos puntos por línea:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Línea | Significa |
|---|---|
| `X:1` | el número de la melodía. Todo archivo ABC empieza con uno |
| `M:4/4` | el compás — cuatro tiempos por compás |
| `L:1/32` | la duración unitaria: una letra sola dura una fusa |
| `Q:1/4=120` | el tempo — una negra a 120 pulsaciones por minuto |
| `V:` | declara una voz. YuE2 escribe dos, una línea vocal y una instrumental |
| `K:D#m` | la tonalidad, re sostenido menor. `K:` siempre va al final de la cabecera |

Después, la música en sí:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Las notas son letras.** `d16` es un re que dura 16 unidades. Las minúsculas suenan una octava por encima de las mayúsculas,
  y `'` o `,` las desplazan más.
- **`-` liga** una nota con la siguiente, para que suenen como una.
- **`z` es un silencio**, con una duración como una nota. Una `Z` mayúscula es un silencio de compás entero.
- **Los acordes van entre comillas dobles**, como `"D#m"`, y se colocan delante de la nota en la que empiezan. Esto
  es lo que edita **buscar y reemplazar**.
- **`|` es una barra de compás**, y **`%` abre un comentario** — así se marcan las secciones:
  `% intro`, `% verse`, `% chorus`.

Así que ese fragmento dice: re sostenido menor, cuatro por cuatro, 120 pulsaciones por minuto, y durante la intro la
voz calla mientras lleva el acorde, mientras el instrumento toca un re y un la ligados, y luego sol y la.

Dos consecuencias prácticas. **Editar los acordes es seguro** aunque las notas parezcan opacas — son solo
las partes entre comillas, y todo lo demás se puede dejar como está. Y **si editas el plan, el render
usa lo que editaste**, así que arreglar uno suele ser más rápido que volver a tirar hasta que salga uno bueno.

### Escucharlo {#hearing-it}

La pestaña **Notación** tiene un reproductor encima de los pentagramas. Pulsa **Reproducir** para oír el plan tal como lo tiene el
cuadro, con ediciones y todo, para juzgar de oído una melodía de la que dudas antes de gastar un render en
ella. Las notas que toca se resaltan sobre la marcha, y su control de tempo cambia solo la vista previa,
no la partitura. Reproducirlo detiene lo que tuviera la barra del reproductor, porque dos cosas a la vez no le
sirven a nadie, y cerrar la ventana — o pasar a Cifrado o Letra — también lo detiene, para que nada quede
sonando sin un control a mano.

**Instrumentos** toca cada voz con un instrumento que nombra el estilo, en lugar de un piano
en todo: un estilo que dice *electric guitar, drums* se oye con una guitarra, sus acordes tocados por
otra, y un bajo debajo; una línea cantada la sustituye una voz, y la melodía de un instrumental
no. Un estilo que nombra batería recibe también una parte de batería, escrita en el compás de la propia
partitura — un backbeat para el rock, el four-on-the-floor para el dance, un ride para el jazz, algo más escueto para una
balada — y suena de principio a fin, ya que la partitura no tiene secciones en las que callar. La
línea junto al reproductor dice qué eligió, y desmarcarlo vuelve al piano que oirías
si no. Es una lectura del estilo, no del render: YuE2 decide la
interpretación real y añade partes que la partitura nunca tuvo, así que tómalo como el plan tocado con los colores
adecuados más que como lo que sonará la toma.

**Descargar MIDI** guarda la partitura para un DAW. Cada parte es una pista propia, en su propio canal,
con el instrumento que usó la vista previa asignado a ese canal: la línea vocal, la línea instrumental y,
salvo que desmarques **Acordes**, los símbolos de acordes como una parte de acordes con su bajo al lado (el único
lugar donde la armonía está escrita en notas), y la batería en el canal 10 cuando el estilo la pide. Los
instrumentos son números de programa General MIDI, así que tu DAW los toca con sus propios sonidos, y el
tempo y el compás están en el archivo. Un plan que cambia de compás a mitad se escribe en el compás con el que
empieza — solo se registra ese — mientras las notas conservan sus propias duraciones. Hacer clic en una nota de
los pentagramas pone el cursor en el ABC que la escribió.

Una partitura con una nota por encima de lo que pueden tocar estos instrumentos, o por debajo, se toca desplazada por octavas
enteras hasta que cabe, y la línea junto al reproductor dice cuánto; los pentagramas, el archivo MIDI y
la propia partitura no cambian. Los instrumentos no tienen todos el mismo registro — un bajo se queda muy por debajo
de un piano — por eso aparece la línea cuando se desplaza una partitura. Una partitura que aún no tiene notas
no tiene nada que tocar y lo dice.

El reproductor necesita sus muestras de notas, que no forman parte de la aplicación: cada instrumento ocupa unos 7 MB,
se descarga de su origen la primera vez que una vista previa lo usa y se guarda en la biblioteca, así que
después funciona sin conexión. **Reproducir** descarga lo que necesita la partitura actual y luego empieza, y
**Obtener los sonidos** descarga lo mismo sin reproducir, para quien prefiera tenerlo listo
antes.

### El piano roll {#the-piano-roll}

Haz clic en **Piano roll** en la ventana de la partitura para abrir el editor MIDI visual. En lugar de editar letras ABC en bruto, ves y das forma a la melodía directamente en una cuadrícula interactiva de altura y tiempo.

El editor muestra las dos voces de la partitura a la vez — **Vocal** (la melodía cantada principal en azul cielo) e **Ins** (el acompañamiento instrumental en ámbar cálido). Las dos voces están siempre plenamente activas, visibles, seleccionables y editables. Los botones **Dibujar** arriba a la izquierda eligen a qué voz se asignan las notas nuevas cuando haces clic para añadirlas.

#### Editar notas {#editing-notes}

- **Añadir una nota:** haz clic en una celda vacía de la cuadrícula para crear una nota en esa altura y ese momento. La nota suena enseguida para que oigas su tono.
- **Seleccionar notas:** haz clic en una nota para seleccionarla. Mantén <kbd>Shift</kbd> o <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> al hacer clic para seleccionar varias notas en las partes vocal e instrumental. Haz clic y arrastra un **recuadro de selección** sobre una zona vacía para seleccionar una frase o un pasaje en todas las voces. Pulsa <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> en macOS) o haz clic en **Seleccionar todo** para seleccionar todas las notas de la partitura. Para seleccionar todas las notas desde el cursor de reproducción hasta el final de la canción, pulsa <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> o <kbd>Alt</kbd>+<kbd>A</kbd> (o haz clic en **Desde el cursor ▶** en la barra de herramientas).
- **Mover notas:** arrastra una nota seleccionada para adelantarla o retrasarla, o en vertical para transponer su altura. Cuando hay varias notas seleccionadas — vocales, instrumentales o de ambas — se mueven todas juntas, conservando su tiempo relativo, sus melodías y su letra.
- **Duración:** arrastra el borde derecho de una nota para alargarla o acortarla. El selector **Ajuste** (1/16, 1/8 o 1/4 de nota) limita los movimientos y cambios de tamaño a divisiones musicales limpias.
- **Borrar notas:** haz doble clic en una nota para borrarla, o selecciona una o varias y pulsa <kbd>Delete</kbd> o <kbd>Backspace</kbd>.
- **Deshacer y rehacer:** cada edición, movimiento, cambio de tamaño, adición y borrado de una nota queda en el historial. Pulsa <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) para deshacer, y <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> o <kbd>Ctrl</kbd>+<kbd>Y</kbd> para rehacer.
- **Escuchar teclas:** haz clic en una tecla del teclado de piano de la izquierda para oír su altura.
- **Maximizar:** haz clic en **Maximizar** en la barra superior para extender el piano roll a todo el ancho de la ventana del navegador.

#### Línea de tiempo, secciones y acordes {#timeline-sections-and-chords}

A lo largo de la regla superior, la línea de tiempo muestra los números de compás y los límites de sección:
- **Renombrar secciones:** haz clic en una marca de sección (`intro`, `verse`, `chorus`, etc.) para editar su nombre o reasignarla.
- **Editar acordes:** justo debajo de la regla de compases, la pista de acordes muestra la progresión armónica de la canción. Haz clic en un acorde existente para renombrarlo (por ejemplo, cambiar `C` por `Am7` o `G/B`), o en un compás vacío para colocar un acorde nuevo.
- **Armonizar compases vacíos (Rellenar huecos):** haz clic en **Rellenar huecos** en la barra de herramientas para rellenar los compases vacíos del acompañamiento instrumental con notas generadas a partir de la progresión de acordes.
- **Quitar compases vacíos (Compactar huecos):** haz clic en **Compactar huecos** para quitar los compases vacíos y en silencio en ambas voces, desplazando a la izquierda las notas y acordes siguientes para eliminar huecos no deseados en el arreglo.

#### Letra y seguimiento karaoke {#lyrics-and-karaoke-tracking}

En la parte inferior del piano roll, una pista de letra propia alinea cada sílaba con la melodía vocal:
- **Ajuste por frases:** haz clic en **Emparejar letra** para repartir la letra sobre la melodía vocal. La alineación detecta las respiraciones naturales y los silencios entre frases melódicas, y asigna cada línea de letra a su frase sin derramar palabras por encima de los silencios hacia los compases siguientes. Las palabras de varias sílabas se reparten limpiamente entre notas.
- **Editar sílabas:** haz clic en una etiqueta de letra (o selecciona una nota vocal y pulsa <kbd>L</kbd>) para editar su texto. Si escribes sílabas separadas por espacios o guiones (por ejemplo `Hel- lo world`), se reparten automáticamente por las notas vocales consecutivas.
- **Resaltado al pasar el ratón:** pasar el ratón por una etiqueta de letra resalta la nota correspondiente en la cuadrícula, y pasarlo por una nota vocal resalta su etiqueta debajo.
- **Bola de karaoke:** durante la reproducción, una bola animada salta por cada nota mientras se canta, y la sílaba activa y la nota de la cuadrícula se iluminan en tiempo real.

#### Reproducción y acompañamiento armónico {#playback-and-harmony-accompaniment}

Pulsa <kbd>Space</kbd> o haz clic en **▶ Reproducir** para empezar a reproducir desde el cursor. La línea de reproducción barre la cuadrícula, actualizando el compás, el tiempo y el contador de tiempo transcurrido.

- **Clic audible (metrónomo):** la reproducción incluye por defecto un clic audible, con un golpe de woodblock acentuado en el primer tiempo de cada compás y clics más suaves en los demás. Pulsa <kbd>C</kbd> o <kbd>M</kbd> (o haz clic en **Clic** en la barra de transporte) para activar o desactivar el metrónomo en cualquier momento.
- **Acompañamiento armónico de acordes:** la reproducción sintetiza cálidos colchones de acordes polifónicos directamente a partir de la progresión de acordes de la partitura. Incluso cuando las pistas vocal o instrumental callan, el espacio armónico sigue siendo musical y cálido en lugar de caer en un silencio muerto. Pulsa <kbd>H</kbd> (o haz clic en **Acordes** en la barra de transporte) para activar o desactivar el acompañamiento de acordes.
- **Avanzar por compases:** pulsa <kbd>Flecha izquierda</kbd> y <kbd>Flecha derecha</kbd> para retroceder y avanzar compás a compás, o <kbd>Home</kbd> para volver directamente al principio.

#### Atajos de teclado {#keyboard-shortcuts}

| Tecla | Acción |
|---|---|
| <kbd>Space</kbd> | Reproducir / pausar |
| <kbd>Flecha izquierda</kbd> | Retroceder un compás |
| <kbd>Flecha derecha</kbd> | Avanzar un compás |
| <kbd>Home</kbd> | Volver al principio (compás 1) |
| <kbd>C</kbd> o <kbd>M</kbd> | Activar / desactivar el clic audible (metrónomo) |
| <kbd>H</kbd> | Activar / desactivar el acompañamiento de acordes |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Borrar las notas seleccionadas |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Deshacer la última edición |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Rehacer |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Seleccionar todas las notas de ambas voces |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Seleccionar todas las notas del cursor al final en ambas voces |
| <kbd>+</kbd> o <kbd>=</kbd> | Ampliar la escala horizontal |
| <kbd>-</kbd> o <kbd>_</kbd> | Reducir la escala horizontal |
| <kbd>0</kbd> | Desplazarse a las notas (ajustar vista) |
| <kbd>L</kbd> | Editar la letra de la nota vocal seleccionada |
| <kbd>Escape</kbd> | Quitar la selección, o cerrar la ventana de la partitura |

### Armonía {#harmony}

A su aire, YuE2 tiende a escribir un bucle de cuatro acordes y quedarse ahí. El deslizador **Armonía** lo aleja
de los acordes que acaba de usar, sin romper la estructura de la canción.

| Nivel | Lo que obtienes |
|---|---|
| Familiar | Los acordes de YuE2. A menudo un solo bucle para toda la canción |
| Variada | Evita repetir los mismos acordes. Se queda en la tonalidad |
| Colorida | Estrofa y estribillo reciben progresiones distintas, con acordes más ricos. Una sección no puede empezar como la anterior |
| Aventurera | Mantiene la armonía en movimiento y toma acordes prestados de fuera de la tonalidad |
| Fuera de tono | Atrevida, y se aleja más de la tonalidad |

**Escribir un plan nuevo** usa la posición actual del deslizador, así que puedes volver a tirar con la misma letra y acordes más
atrevidos y comparar.

Esto se midió en lugar de suponerse — una sola letra, dos estilos, tres semillas cada uno:

| | Familiar | Variada | Colorida | Aventurera | Fuera de tono |
|---|---|---|---|---|---|
| Acordes distintos en una canción | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Compases con un acorde de fuera de la tonalidad | 0% | 0% | 0% | 13% | 24% |
| Patrones de cuatro compases que no se repiten | 29% | 38% | 50% | 63% | 64% |

Cada plan, en cada nivel, mantuvo sus secciones y acordes válidos. Pedir una armonía atrevida en el
texto del estilo en su lugar — «jazz harmony», «borrowed chords» — no tuvo ningún efecto medible.

### Variedad del plan {#plan-variety}

En *Avanzado*, **Variedad del plan** fija con cuánta libertad escribe el planificador. Donde la Armonía actúa sobre los
acordes, esto actúa sobre todo: melodía, estructura y duración.

- **Tranquila:** la más estable. Pocos acordes, y una melodía que no se aleja.
- **Normal:** la de por defecto.
- **Animada:** algunos acordes y giros más.
- **Audaz:** una armonía más rica, unas tres veces el vocabulario de acordes normal, mientras la melodía sigue siendo
  reconociblemente del mismo tipo.
- **Peculiar:** inquieta. Los acordes no paran de cambiar, y la melodía salta entre registros de una
  sección a la siguiente. Para canciones raras y estrafalarias.
- **Salvaje:** la más inquieta de todas, y puede cambiar de tonalidad a mitad.

### Una canción sin partitura {#a-song-with-no-score}

**Sin partitura**, la tercera opción de **Modo**, canta la letra sin ningún plan: YuE2 escribe la melodía y
los acordes mientras canta, como hacía el YuE original, y la canción se renderiza enseguida con **Cantar sin partitura**.
A menudo suena bastante distinta de una canción planificada.

Lo que orienta un plan no tiene aquí sobre qué actuar, así que **Armonía**, **Variedad del plan**, **Conservar esta melodía** y **Seguir esta estructura exactamente**
se atenúan mientras está elegida, y no hay partitura que leer ni editar. YuE2 decide
la duración, hasta el límite. Fijar tonalidad y Fijar tempo solo le llegan como palabras en el estilo. Cantar de nuevo,
Variaciones, Probar más y la nueva letra funcionan todos, cada uno cantado otra vez sin partitura. **Escribir un plan nuevo** da a la toma una
partitura, y Modo vuelve a *completo*. Es solo para canciones a partir de un prompt: una versión es la partitura de su grabación, y un
instrumental necesita una para mantener fuera su voz. Ambos motores pueden hacerlo.

---

## Renderizar {#rendering}

### Interpretación {#interpretation}

La partitura fija las notas. La **interpretación** fija cómo se tocan.

| Interpretación | Lo que oyes |
|---|---|
| Estándar | La lectura habitual de YuE2 |
| Ajustada | más controlada y pulida |
| Suelta | más áspera y espontánea |
| Asentada | libre de repetir una figura y quedarse en un groove |
| Inquieta | mantiene las partes en movimiento, evita repetirse |
| Amplia | busca sonidos menos obvios |

### Variaciones {#variations}

El botón de destello de una tarjeta renderiza **la misma partitura y la misma semilla** en las otras
interpretaciones. Como solo cambia la interpretación, lo que oyes entre ellas es la
interpretación — no otra tirada de dados. Cada una es una toma propia, titulada
*Night drive · Loose* y guardada dentro de la toma de la que salió (consulta **Tomas dentro de una toma**,
en La biblioteca). La ventana tiene su propio límite de duración, que parte del del editor y solo se aplica
a estas tomas.

### Probar más {#try-more}

El botón del dado de una tarjeta renderiza **la misma partitura y la misma letra otra vez como varias tomas nuevas**, para
escucharlas juntas. Variaciones solo cambia la interpretación y conserva la semilla; esto cambia la
tirada:

- **Semillas nuevas:** una semilla nueva para cada una, todo lo demás igual.
- **Intensidades del Planificador:** para una toma con una LoRA de estilo que tiene mitad de planificador, la misma semilla con
  otras fuerzas de Planificador (se excluye la suya). El planificador cambia la interpretación en sí, no solo
  la voz, así que funciona como otra semilla.

Las tomas nuevas se titulan *Night drive · try 1* o *Night drive · planner 0.60* y se guardan dentro de
la toma de la que salieron, cuyo panel se abre para mostrarlas a medida que terminan. Para oírlas unas contra
otras, pulsa **Seleccionar todo** mientras el panel está abierto y luego **Comparar**. La ventana tiene su
propio límite de duración, que parte del de la toma.

### La semilla, y reproducir una toma {#seed-and-reproducing-a-take}

Cada toma registra su semilla y cada ajuste que le dio forma. La tarjeta los nombra, hacer clic en una tarjeta
los muestra en el panel de la toma, y abrirla en el editor lo vuelve a cargar todo. **Otra vez** abre el
editor con exactamente eso, semilla incluida, para reproducir una toma que te gustó, y ajustar un ajuste cada vez una toma que casi
te gustó.

En los menús del editor, pasar el ratón por una interpretación muestra lo que hace.

Marca **conservar esta semilla** para mantener la misma semilla entre renders; sin marcar, cada render tira una
nueva.

Un render usa lo que muestra el editor: su estilo, la LoRA de estilo y sus fuerzas, el límite de duración, el modo,
la interpretación y la semilla, incluso al volver a renderizar la propia partitura de una toma.

### Misma melodía, nueva letra {#same-tune-new-words}

El planificador lee toda la letra antes de escribir una nota, así que la misma semilla da el mismo plan solo
con la misma letra. Cambia una línea y el siguiente plan es una melodía nueva: otra melodía, a menudo otra
tonalidad y otro tempo, y la voz cambia con ellos.

Para conservar una melodía que te gusta, abre la toma y cambia su letra. **Conservar esta melodía** aparece bajo la
letra, marcado, y el botón principal pasa a ser **Cantar con la letra nueva**. Cambia antes todo lo demás que
quieras: el estilo, la LoRA y sus fuerzas, el límite de duración, la interpretación. La partitura de la toma se
canta entonces con la nueva letra, como toma nueva junto a la original, que queda como está. Deja la semilla
marcada para mantener la voz lo más parecida posible. Desmarca **Conservar esta melodía** para escribir en su lugar un plan nuevo, y una
melodía nueva, para la letra. Una letra nueva que conserva el número de sílabas de las líneas antiguas encaja mejor
con la melodía. Cuando no lo hace, porque hay más secciones o muchas más sílabas que notas tiene la melodía (líneas largas en una melodía
hecha para cortas: las líneas salen repetidas o se pierden), o muchas menos (líneas cortas en una melodía hecha para largas:
el cantante llena las notas sobrantes con palabras suyas), **Conservar esta melodía** se desmarca solo con una línea que dice por qué, y
se escribe un plan nuevo para la letra. Vuelve a marcarlo para cantar la melodía de todos modos.

### Pulido de producción {#production-polish}

**Pulido de producción** aplica la LoRA de decodificador Realaudio de Mothersuperior. YuE2 tal cual suele sonar encajonado
en los medios; esto separa con más limpieza instrumentos y voces. Activado por defecto.

### Duración {#length}

El límite de duración es un tope firme, no un objetivo. YuE2 decide cuándo termina una canción, y suele terminar
sola; el límite detiene la que no lo hace. Empieza en 360 segundos, o en lo que diga **Límite de duración de una toma nueva**
en Configuración. Después hace sitio a la música, para que una canción larga no se corte:

- A una **canción o instrumental a partir de un prompt** se le sube el límite cuando se escribe su plan, si el plan
  es más largo: a la duración del plan con unos diez segundos de margen. Nunca se baja.
- Con una **grabación** elegida, para una versión o un instrumental, el límite sigue la partitura de la grabación,
  redondeado hacia arriba del mismo modo.

Un límite que escribes tú se queda como lo pusiste, y la página Partitura avisa entonces cuando un plan es más largo
que él. Un plan mucho más largo que su límite (más de un tercio por encima, y de más de ocho minutos) no se toma
por una canción en absoluto, y se vuelve a escribir. De vez en cuando
un render no se detiene al final de su partitura y sigue hasta el límite; esa toma se funde
en sus últimos segundos en lugar de cortarse, y su tarjeta dice que llegó al límite. Más raro aún, un
render termina antes de que empiece la última sección de su partitura. La aplicación lo vuelve a renderizar entonces con una
semilla nueva antes de darlo por terminado, y si ese también se queda corto, la tarjeta dice que se detuvo antes de la
última sección: **Renderizar** otra vez para otro intento.

---

## Hacer una versión de una grabación {#covering-a-recording}

1. Suelta un archivo de audio, de hasta 2 GB. Se guarda una vez y se calcula su hash, así que el mismo archivo nunca se
   guarda dos veces. Un archivo de vídeo (MP4, MOV, MKV, WebM y similares) también vale: solo se conserva su sonido, como FLAC.
2. Pulsa **Transcribir**. SheetSage2 escribe la melodía y los acordes en el cuadro de la partitura. Esto se
   guarda en caché por grabación, así que hacer otra versión de la misma canción se lo salta.
3. Corrige lo que haya oído mal.
4. Añade una letra, elige un estilo, pulsa **Crear versión**.

Una versión sigue la melodía y los acordes del original mientras el estilo decide todo lo demás, que es
lo que la convierte en una versión y no en una copia.

### Grabar una melodía propia {#recording-a-tune-of-your-own}

> [!NOTE]
> Lo bien que se detecta una melodía depende de la grabación, y un plan construido a su alrededor puede aun así fallar o
> divagar: escribe un plan nuevo, o vuelve a grabar la melodía.

En el modo **Versión**, **Grabar melodía** abre la grabadora. Elige qué estás grabando en **Entrada**:

- **Voz:** canta o tararea a un micrófono. **Autotune** puede ajustar la toma a una tonalidad y una escala; el
  botón de una toma alterna entre la versión afinada y la original para que oigas lo que hizo.
- **Instrumento:** toca la melodía con un instrumento, por ejemplo una guitarra conectada a una interfaz de audio.
  Tócala **nota a nota**: la línea que tocas se convierte en la melodía que se canta, y los acordes
  rasgueados no dan melodía que cantar. Elige la interfaz en **Dispositivo**, y en **Canal** el lado
  en el que está conectado tu instrumento (la entrada 1 de una interfaz suele ser **Izquierda**). Sube **Ganancia de entrada**
  para un instrumento flojo, manteniendo el medidor fuera de CLIP. No se ofrece autotune: un instrumento ya
  está afinado. Yeufonic recuerda estas opciones en este navegador.

El metrónomo, la cuenta atrás y la escucha por auriculares funcionan igual para ambos. **Usar como versión** guarda la
toma como grabación, marcada **MIC** o **INST** en la lista. Transcríbela como cualquier grabación; una
melodía grabada se transcribe solo como melodía, porque unos acordes adivinados a partir de una melodía suelta se mantendrían en
cada estribillo de una canción hecha con ella (una grabación transcrita antes de esto conserva sus acordes hasta que se
vuelva a transcribir). De diez a treinta segundos de melodía son más que suficientes.
**Extraer la letra** no se ofrece para una toma de instrumento, porque no tiene palabras que oír: usa
**Escribir letra**.

**¿Te oyes con retraso?** El navegador añade un pequeño retardo entre lo que cantas o tocas y lo que
oyes en los auriculares. Si tu interfaz de audio tiene escucha directa (sin latencia), úsala
y apaga el **Monitor** de la grabadora, para oírte directamente desde la interfaz, y una sola
vez. Usa auriculares con cable: el Bluetooth añade su propio retardo.

#### Ampliar a canción completa {#expand-to-full-song}

Una melodía grabada suele durar solo unos compases. **Desarrollar en canción completa** hace que YuE2 planifique una canción entera
con tu melodía dentro: el plan está en la tonalidad, el compás y el tempo de tu melodía, cada estribillo (o cada estrofa,
si lo eliges) contiene tu melodía, y el resto de la canción se escribe a su alrededor. Después se renderiza
como una versión de tu grabación.

- **Cantada por:** un hombre o una mujer. Tu melodía se mueve por octavas enteras a donde canta esa voz,
  porque la octava en que está escrita la melodía decide quién la canta. Si el estilo no nombra a ningún cantante,
  se le añade la voz.
- **Acordes:** una melodía sola suele volver del transcriptor sin acordes. Yeufonic le da entonces
  acordes a partir de sus propias notas, para que el planificador tenga una armonía que seguir. Los acordes que escribas en
  la partitura de la grabación se conservan.
- **Tu melodía** es siempre la partitura de la grabación, aunque el editor esté mostrando una toma hecha a partir
  de ella.
- **Estructura de la canción:** se usa cuando el cuadro de la letra está vacío. Con palabras en el cuadro, sus secciones son
  la estructura, y necesitan un **[Chorus]** (o un **[Verse]**) donde poner tu melodía.
- **Letra:** un tarareo se puede planificar sin letra. Una melodía tocada con un instrumento necesita letra para
  cantarse, así que escríbela primero: **Escribir letra** la redacta por ti.

### Archivos MIDI y versiones {#midi-files-and-covers}

> [!NOTE]
> Los archivos MIDI están pensados para generar tomas distintas, a menudo estrafalarias, de melodías originales.

Además de archivos de audio grabados, puedes soltar o subir archivos MIDI estándar (`.mid`, `.midi`) directamente en el modo **Versión**.

Cuando se sube un archivo MIDI:
- **Transcripción automática de la partitura:** Yeufonic analiza pistas y canales para identificar la melodía vocal principal, el acompañamiento y la progresión de acordes, los transcribe a notación ABC y los carga directamente en el piano roll. Los leads de sintetizador o las melodías vocales secuenciadas en registros más graves se transponen automáticamente a una octava natural para cantar.
- **Letra incrustada:** los eventos de letra o texto incrustados en la secuencia MIDI se extraen y se alinean con las sílabas de la melodía.
- **Dónde caen los compases:** un archivo MIDI no tiene barras de compás propias, y algunos empiezan con la primera palabra en el tiempo *anterior* al tiempo fuerte. Yeufonic lee la batería y el bajo para encontrar la barra de compás real y, cuando el archivo empieza con esa anacrusa, pone las primeras palabras en un compás corto propio para que los acordes y las marcas de compás caigan donde caen los de la canción. Un archivo sin un patrón claro de batería y bajo se deja como está.
- **Letra pegada:** las palabras que pegas se ajustan a toda la melodía de una vez, una sílaba por nota, y las notas sobrantes se mantienen en la sílaba anterior. Las líneas terminan donde la melodía hace silencio y empiezan donde empieza una frase, así que una sección más larga o más corta que los títulos de la letra ya no desplaza el resto. Si las palabras son más largas de lo que puede llevar la melodía, se dejan fuera las últimas líneas.
- **Escucha completa con SoundFonts:** el reproductor sintetiza el arreglo MIDI en audio de alta fidelidad con **FluidSynth** y SoundFonts General MIDI (`.sf2`). La salida se normaliza a pico para que grabaciones MIDI multipista flojas se escuchen con presencia y claridad sin distorsión.
- **Elegir SoundFonts:** en **Configuración** puedes elegir tu banco SoundFont `.sf2` activo preferido (como *Arachno SoundFont 1.0* o *JNS-GM 2.0*). Los archivos `.sf2` adicionales que pongas en `data/models/soundfonts/sf2/` se detectan automáticamente.
- **Retoques en el piano roll:** abre el **Piano roll** para revisar o modificar notas, elegir qué pista hace de melodía vocal principal, armonizar huecos del acompañamiento con **Rellenar huecos**, o alinear una letra recién pegada con **Emparejar letra**.

### Hacer una versión de una canción de un corpus {#covering-a-song-from-a-corpus}

El análisis de un corpus ya ha hecho lo que necesita una versión: la partitura, las palabras oídas en la canción y
su voz separada. Así que, debajo de tus grabaciones, la lista ofrece **De tus corpus**, plegada por
corpus, con la tonalidad y el tempo de cada canción, y un filtro para uno grande. Elige una canción y se convierte al instante en una
de tus grabaciones, con su partitura y su letra, y no se vuelve a ejecutar nada. Las palabras se colocan
bajo las secciones de la partitura, como las coloca **Extraer la letra**, salvo que las hayas revisado en el corpus,
en cuyo caso llegan como las dejaste. Van al cuadro de la letra, sustituyendo palabras que venían de
otra grabación; las palabras que escribiste o editaste allí solo se sustituyen si lo dices. El cuadro Estilo toma el
estilo con el que la canción se aprendió en el corpus, el mismo que su chip bajo una LoRA entrenada con él.

El archivo se enlaza en lugar de copiarse cuando el disco lo permite, así que no ocupa más espacio, y se queda
si se borra el corpus. Algunas canciones están marcadas *score: melody only* o *score: first 4 min*: su
transcripción completa falló durante el análisis, lo cual basta para el entrenamiento. Pulsa **Transcribir** para la
partitura completa con sus acordes.

**Con una LoRA.** Aquí es donde más sirven las canciones de un corpus: una canción y una LoRA hechas de la misma
obra, o de obras distintas.
1. En el modo **Versión**, abre la lista de grabaciones y elige la canción en **De tus corpus**. Su
   partitura fija la melodía y los acordes, y su letra está en el cuadro.
2. Elige una **LoRA de estilo**. La LoRA del propio corpus hace que su cantante versione su propia canción, lo más cerca del
   original. La LoRA de otro corpus la versiona en ese otro estilo y esa otra voz.
3. Ajusta las fuerzas como para cualquier versión: la grabación ya fija la melodía, así que mantén **Sonido**
   cerca de **0.50**, y súbelo para más voz y sonido de la LoRA.
4. El cuadro Estilo ya contiene el estilo propio de la canción, y elegir una LoRA pone su palabra disparadora
   delante. Eso mantiene el género y el ambiente de la canción; otro chip, o las etiquetas del filtro, la llevan
   a otra parte. El tempo y la tonalidad vienen de la partitura, diga lo que diga el estilo.
5. Pulsa **Crear versión**. **Variaciones** la renderiza después en las otras interpretaciones, y
   **Cantar de nuevo** da otra voz sobre la misma partitura, como con cualquier toma.

### Extraer la letra {#extracting-the-lyrics}

**Extraer la letra**, junto a *Transcribir*, escribe lo que canta la grabación: separa la
voz, la escucha y coloca las líneas bajo las secciones de la partitura. Se pide en lugar de
hacerse con cada transcripción, porque tarda un par de minutos donde transcribir una partitura
tarda segundos. La voz se separa, y se oyen sus palabras, en la GPU cuando el motor tiene Demucs y Whisper, y en la CPU
si no (Configuración, **Usar la GPU para stems y letras**), y la barra indica en cuál de las dos etapas está. Whisper en la GPU
y en la CPU no siempre escriben las mismas palabras para la misma voz, ya que ninguno es exacto: una voz difícil, como coros
sobre una voz principal, puede diferir en una quinta parte de sus palabras en un sentido u otro. La voz separada se guarda, así que extraer la misma grabación otra vez salta
directamente a la escucha, lo que ahorra la mayor parte de la espera.

Las palabras se guardan con la grabación. Pulsa **Extraer la letra** otra vez y vuelven directamente al
cuadro, y se te pregunta si extraerlas de nuevo, cosa que vale la pena tras cambiar el
método en Configuración. Elegir otra grabación toma sus palabras del mismo modo, y una grabación
sin palabras borra las de la anterior. Las palabras que escribiste o editaste se quedan salvo que aceptes sustituirlas.

Espera un buen borrador más que una transcripción. Medido contra la letra real de dos canciones, Whisper
falló en **el 1,5 % de las palabras** en una y en **el 25 %** en la otra, donde la voz principal y los coros se pisan
en el último estribillo. Escucha toda la voz: antes se saltaba lo que su detector de voz
tomaba por silencio, que en voces cantadas era la mayor parte de la canción. Lee el borrador y corrige lo que
oyó mal, sobre todo donde las voces se solapan.

**Dejar que escuche un LLM externo.** Si un [LLM externo](#external-llm) es tu proveedor, Configuración ofrece una opción en
*Letra a partir de una grabación*. Ponla en **LLM externo** y la voz separada se envía al modelo para
oír las palabras, mientras Whisper sigue calculando cuándo se canta cada línea. En las mismas dos canciones, Gemini
obtuvo **1,5 % y 23 %**, así que están cerca; prueba ambos en una canción que a Whisper se le resista. Necesita un
modelo que acepte audio, como Gemini. Cuando la respuesta del modelo parece una letra, se usan sus palabras,
incluso donde difieren bastante de las de Whisper: una voz enterrada en una mezcla es donde Whisper
más sufre, y el modelo no. Si el modelo rechaza el audio, se contiene (acortando líneas,
o remitiéndote a una web de letras, como puede hacer un modelo con una canción que reconoce) o devuelve
casi nada, obtienes la versión de Whisper en su lugar. El mensaje al terminar dice cuál
oyó las palabras. La voz sale de tu equipo para esto; Whisper la mantiene aquí.

Para una canción de corpus, **se guardan las dos versiones**. Cuando existen ambas, el panel de revisión de la canción muestra
**Palabras de** con cada versión y su número de palabras, la del modelo externo en uso por defecto. Elige
la otra y sus palabras van al cuadro. La primera vez que se elige una versión se redactan sus palabras, lo que
marca sus secciones con el modelo externo; después cada versión conserva sus propias palabras, ediciones y
casilla **revisada**, así que cambiar entre ellas es instantáneo y no hace ninguna llamada al modelo. En las líneas de Whisper, cualquier palabra
que repitió más de ocho veces seguidas, como un «la» sostenido que escribió cientos de veces, se recorta
a ocho.

---

## Instrumentales {#instrumentals}

El tercer modo escribe una pieza sin voz. En lugar de letra, toma una **estructura**:

| Estructura | Lo que recibe YuE2 | Quién decide |
|---|---|---|
| Dejar que YuE2 decida | `[instrumental]` | YuE2 elige las secciones y su duración |
| Secciones | `[intro] [verse] [chorus] …` | tú eliges las secciones, YuE2 su duración |
| Secciones con tiempo | `[intro 0:00-0:15] …` | tú eliges ambas |

Añade secciones con los chips **+**, reordénalas con las flechas, y dale una duración a cada una en modo con tiempos.
**Enviado a YuE2:** muestra exactamente lo que recibe el modelo. La estructura es una orientación: YuE2 puede renombrar una
sección, añadir un interludio, o pasarse de los tiempos que diste, así que el límite de duración es el tope firme.

### Un instrumental a partir de una grabación {#an-instrumental-from-a-recording}

**A partir de una grabación (opcional)** en la parte superior del editor toma una de tus grabaciones, como una versión. Su
transcripción es la partitura, así que no hay plan que escribir, y el render toca su melodía y sus
acordes con la LoRA instrumental.

Las secciones también vienen de la partitura: una por cada sección de la partitura, con los nombres que conoce la LoRA. Un
*interludio* se convierte en un puente. Un render empareja cada sección de la estructura con una de la partitura,
por eso el constructor les cede el paso. Para reordenar la canción, arrastra una sección a otro sitio o muévela con las flechas, añade una
**copia** de ella detrás, o quítala con la **✕**: cada cambio reescribe la partitura (la ventana Partitura
lo muestra), y **Restaurar las secciones originales** la devuelve hasta que se cargue otra partitura.
Mientras la toma suena en el editor, se ilumina la sección en la que está, y un doble clic en una sección salta a ella. Los tiempos vienen de los compases y el tempo de la partitura, que el render sigue de cerca al principio de una toma y en una que se renderiza entera. Un render que termina bastante antes que su partitura ha tocado menos música de la que contiene la partitura, así que la lista puede desfasarse respecto al audio a medida que avanza la canción; una línea bajo la lista lo indica y dice cuánto. Una versión muestra la misma lista bajo su letra, y su letra se asocia con las secciones en orden, así que
adáptala: la lista dice lo que necesita después de añadir, quitar o reordenar secciones. También muestra el total frente al
límite de duración, y ofrece subir el límite cuando una canción más larga se cortaría. Pulsa **Crear instrumental** para renderizar.

Un instrumental escrito a partir de una estructura también tiene partitura, y una vez planificado sus secciones se listan del mismo modo. El
constructor de estructura es el encargo de un plan aún no escrito, así que cede el paso a la lista. Reordena las secciones y pulsa
**Renderizar esta partitura**: las etiquetas de sección del render siguen la partitura editada. Una toma que ya tiene audio se renderiza como una
toma nueva a su lado, cambies lo que cambies, así que la original conserva la suya. **Escribir un plan nuevo** (bajo la partitura) sigue pidiendo
una melodía distinta a partir de la estructura con la que se escribió la toma.

**También funciona una canción con voz.** Su partitura tiene la melodía cantada en la parte vocal, que saldría
cantada, así que la melodía se da a un instrumento: donde no toca ningún instrumento, las notas cantadas
pasan a uno, y la parte vocal se queda solo con sus acordes. El editor lo indica bajo la grabación. Para una canción
suele ser la mejor opción: sin su voz, el transcriptor tiende a perder la
diferencia entre estrofa y estribillo, y oye toda la canción como un solo bucle de acordes. La LoRA
la arregla como instrumental, así que espera partes propias, como guitarra de más.

Elige **Sin grabación: escribir un plan de partitura** en la lista para volver a escribir un plan.

### Cuando un instrumental canta {#when-an-instrumental-sings}

De vez en cuando el modelo mete una voz en un instrumental. Es un fallo del modelo, no un ajuste
que hayas puesto mal. Antes de renderizar, si el plan pone notas en la voz vocal, un diálogo ofrece un plan
nuevo, una semilla nueva, o renderizar de todos modos. Una toma terminada no se comprueba: escúchala.

### Un instrumental a partir de la partitura de una canción {#an-instrumental-from-a-song-s-score}

**Hacer un instrumental**, bajo la partitura de una canción o de una versión en la página Partitura del editor (junto a **Renderizar esta partitura**
en una canción), hace de la
misma partitura un instrumental, en una toma nueva: la original queda como estaba. La melodía cantada pasa
a un instrumento, solo se envían al modelo las etiquetas de sección de la partitura en lugar de la letra, se
usa la LoRA instrumental, y el estilo pierde las etiquetas que describen una voz («soft male vocal»).
Es la forma de conseguir «esta melodía, sin voz». Vaciar a mano la parte Vocal de la partitura de una canción no
basta: el render de una canción sigue cantando las palabras que recibe.

---

## Voces {#voices}

Los chips **Voz** fijan el sexo y el carácter del cantante escribiendo en el estilo, para toda la canción.

Para un dúo, o un cantante para las estrofas y otro para el estribillo, pon indicaciones de voz en la letra y marca
**Las voces siguen las indicaciones**: consulta [La letra](#the-words) en «Escribir una canción a partir de un prompt». También funciona para la letra
de una versión.

## Corpus y entrenar una LoRA {#corpora-and-training-a-lora}

Un **corpus** es una carpeta de canciones, preparada como conjunto de entrenamiento para una LoRA de estilo: normalmente un
artista, un género o unos cuantos artistas parecidos.
Abre **Corpus** desde el menú. Está activado por defecto; `TRAINING_ENABLED=0` para la aplicación, o un
motor construido con `WITH_TRAINER=0`, lo quita.

Entrenar es lo más exigente que hace la aplicación: con el modelo de calidad completa (BF16) recomendado,
una tarjeta gráfica de 16 GB y 32 GB de RAM del sistema (en WSL2, `memory=32GB` en `.wslconfig`) son el mínimo práctico.
Una tarjeta de 8 GB puede servir para entrenar usando el modelo de poca memoria (INT8).

1. **Corpus nuevo.** Dale un nombre y una **palabra disparadora**, di si la voz es masculina o femenina
   (**ninguna** para canciones sin voz: ver más abajo), describe el sonido que comparten todas las canciones, y abre la carpeta que las contiene. Confirma que
   tienes derecho a entrenar con ellas, y pulsa **Examinar la carpeta**. La carpeta solo se lee.
   **Un corpus sin voz.** Elige **ninguna** en **Voz** cuando las canciones sean instrumentales, como
   la música dance y electrónica. La aplicación no separa entonces ninguna voz ni escucha palabras, así que nada
   inventa letras sobre sintetizadores. La letra de cada canción son las etiquetas de sección que hay en su partitura (o
   `[instrumental]` si no tiene ninguna), la descripción omite la parte vocal, y no hay revisión de la
   letra: el cuadro **Secciones** se puede editar, y la edición se guarda. El sonido de cada canción lo describe
   el modelo local cuando está instalado, ya que el externo solo tendría un título en el que basarse.
   Una LoRA entrenada así puede escribir notas en la parte Vocal de un plan, lo que hace que un render cante o tararee;
   el aviso «puede cantar» de un plan lo muestra. Cambiar la Voz de un corpus ya analizado cambia su
   letra en consecuencia.
2. **Elige las canciones.** Desmarca las que quieras dejar fuera. Cuando se prepara una canción, la aplicación guarda su propia copia de la grabación completa en el almacenamiento interno de corpus, así que un corpus sigue intacto aunque su carpeta de origen se vacíe o se mueva más tarde. Una grabación de más de 25 minutos se deja fuera, porque lo más probable es que sea un álbum entero o un concierto en un solo archivo. Si hay una hoja `.cue` al lado, **Dividir en pistas** la corta en sus canciones, que ocupan su lugar en el corpus. Las pistas van a la carpeta propia de la aplicación; la tuya no cambia. (Las canciones más largas que el límite de GPU del entrenador, como pistas de 15 minutos, se cortan con seguridad y se funden en un límite de sección musical al exportar.)
3. **Analizar.** Se separa la voz de cada canción, se encuentran su tonalidad, su tempo y sus secciones, y se redacta su letra, marcada por secciones. Con un LLM externo configurado, las secciones se marcan a partir de las palabras oídas: los estribillos porque sus palabras vuelven, las secciones nuevas por las pausas. Solo se envían las líneas y sus tiempos, y las palabras y su orden nunca se cambian. Sin él, o si su respuesta no contiene todas las líneas, las etiquetas salen del análisis musical. **Reesbozar**, junto a Guardar en la revisión de una canción, vuelve a marcar las secciones del mismo modo sin volver a escuchar la canción, para una canción redactada antes, y sustituye lo que hay en el cuadro. Una línea bajo los botones dice qué se está ejecutando, y el análisis en curso aparece en la tarjeta de trabajos y la cola de la pantalla principal. **Detener** lo detiene. Los pasos terminados se conservan, así que **Analizar** sigue donde lo dejó.

   **Volver a analizar.** Cuando todas las canciones están analizadas, el botón muestra **Analizado ✓**. Al hacer clic pregunta si quieres volver a analizar las sugerencias de estilo de todas las canciones con los prompts y ajustes de LLM más recientes (útil tras renombrar un corpus o cambiar de proveedor). Mayús+clic en **Analizado ✓** ofrece un nuevo análisis completo desde cero (separación, tonalidad, tempo, transcripción y estilos otra vez). Cada canción también se puede volver a estilizar con **Volver a analizar** en su revisión.
4. **Revisar** Abre una canción para revisar su letra y marcar **revisada**, y para describir su sonido
   donde difiera del resto. La descripción de estilo muestra lo que leerá el entrenador.
5. **Exportar el conjunto de entrenamiento.** Escribe el audio, la letra y la descripción de cada canción. Una línea bajo los
   botones muestra cuánto lleva. El entrenador toma solo una parte de cada canción, que la aplicación calcula
   según la memoria libre de tu tarjeta gráfica (unos 5½ minutos en una tarjeta de 16 GB; la ventana Registros
   dice lo que eligió). Una canción más larga se corta al final de su última sección dentro de ese margen, se funde,
   y conserva solo las palabras que aún se cantan. Su fila dice «first 3:12 trained». Si el entrenamiento
   se queda sin memoria, pon la variable de entorno `TRAIN_MAX_MINUTES` en un número más bajo, como
   3.5: consulta el README.
6. **Entrenar un LoRA.** Tarda mucho, y la GPU no está disponible para la aplicación hasta que
   termina. El progreso se ve bajo los botones y en la pantalla principal, donde puedes detenerlo,
   y la insignia del corpus en la parte superior de la página palpita mientras entrena. Entrenar de nuevo conserva
   la LoRA de la ejecución anterior con un nombre fechado, en **Ejecuciones anteriores**, o la borra, como
   elijas.
   Entrenar con el modelo de calidad completa (BF16) recomendado necesita al menos unos 12,5 GB de memoria de GPU
   (con un corte de 3½ minutos; un corte más largo necesita más), la mayor parte mientras prepara las canciones, así que una tarjeta de 16 GB
   es el mínimo práctico, junto con 32 GB de RAM del sistema (ComfyUI deja los pesos completos de YuE2
   y las cachés del conjunto de datos en la memoria del anfitrión; en WSL2, pon `memory=32GB` en `.wslconfig`). Una tarjeta de 8 GB puede
   entrenar usando el modelo de poca memoria (INT8). Las tarjetas que no pueden entrenar pueden usar igualmente LoRA entrenadas
   en otra parte (**Instalar un LoRA**). La ventana Entrenar avisa cuando hay menos memoria de GPU o del sistema disponible,
   así que cierra antes todo lo demás que use la GPU.

### Una ejecución que termina antes de tiempo {#a-run-that-ends-early}

Una ejecución puede terminar antes de su último paso: **Detener**, un fallo, o la GPU que se queda sin memoria. La línea
bajo los botones dice entonces cuándo y por qué, y tras qué paso. Por el camino, el entrenador guarda un
checkpoint cada 50 pasos, y conserva una copia del mejor hasta el momento según su pérdida de planificador, así que la mayor parte del
trabajo suele seguir ahí. **Terminar con lo que guardó** hace lo que hace una ejecución terminada, a partir de
esos archivos: la mejor copia, o si no el último checkpoint, se convierte en la LoRA con el
nombre del corpus, con su palabra disparadora, y los checkpoints se pliegan debajo en la lista de LoRA de estilo. Tarda
segundos y nada de tiempo de GPU. Los últimos pasos de una ejecución son los que menos cambian la LoRA, así que una terminada de este
modo suele estar cerca de una ejecución completa; **Checkpoints** renderiza una canción una vez en cada paso si quieres
comparar de oído. Para entrenar de nuevo toda la ejecución, pulsa **Entrenar un LoRA**.

### Ejecutar todo {#run-all}

**Ejecutar todo**, junto a los tres, hace Analizar, Exportar y Entrenar uno tras otro, para un corpus por el que
prefieres no esperar: uno grande tarda horas en analizarse. Primero pregunta qué hacer con una
LoRA anterior, y luego sigue con la página cerrada. Solo analiza lo que aún lo necesita, y una
canción cuyo análisis falla se deja fuera del conjunto de entrenamiento y se nombra bajo los botones. Las letras
que nadie ha revisado se usan tal como se redactaron. **Detener** lo detiene donde esté, conservando lo terminado;
detenido mientras exporta, termina primero el conjunto de entrenamiento. Espera a todo lo que ya esté usando
el motor antes de entrenar. Reiniciar la aplicación lo detiene, y **Ejecutar todo** otra vez lo continúa.

### Cuando se acaba la memoria de la GPU {#running-out-of-gpu-memory}

Un trabajo que se queda sin memoria de GPU lo dice, con qué probar: cierra otros programas que usen la GPU,
baja el límite de duración, o, para entrenar, deja fuera las canciones más largas. Si el motor falla y
se reinicia, el trabajo que estaba ejecutando se pierde, y también lo dice.

### La LoRA entrenada {#the-trained-lora}

Cuando termina el entrenamiento, la LoRA aparece en la lista **LoRA de estilo** con su palabra disparadora. Elegirla
muestra un chip por cada canción de la que aprendió, bajo el cuadro Estilo, y hacer clic en uno pone el estilo de esa canción en
el cuadro.
A partir de una docena de canciones, un cuadro de filtro y una fila de las etiquetas que se repiten en el corpus (sus géneros,
ambientes e instrumentos) las acotan; haz clic en dos etiquetas para encontrar canciones con ambas. La lista muestra su
primera docena hasta **Mostrar todo**. Consulta **Equilibrar Planificador y Sonido** más abajo para las fuerzas iniciales. Para compartirla, pulsa **Descargar LoRA** en la página del corpus, o **Descargar** bajo
el selector; consulta **Compartir una LoRA** más abajo.

Para añadir una LoRA que alguien compartió, pulsa **Importar LoRA** junto a **Corpus nuevo** y elige su zip. Para usar una
LoRA entrenada en otra parte a partir del conjunto exportado, pulsa **Instalar un LoRA** y elige el
archivo. Se añade a la lista de LoRA de estilo con la palabra disparadora de este corpus.

**Borrar un corpus** quita las copias de sus canciones que hizo la aplicación, las voces separadas, las letras y
las partituras. La carpeta que le indicaste, y cualquier LoRA hecha con él, no se tocan.

---

## Derechos de autor y consentimiento {#copyright-and-consent}

Con qué entrenas, y qué haces con el resultado, es responsabilidad tuya según la ley del lugar donde
vives. La aplicación te pide que lo declares y no lo comprueba: crear un corpus exige que confirmes
que tienes derecho a entrenar con esas grabaciones.

Conviene saber dos cosas:

- Los pesos de YuE2 están bajo **CC BY-NC 4.0** — uso no comercial, entrenes lo que entrenes a partir de ellos.
- Entrenar en privado con un corpus y publicar la LoRA o lo que produce son actos distintos. El segundo
  es el que suele necesitar permiso: de quien tenga los derechos de las grabaciones, y para
  una voz reconocible, del cantante.

Las LoRA que no entrenaste tú llevan sus propias licencias: léelas en la página de donde viene cada una
(consulta **Dónde encontrar LoRA de estilo** en LoRA de estilo).

## LoRA de estilo {#style-loras}

Una LoRA es un archivo pequeño que inclina el modelo hacia un sonido. Pon una en `models/loras/` y pulsa
**Volver a buscar** bajo el selector, o usa **Instalar**, y aparece en la lista **LoRA de estilo**.

Una LoRA de estilo puede tener dos mitades, y el selector muestra cuáles tiene un archivo:

- **Planificador** da forma a lo que se toca — el plan de partitura (forma, armonía, fraseo), y después la música
  que el render escribe a partir de esa partitura. Actúa en los dos pasos.
- **Sonido** da forma al audio — timbre y producción.

Una fuerza que el archivo no puede usar aparece atenuada, y un archivo que este motor no puede cargar en absoluto se señala
como tal en lugar de fallar en silencio dentro de un render.

### Dónde encontrar LoRA de estilo {#where-to-find-style-loras}

Lo más rápido es al instalar: marca **LoRA de estilo** en la página de componentes del instalador (o, con Docker, ejecuta
`sh scripts/fetch-models.sh --loras`). Eso descarga 39 LoRA de estilo de sus autores, 3,8 GB en total, cada una con una
descripción que da su palabra disparadora y las fuerzas sugeridas: los conjuntos de abajo, dos de atomtanstudio (dream pop
y hip-hop old school), y dieciséis deslizadores de concepto de ntc-ai, que solo dan forma a la partitura (Sonido no hace nada,
y no necesitan palabra disparadora). Están reunidas, sin cambios, en
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), cuyo README da crédito a cada autor
y enlaza la página de origen. Una LoRA que ya esté en tu carpeta con el mismo nombre se deja como está.

Hay más en Hugging Face. Estos son los conjuntos reunidos allí, cada uno en la página de su autor:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), una única LoRA con solo la mitad de Sonido

Para añadir una, descarga su archivo `.safetensors` desde la pestaña **Files** del repositorio, ponlo en `models/loras/`
y pulsa **Volver a buscar**, o pulsa **Instalar** y elige el archivo. La página del repositorio da la
palabra disparadora y las fuerzas sugeridas de cada LoRA: escríbelas en un `.txt` junto al archivo (consulta **Descripciones** más abajo) y
el selector las muestra, y pone la palabra disparadora al principio del Estilo por ti. Una LoRA de otra parte
puede estar guardada en un formato que este motor no sabe cargar: el selector la señala como tal, y no hace ningún daño.

Cada LoRA lleva la licencia de su autor, que estos conjuntos dan como CC BY-NC 4.0: uso personal y no
comercial, igual que los propios pesos de YuE2. Lee la licencia en la página de una LoRA antes de usarla, o de compartir lo que
produce.

### Equilibrar Planificador y Sonido {#balancing-planner-and-sound}

- **Corpus cohesionados:** una LoRA entrenada con un solo álbum o un sonido acústico unificado (p. ej., folk rock de los años sesenta) admite fuerzas más altas, normalmente en torno a **Planificador ~0.85 / Sonido ~0.80**.
- **Corpus diversos:** si el corpus de entrenamiento abarca varios géneros, estilos de producción o épocas (p. ej., folk acústico, rock y synth-pop), pesos altos de Sonido pueden causar choques acústicos. Hasta unos **Planificador 0.70 / Sonido 0.70** el audio se mantiene limpio conservando el fraseo melódico y el carácter vocal del artista.
- **Versiones:** tu grabación fija la melodía, así que la LoRA tiene menos que moldear y la mitad de Sonido se fuerza más. Mantén Sonido cerca de **0.50**.
- **Variedad del plan:** con una LoRA entrenada a partir de un corpus, **Tranquila** o **Normal** dan el resultado más reconocible. **Tranquila** puede entrar en bucle con una LoRA de estilo y un estilo corto, y el plan dura entonces
  minutos con largas intros repetidas, o sin nada cantado. Describe el estilo con más detalle (género, instrumentos y sensación), o usa **Normal**. Un plan así, o uno mucho más largo que una canción, se vuelve a escribir una vez
  con una semilla nueva, y la toma falla con un consejo si el segundo sale igual.
- **Encontrar una buena toma:** el carácter de la LoRA depende de la tirada tanto como de las fuerzas.
  Entre 0.3 y 0.6 aproximadamente, **Sonido** cambia poco la voz, así que no hace falta subirlo.
  **Planificador** cambia la interpretación en sí, no solo la voz, así que un valor que va bien a una canción
  puede ser el más flojo para otra. Trátalo como la semilla: prueba unos cuantos (por ejemplo 0.6, 0.8 y 1.0) y unas
  cuantas semillas con **Cantar de nuevo**, y quédate con la toma que te guste.
- **Guardar intensidades:** cuando encuentres la pareja adecuada para una LoRA, pulsa **Guardar intensidades** bajo el
  selector. Elegir esa LoRA empezará entonces en ellas, y viajan con ella cuando la compartes.

### Palabras disparadoras {#trigger-words}

La mayoría de las LoRA de estilo se entrenan con descripciones que **empiezan** por una palabra disparadora, y hacen muy poco
sin ella. La aplicación se encarga: elegir una LoRA pone su disparadora al principio del Estilo,
cambiar a otra la sustituye, elegir Ninguna la quita, y un render la vuelve a poner si se
borró. Verás aparecer la palabra en el cuadro Estilo — puedes editarla o moverla.

### Descripciones {#descriptions}

La lista está agrupada por conjuntos. Haz clic en un título para abrirlo o plegarlo; el selector recuerda cuáles
dejaste abiertos, y el grupo con tu elección actual se abre siempre con él.

Pasa el ratón por una entrada para leer qué es, con las palabras de su autor, y sus fuerzas sugeridas. Esas
descripciones vienen de un archivo de texto junto a la LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

La primera línea le da nombre, una línea `Trigger:` se convierte en la palabra disparadora, y el resto es la
descripción. Una LoRA tuya tiene una si escribes un `.txt` a su lado. `families.txt` en la misma
carpeta da a los grupos sus títulos, un `prefix = label` por línea.

### LoRA entrenadas a partir de un corpus {#loras-trained-from-a-corpus}

Una LoRA entrenada a partir de uno de tus corpus es una LoRA de estilo corriente: aparece en esta lista con las
demás, con su palabra disparadora al lado, y se aplican las mismas dos fuerzas.

### Probar los checkpoints {#trying-the-checkpoints}

Una ejecución de entrenamiento guarda un checkpoint cada 50 pasos, y los conserva bajo su LoRA en el selector:
**▸ 9 pasos** junto al nombre de la LoRA los abre (Configuración puede borrarlos en su lugar, para ahorrar
espacio). Un checkpoint cuya LoRA se ha borrado se queda en **Checkpoints de entrenamiento**. Para
quitar algunos, pulsa **Editar** en el corpus: **Checkpoints de entrenamiento** allí lista los de cada ejecución, esta
y las anteriores, con sus tamaños. Marca los que deban irse y pulsa **Eliminar**. La LoRA
terminada no aparece; tiene su propio **Eliminar LoRA**. Cada uno es la LoRA tal como estaba en
ese punto del entrenamiento. Suenan más o menos igual de bien, pero cada uno pondera a su manera
lo que aprendió, así que cada uno tiene su propio gusto sin perder el estilo y el sonido característico con los que se entrenó
la LoRA.

Para oírlos uno junto a otro, elige la LoRA, prepara el editor como para una sola toma, y pulsa
**Checkpoints** junto a **Eliminar LoRA**. Está atenuado para una LoRA sin checkpoints. Marca los
pasos que quieras, pon un límite de duración para estas tomas si quieres, y pulsa **Renderizar**. La acción
propia del editor se ejecuta una vez en cada checkpoint, todas con una misma semilla, y cada toma lleva el nombre de su paso:
*Night drive · step 250*, *Night drive · full*. Se guardan dentro de la toma abierta en el editor,
o, para una canción nueva, dentro de la última de ellas (consulta **Tomas dentro de una toma**, en La biblioteca). El editor se cierra, así que vuelves a la biblioteca
donde se están haciendo las tomas. Una canción o un instrumental escribe su plan y pasa directamente a
renderizar.

En una canción o un instrumental, la LoRA escribe la melodía además de dar forma al sonido, así que la misma
semilla no da la misma canción: cada checkpoint escribe su propia melodía y estructura. La semilla
elige entre lo que el modelo considera probable, y cada checkpoint piensa un poco distinto desde la
primera nota, así que los planes se separan en pocos compases. Lo que queda es el sonido. Para comparar solo el
sonido, carga un plan con **Partitura** y pulsa **Renderizar esta partitura** con cada checkpoint por turnos.

Los archivos nuevos aparecen cuando el motor ha vuelto a mirar `models/loras/`, cosa que hace cuando se recargan las
opciones.

### Compartir una LoRA {#sharing-a-lora}

Elige una LoRA y pulsa **Descargar** bajo el selector: obtienes un zip con la LoRA y su nota.
Para una LoRA entrenada a partir de un corpus, la nota lleva sus estilos aprendidos, así que los chips van con ella.

Para añadir una que te hayan enviado, pulsa **Instalar** y elige su zip, o un archivo `.safetensors`
suelto. Va a `models/loras` bajo el título **Instaladas**, con su nombre, su palabra disparadora y sus
chips. **Eliminar LoRA** quita la LoRA elegida, su nota y su línea de grupo; **Volver a buscar** vuelve a leer la carpeta
después de que añadas un archivo a mano.

---

## Stems {#stems}

Pulsa **Stems** en cualquier toma. Elige un modelo, marca las partes que quieras — voz, batería, bajo, otros,
y guitarra y piano en algunos modelos — y ejecuta.

La separación se hace en la **GPU** cuando el motor tiene Demucs, como un trabajo en la cola del motor: espera a un
render en curso, luego va rápido, y un render en cola detrás de ella espera a su vez. Un motor construido antes de
esto, una LoRA en entrenamiento (que ocupa la GPU), **Usar la GPU para stems y letras** en No en Configuración, o `STEMS_ON_GPU=0` la deja en la **CPU**, que es más lenta
y nunca retrasa un render. *Ajustado* ejecuta cuatro modelos seguidos para una mejor separación y tarda unas cuatro veces
más.

Para una pista de acompañamiento, elige **Voz e instrumentos**. Parte la canción en dos: la voz, y
los **instrumentos**, todo lo demás como un solo stem. Desmarca **voz** para quedarte solo con los instrumentos. Es
la misma separación que los cuatro stems, sumados de nuevo, así que tarda lo mismo y suena igual de limpia.
La versión *ajustada* es la que deja menos voz atrás.

Los stems van a `data/stems/<title>-<id>/`, se reproducen desde los chips de la tarjeta, y se descargan uno a uno o en
zip. Se quedan hasta que los borres.

---

## Detener, borrar y empezar de nuevo {#stopping-deleting-and-starting-again}

En qué está trabajando el motor se ve en la barra superior, junto al nombre: una píldora con el trabajo, su tiempo, una línea
en su base que indica cuánto lleva, y cuántos trabajos esperan detrás. No cambia nada más de la página cuando un
trabajo empieza o termina. Haz clic en ella para la tarjeta del trabajo: la etapa, **detener**, y **A continuación**, los trabajos en espera, cada uno con
**cancelar**.

Una toma en cola o en curso muestra **Cancelar** en su tarjeta, y **detener** en la tarjeta del trabajo detiene aquello en
lo que esté trabajando el motor. El título de una toma en la tarjeta del trabajo, en su lista **A continuación**, o en el reproductor al
pie de la página te lleva a la toma: a su espacio, quitando cualquier búsqueda o filtro que la oculte. Borrar una toma detiene su trabajo y quita sus stems. **Eliminar** junto a una
grabación quita el archivo y sus stems; las versiones hechas a partir de ella conservan su audio y su partitura, pero no se pueden
volver a renderizar.

**+ Canción**, **+ Versión** e **+ Instrumental** en el panel de la toma, o **Canción nueva** junto al
título del editor, empiezan de nuevo a partir de la toma mostrada. Borran el título, la letra y la partitura,
y parten de los valores por defecto: un estilo vacío (con la palabra disparadora de una LoRA elegida), el límite de duración
habitual, Armonía Variada, variedad del plan normal, interpretación Amplia, pulido de producción activado,
normalización desactivada, y una semilla nueva no fijada. Una LoRA elegida y una grabación elegida siguen elegidas.
La toma mostrada suelta el editor, para que Renderizar no pueda actuar sobre ella por error.

Las palabras que habías escrito pero no usaste no se tiran: una barra ofrece restaurarlas.

## La biblioteca {#the-library}

### Espacios {#spaces}

Las tomas viven en **espacios**: un espacio por canción, por álbum, o para bocetos. El nombre del espacio sobre las tomas
es el que se muestra, y todo lo que haces llega ahí. Haz clic en él para la lista de espacios: escribe para encontrar uno por
nombre, o elígelo con las flechas e Intro. Los cinco que usaste últimamente van primero, y luego todos los espacios, cada uno con
cuántas tomas tiene. **Espacio nuevo**, **Renombrar este espacio**, **Importar toma…** y **Eliminar este espacio** están al
pie de la lista. Borrar un espacio nunca borra tomas —
pasan a Default. Las grabaciones las comparten todos los espacios, así que una misma grabación puede versionarse en
varios.

El botón de carpeta de una tarjeta mueve esa toma a otro espacio, con las tomas que contenga.

### Tomas dentro de una toma {#takes-inside-a-take}

**Variaciones**, **Probar más** y **Checkpoints** hacen cada uno varias tomas de una canción. Se guardan
**dentro** de la toma de la que salieron, para que el espacio liste tus canciones y no cada render de cada una.
Checkpoints se pulsa en el editor: con una toma abierta allí, sus tomas van dentro de esa toma; para
una canción nueva, que aún no tiene toma, la toma del último checkpoint marcado (la LoRA terminada, cuando
está entre ellos) contiene las demás.

- **El botón Dentro** aparece entre los botoncitos de la parte superior de una tarjeta cuando su toma contiene
  tomas, terminadas o aún en proceso, y está **iluminado en naranja**. Pasa el ratón por encima para leer cuántas están
  hechas y cuántas faltan. La propia tarjeta es claramente más clara que las demás (en el
  tema claro, un tono cálido), para que una toma con tomas dentro destaque en una lista. (El botón del rack de masterización a su lado se ilumina en verde de
  la misma manera cuando la toma está masterizada.)
- **Haz clic en él** y se abre un panel bajo la tarjeta con las tomas que contiene, cada una en su propia tarjeta. Una
  toma aparece allí cuando está terminada; mientras se hace, solo se muestra la toma a la que pertenece.
  Haz clic otra vez en el botón, o en **Cerrar**, para cerrarlo.
- **Una toma dentro de otra es una toma como cualquier otra.** Reprodúcela, márcala con estrella, guárdala, sepárala en
  stems, renómbrala, y haz doble clic para abrir su canción y su partitura.
- **Un solo nivel.** Una toma dentro de otra no contiene ninguna, así que su tarjeta no tiene Variaciones ni Probar
  más, y **Checkpoints** en el editor se atenúa mientras sea la toma abierta allí. **Sacar** (la flecha que sale de una caja) la convierte en una toma propia en la lista del espacio, y entonces sí puede.
- **Las herramientas de la lista siguen al panel.** Mientras hay uno abierto, **Seleccionar todo**, **Favoritas**, los botones
  de tipo, **Comparar**, **Eliminar** y anterior y siguiente del reproductor actúan sobre las tomas del
  panel. La toma cuyo panel está abierto se queda en la página digan lo que digan los filtros.
- **Lo que suena dentro se ve fuera.** Si cierras el panel mientras suena una de sus tomas,
  el botón Reproducir de la toma que la contiene brilla en dorado, para que veas de dónde viene el
  sonido. El verde sigue indicando que es esa misma toma la que suena.
- **La búsqueda las encuentra** como a cualquier otra toma, estén donde estén. Mientras hay una búsqueda, lo que
  encuentra se muestra como tarjetas sencillas, y una toma que está dentro de otra dice en cuál.
- **Borrar una toma borra las tomas que contiene.** El aviso dice cuántas. Saca antes las que quieras
  conservar.

Las tomas hechas antes de que existiera esto se quedan donde están, una al lado de otra en la lista.

### Tarjetas {#cards}

Cada tarjeta nombra los ajustes que le dieron forma — Armonía, Interpretación, Variedad del plan, la LoRA y
sus fuerzas, la semilla, el motor que la renderizó y su antigüedad — para que una tarjeta se lea como la receta que la hizo.

**Guardar** pregunta en qué formato descargar la toma, FLAC, WAV o MP3. Empieza con lo que guardaste la última
vez, y sin nada elegido la primera vez. Una toma con imagen también se puede guardar como **Vídeo**: un MP4 de
la canción que muestra la imagen de su tarjeta (vídeo H.264, audio AAC a 192 kbps). Las aplicaciones de mensajería como
WhatsApp lo envían y reproducen como vídeo, donde un archivo de audio va como documento. Con el rack de masterización activo, el
vídeo tiene el sonido masterizado, como los demás formatos. **Toma**, a su lado, guarda además la receta de la toma: un archivo pequeño
(`<title>.yeufonic.json`) con su letra, su estilo y su partitura, sus semillas y ajustes, sus LoRA por nombre y
los ajustes del rack de masterización, pero no su audio. Con un formato elegido también, ambos van en un zip; pulsa de nuevo el
formato elegido para guardar solo la receta. El archivo no contiene nada de tu instalación (ni rutas, ni identificadores, ni claves),
así que se puede conservar, o compartir con otro usuario de Yeufonic.

**Importar toma…**, en la lista de espacios, crea a partir de un archivo así una toma nueva en el espacio mostrado; soltar el archivo
en la biblioteca hace lo mismo. La toma contiene el plan, listo para renderizar, para poder revisarlo o cambiarlo antes.
Cualquiera de los dos motores puede renderizarla: la misma partitura y la misma semilla en el mismo motor dan una toma muy parecida, en el otro
motor una distinta. Una LoRA que nombra y que no está instalada aquí se señala al importar, para que puedas
instalarla o elegir otra antes de renderizar. La grabación de una versión no está en el archivo, así que una versión compartida llega
como una canción con la partitura y la letra de la versión, dejando atrás los ajustes que pertenecían a su grabación (el
tempo fijado, la Armonía, las indicaciones de voz y el límite de duración): un plan nuevo a partir de ella empieza como una canción a partir de un prompt.

**Buscar tomas** encuentra las tomas en las que todas las palabras que escribes aparecen en algún lugar del título, el estilo, la letra o el
nombre de la LoRA, sin distinguir mayúsculas. Busca en el espacio mostrado; **Todos los espacios**, a su lado en cuanto escribes,
busca en todos los espacios, y una tarjeta de otro espacio dice de cuál. × o Escape la borra. El
cuadro empieza vacío cada vez que se abre la página, y ofrece tus últimas búsquedas que encontraron algo:
haz clic en una, o elígela con las flechas e Intro.

**Canción**, **Versión** e **Instrumental** muestran tomas de esos tipos: enciende uno o más, o ninguno para todos los tipos.
**Favoritas** muestra solo las tomas con estrella; haz clic otra vez para mostrarlas todas. Los iconos de al lado fijan cómo se disponen
las tomas, los que están en uso iluminados en verde: tarjetas **cómodas** más anchas con más del prompt o **compactas** más estrechas,
**todo el ancho** de la ventana o una columna centrada, y cada toma **plegada** a su línea de título. Pasa el ratón por
un icono para leer lo que hace un clic.

Marca tomas y la fila ofrece lo que se puede hacer con ellas, en lugar de los tipos y la disposición: cuántas están
elegidas, **Comparar**, **Eliminar** y **Hecho**, que las desmarca. **Seleccionar todo**, al final de la fila, marca
cada toma mostrada. Un título siempre se queda en una línea, terminado en … si es largo. Pasa el ratón por el título, los ajustes o el estilo de una tarjeta para leerlo entero.

### Una imagen para cada toma {#a-picture-for-each-take}

Cada toma nueva recibe una imagen de la canción, que se ve tenue detrás de su tarjeta, en la parte superior del panel de la toma cuando la eliges, y detrás del editor cuando la toma está abierta
allí. Dibujada en este PC, espera a que no se esté haciendo ninguna canción, así que nunca retrasa un plan o un render, y
aparece poco después de que la canción termine; dibujada por un LLM externo, se hace mientras la toma se renderiza.
Se hace en dos pasos: el título, el estilo y las primeras palabras de la toma se convierten en una **descripción** de
una imagen, luego un modelo de imagen la **dibuja** sobre blanco, y se quita el blanco, dejando la imagen
con un fondo transparente. Una toma hecha dentro de otra (Probar más, Variaciones, Checkpoints) muestra la
imagen de la toma en la que está en lugar de tener una propia.

Un modelo de imagen no dibuja un grupo o una persona reales, así que la descripción omite los nombres; y las
letras propias de la imagen se mantienen suaves, para que no compitan con las de la tarjeta.

#### Dos formas de dibujar: FLUX.2 klein en este PC, o un LLM externo {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

Las imágenes necesitan algo que sepa dibujar. Hay dos, y puedes tener uno, los dos o ninguno.

| | FLUX.2 klein, en este PC | El modelo de imagen de tu LLM externo |
|---|---|---|
| Qué es | un modelo de imagen pequeño que funciona en el motor, junto a YuE2 | el propio modelo de imagen del proveedor, como el de Gemini |
| Cuánto cuesta | nada; unos 8 GB de disco | cada imagen es una petición al proveedor, que puede cobrarse |
| Qué sale del PC | nada: la descripción la escribe Gemma en este PC, o se hace a partir de la propia toma | el título, el estilo y las primeras palabras de la toma, y la descripción |
| Cuándo funciona | en la GPU cuando no se está haciendo ninguna canción: después de tu canción, nunca en su camino | junto a los renders, mientras se ejecutan |
| Qué configuras | una opción de instalación | el LLM externo en Configuración, con un proveedor que ofrezca un modelo de imagen |

**Para dibujar en este PC, instala FLUX.2 klein.**

- **Windows:** marca **FLUX.2 [klein]** en la página de componentes del instalador. No está marcado
  a menos que lo elijas. Una aplicación instalada recibe la misma página al actualizarse, o vuelve a ejecutar el instalador
  desde la página de la versión: la casilla se recuerda después, y una actualización nunca lo descarga dos veces. Son
  tres archivos, unos 8 GB en total.
- **Docker:** ejecuta `sh scripts/fetch-models.sh --pictures`, que pone los tres archivos en `models/`
  (`diffusion_models`, `text_encoders` y `vae`) y comprueba cada uno, y luego reinicia la aplicación con
  `docker compose restart app` para que los encuentre.

**FLUX.2 klein 9B, si tienes la tarjeta gráfica para ello.** klein tiene un tamaño mayor, un modelo de más calidad
que dibuja más detalle y mejores manos y caras, pensado solo para tarjetas gráficas con más memoria
de vídeo. Yeufonic nunca lo descarga, porque sus archivos tienen acceso restringido en Hugging Face y están bajo la **licencia no comercial**
de Black Forest Labs, pero ponlos en su sitio y se usan.

- **Disco:** unos 18 GB para la pareja habitual, el modelo FP8 y su codificador de texto FP8 (16 GB con el codificador
  FP4), junto a los archivos del 4B. Necesita el VAE del 4B (`flux2-vae.safetensors`), así que instala primero el 4B.
- **Memoria de vídeo:** funciona en una tarjeta de 16 GB, pero ocupa casi toda mientras dibuja, con la memoria libre
  cerca de cero. Las imágenes esperan a que no se esté haciendo ninguna canción, así que no ralentiza tus canciones, pero otros
  programas que usen la tarjeta gráfica a la vez pueden tener problemas. Con menos memoria sigue funcionando, más
  despacio, mientras el motor mete y saca el modelo; ahí el 4B es la mejor opción.

1. **El modelo.** Inicia sesión en Hugging Face, acepta la licencia en
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   y descarga `flux-2-klein-9b-fp8.safetensors` (9,4 GB). O toma el de precisión completa
   `flux-2-klein-9b.safetensors` de [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   el de Mac, que ocupa más o menos el doble y necesita el doble de memoria.
   Va en la carpeta `diffusion_models`.
2. **Su codificador de texto.** Desde [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   que no requiere iniciar sesión, descarga uno de estos y ponlo en la carpeta `text_encoders`:
   `qwen_3_8b_fp8mixed.safetensors` (8,7 GB, la opción habitual en una tarjeta NVIDIA), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 GB, el más pequeño) o `qwen_3_8b.safetensors` (16,4 GB, precisión completa, para un Mac).
   **Con el motor yue2.cpp** el servidor de imágenes no puede leer esos codificadores: toma en su lugar `Qwen3-8B-Q4_K_M.gguf`
   (5,0 GB) de [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (`-Q8_0.gguf`, 8,7 GB, también funciona), y ponlo en la misma carpeta.
3. **Dónde están las carpetas:** bajo `models/` en la carpeta de Yeufonic para **Docker**; bajo
   `engine\ComfyUI\models` en la carpeta de instalación en **Windows**; bajo `engine/ComfyUI/models/` en la
   carpeta de instalación en un **Mac**.
4. **Deja que la aplicación los vea, y elígelo.** Reinicia Yeufonic (con Docker, `docker compose restart app`),
   y luego pon **Imágenes de las tomas: modelo** en Configuración en *FLUX.2 klein 9B*. El 4B dibuja hasta que lo hagas, y
   Configuración lo indica cuando el 9B está elegido pero no puede dibujar aquí. Elige
   *4B* para volver atrás sin quitar nada. La nota de la imagen en el editor dice cuál la dibujó
   (*drawn by FLUX.2 klein 9B on this PC*).

El modelo y su codificador solo se encuentran con estos nombres, así que mantén los nombres de archivo tal como se descargan.

**FLUX 3 klein, para rotular y una tarjeta de 12 GB o más.** FLUX 3 Image Klein de Black Forest Labs dibuja a partir de una
descripción completa de la escena, que es justo lo que son los prompts de imagen que escriben Gemma o el LLM externo, y
rotula bien, lo que va bien con **Imágenes de las tomas: título de la canción en la imagen**. Como el 9B, Yeufonic nunca lo descarga: sus archivos tienen
acceso restringido en Hugging Face y están bajo la **FLUX Kommunity License** (uso no comercial, y uso comercial de lo que
dibuja para quien esté por debajo del límite de ingresos de la licencia; léela antes de aceptarla). Pon sus archivos en su sitio y se
puede elegir.

- **Disco:** unos 11 GB para la pareja int8, junto a los archivos del 4B. Usa el VAE del 4B (`flux2-vae.safetensors`),
  así que instala primero el 4B.
- **Memoria de vídeo:** unos 11 GB mientras dibuja. Da varias veces más pasos que los FLUX.2 klein, así que cada
  imagen tarda más.
- **Motor:** solo el motor ComfyUI, por ahora; con el motor yue2.cpp no se ofrece.

1. **Inicia sesión en Hugging Face** y acepta la licencia en
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **El modelo,** en la carpeta `diffusion_models`: `flux3-image-klein-int8-convrot.safetensors` (5,8 GB, la opción
   habitual en una tarjeta NVIDIA), `flux3-image-klein-nvfp4.safetensors` (5,3 GB, para una tarjeta RTX 50) o
   `flux3-image-klein-bf16.safetensors` (11,1 GB, precisión completa, para un Mac).
3. **Su codificador de texto,** en la carpeta `text_encoders`: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) o
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, para un Mac).
4. **Deja que la aplicación los vea, y elígelo:** reinicia Yeufonic (con Docker, `docker compose restart app`), y luego pon
   **Imágenes de las tomas: modelo** en Configuración en *FLUX 3 klein*. La nota de la imagen en el editor dice *drawn by
   FLUX 3 klein on this PC*.

Las carpetas son las mismas que para el 9B, y los archivos solo se encuentran con estos nombres.

**FIBO 2.0, para el aspecto de una fotografía y una tarjeta de 16 GB.** FIBO 2.0 de Bria dibuja lo más parecido a una
fotografía real de las fundas de disco en las que se inspiran las imágenes: detalles más nítidos, una profundidad de
campo natural, los colores de la película y más de lo que pide la descripción. Yeufonic tampoco lo descarga nunca. **Su
licencia es CC BY-NC 4.0: solo uso no comercial.** La licencia de FLUX 3 permite a quien está por debajo de su límite de
ingresos usar comercialmente lo que dibuja; con FIBO, cualquier uso comercial, incluida la portada de una canción que
vendas, necesita un acuerdo con Bria. Lee la licencia antes de usarlo.

- **Disco:** unos 10,4 GB, el modelo y su complemento turbo. Lee el codificador de texto de FLUX 3 y el VAE del 4B, así
  que con FLUX 3 instalado no hace falta nada más.
- **Memoria de vídeo:** unos 12,5 GB mientras dibuja, así que una tarjeta de 16 GB. Una tarjeta más pequeña descarga una
  parte, lo que es mucho más lento.
- **Tiempo:** con el complemento turbo, más o menos lo mismo que FLUX 3. Sin él, FIBO dibuja con sus propios ajustes,
  unas ocho veces más.
- **La funda:** dibujada por FIBO, el borde alrededor de la fotografía no tiene la fina línea oscura, que FIBO dibujaba
  como barras gruesas y un recuadro alrededor del título.
- **Motor:** solo el motor ComfyUI.

1. **El modelo,** de [Comfy-Org/Fibo-2.0](https://huggingface.co/Comfy-Org/Fibo-2.0), sin iniciar sesión, en la carpeta
   `diffusion_models`: `fibo2_dev_int8_convrot.safetensors` (8,4 GB, la opción habitual en una tarjeta NVIDIA) o
   `fibo2_dev_bf16.safetensors` (16,5 GB, precisión completa, para un Mac).
2. **Su complemento turbo,** de la misma página, en la carpeta `loras`:
   `fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors` (2 GB). No es una LoRA de estilo y no se ofrece como tal.
3. **Su codificador de texto,** si FLUX 3 no está instalado: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) o
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, para un Mac), de la misma página, en la carpeta `text_encoders`.
4. **Deja que la app los vea, y elígelo:** reinicia Yeufonic (con Docker, `docker compose restart app`) y después pon
   **Imágenes de las tomas: modelo** en Ajustes en *FIBO 2.0*. La nota de la imagen en el editor dice *drawn by
   FIBO 2.0 on this PC*.

**Para dibujar con un LLM externo,** abre Configuración y pon **LLM para escribir letras y etiquetas de estilo** en el
[LLM externo](#external-llm), con su **URL de la API**, su **clave de API** y su **modelo**, como para las letras. El proveedor debe tener un modelo
de imagen: Gemini lo tiene (se usa `gemini-3.1-flash-image` salvo que nombres otro), y a un proveedor compatible con OpenAI
se le pide `gpt-image-1`. La aplicación pide al proveedor su lista de modelos, en segundo plano,
al arrancar, cuando cambian estos ajustes y cada pocas horas, y solo dibuja allí cuando la lista
tiene el modelo de imagen.

Sin ninguno de los dos, **Imágenes de las tomas** en Configuración dice **Sin imágenes: el fondo por defecto**, con una línea sobre cómo
tenerlas, y la opción de hacerlas no se puede elegir.
Configura cualquiera de los dos y se activan: a partir de entonces se hacen imágenes para las tomas que crees.

#### Gestionar las imágenes en Configuración {#managing-pictures-in-settings}

| Ajuste | Hace |
|---|---|
| **Imágenes de las tomas** | *Hacer una para cada toma nueva* (por defecto cuando algo puede dibujar), o *Solo cuando se pida*, donde una toma mantiene el fondo por defecto hasta que hagas una desde su cuadrado o el botón Imagen del editor. Los ajustes de abajo dan forma a una imagen hecha de cualquiera de las dos maneras. Es *Sin imágenes* mientras nada aquí pueda dibujar. |
| **Imágenes de las tomas: dibujadas por** | *Este PC si klein está instalado, si no el LLM externo* (por defecto), *Este PC (el modelo de abajo)* o *El modelo de imagen del LLM externo*. Qué klein dibuja en este PC (FLUX.2 klein 4B o 9B, o FLUX 3 klein) se elige en **modelo**. FIBO 2.0 también se elige ahí. |
| **Imágenes de las tomas: modelo** | *FLUX.2 klein 4B* (por defecto), *FLUX.2 klein 9B*, *FLUX 3 klein*, o *9B donde estén instalados sus archivos, si no 4B*. Solo para imágenes dibujadas en este PC. El 9B y FLUX 3 nunca se instalan por ti: consulta [FLUX.2 klein 9B y FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) más arriba. Si el pedido no está, dibuja otro, y Configuración dice cuál. *FIBO 2.0* también se añade a mano y es solo para uso no comercial: consulta más arriba. |
| **Imágenes de las tomas: descritas por** | quién escribe el prompt de imagen, a partir del título de la toma, el estilo artístico de abajo, su estilo y su letra (hasta 50 líneas). *Gemma local si está instalado, si no la propia toma* (por defecto), dibuje quien dibuje. *Gemma local*: escrito en este PC; necesita la opción Borradores de letra. *A partir de la propia toma*: sin LLM; una descripción hecha con el título, el estilo y las primeras palabras de la toma, la más rápida, y no se envía nada. O el *LLM externo*, una petición por imagen; cuando no está disponible, o pasas a LLM locales para la sesión, Gemma las escribe en su lugar si está instalado. |
| **Imágenes de las tomas: estilo artístico** | cómo debe verse la imagen, dado al LLM que escribe el prompt de imagen (atenuado cuando la toma se describe a sí misma). Por defecto un diseño abstracto y surrealista al estilo de las portadas de los años setenta y ochenta, sin texto ni personas. Vaciado, vuelve a eso. |
| **Imágenes de las tomas: tu propio prompt** | palabras con las que empieza el prompt de imagen de cada imagen, como *salt marsh, overcast*, hasta 512 caracteres; el prompt que escribe el LLM va detrás. Vacío (por defecto): ninguna. Solo cuando un LLM escribe el prompt de imagen (atenuado cuando la toma se describe a sí misma). |
| **Imágenes de las tomas: título de la canción en la imagen** | *No* (por defecto) o *Sí*: el título de la canción se rotula en negrita en la portada, en mayúsculas o minúsculas, tal como lo escribiste, incluso cuando es el nombre de un artista (la imagen en sí se sigue describiendo sin él). Casi siempre la imagen va enmarcada por una fina línea oscura dentro de un borde blanco roto, como en muchas portadas de los setenta, con el título centrado en una banda más ancha arriba o abajo. Más o menos una de cada cinco no tiene borde: el título va sobre la imagen, en una esquina o centrado arriba o abajo, en un color apagado sacado de la imagen, y se pide al LLM que deje esa parte de la imagen despejada para él. Todo esto se elige al azar para cada imagen. FLUX.2 klein puede escribirlo con alguna errata. Solo cuando un LLM escribe el prompt de imagen. |
| **Imágenes de las tomas: modelo de imagen** | cuál de los modelos del proveedor dibuja. Solo para imágenes dibujadas por el LLM externo (elígelo en **Dibujado por**; atenuado si no), y vacío para el habitual del proveedor, que es casi siempre lo que quieres. |

Así que con FLUX.2 klein instalado y los ajustes como vienen, las imágenes se hacen enteramente en este PC, incluso
cuando el LLM externo escribe tus letras: Gemma escribe cada prompt de imagen donde están instalados los Borradores de letra, y
sin él la descripción se hace a partir de la propia toma, sin LLM, lo que no lleva tiempo. Elige *El modelo de imagen del
LLM externo* para que las dibuje el proveedor, o pon **descrito por** en *A partir de la propia toma* para las
imágenes más rápidas, o en *LLM externo* (una petición por imagen).

#### La imagen de una toma en el editor {#a-take-s-picture-in-the-editor}

El icono **Imagen** en la fila superior de la ventana del editor, junto a los demás botones de la toma, muestra la imagen
con dos opciones: **Hacer una imagen nueva**, que la vuelve a hacer en segundo plano, y **Usar el fondo por defecto**, que la quita para siempre: no se vuelve a hacer imagen para esa toma salvo que pidas una.
Haz clic en la imagen para verla entera, tan grande como permita la ventana; un clic en cualquier sitio o Escape
la retira y deja el editor como estaba. La imagen entera tiene las mismas dos opciones debajo. Elige
ahí **Hacer una imagen nueva** y la imagen se queda a la vista mientras se hace la nueva, con lo que está pasando mostrado
entre los botones, y luego cambia a la nueva cuando está lista.

En la tarjeta de una toma, el cuadrado de arriba a la izquierda muestra la imagen cuando pasas el ratón por él. Una toma sin
imagen ofrece ahí **Hacer una imagen nueva** en su lugar, donde este PC puede hacer imágenes.

### Comparar tomas {#comparing-takes}

Marca de dos a seis tomas y pulsa **Comparar** (aparece junto a Seleccionar todo cuando hay dos marcadas, y
espera a las tomas que aún se renderizan). Las tomas se apilan en una ventana sobre una posición compartida: pulsa de **1** a
**6** o haz clic en una para cambiar, y sigue desde el mismo momento de la canción, sonando o
en pausa. **Espacio** reproduce y pausa, las flechas avanzan 5 segundos, y la estrella marca la que
prefieres. **Igualar el volumen** baja las tomas más fuertes hasta la más suave, ya que una toma más fuerte tiende
a sonar mejor; **Ocultar nombres** baraja las tomas y las llama Toma A, B, C para una escucha a ciegas.

### El reproductor {#the-player}

Haz clic o arrastra en la forma de onda para desplazarte. Anterior y siguiente recorren las tarjetas en el orden mostrado.

| Tecla | Hace |
|---|---|
| Espacio | reproducir o pausar |
| Izquierda, Derecha | retroceder o avanzar cinco segundos |
| Mayús+Izquierda, Mayús+Derecha | la toma anterior o siguiente; en la vista Listas, la canción anterior o siguiente de la lista |
| Arriba, Abajo | volumen |

Las teclas multimedia del sistema también funcionan. Las teclas propias de la toma están en [Atajos de teclado](#hot-keys).

### El visualizador de audio y la letra sincronizada {#the-audio-visualizer-and-synced-lyrics}

Pulsa **Visualizador** en la barra de transporte (o **V** mientras suena una pista) para abrir el escenario del visualizador a pantalla completa.

El escenario muestra visualizaciones de audio en tiempo real sincronizadas con la reproducción:

- **Modos del visualizador:** elige entre diez visualizadores en la barra superior:
  - *Yeufonic:* el propio logotipo, respirando — la baldosa brilla con los graves y se expande con el pulso, cada brazo de la horquilla es un medidor con su mitad del espectro, y el punto verde se enciende con el pulso.
  - *Cinta de onda:* dos cintas armónicas flotantes que reaccionan al sonido.
  - *Aurora boreal:* cortinas ondulantes de aurora etérea que reaccionan a medios y agudos.
  - *Nebulosa cósmica:* un campo de estrellas y una nebulosa de partículas interestelares que gira y late al ritmo.
  - *Caleidoscopio:* simetrías geométricas radiales que laten con el tempo.
  - *Rejilla neón:* un plano de alambre synthwave retrofuturista en perspectiva que ondula con las líneas de bajo.
  - *Distorsión líquida:* una superficie fluida desplazada por ondas armónicas.
  - *Enjambre de partículas:* cúmulos de partículas gravitatorios que se dispersan con los golpes de percusión.
  - *Barras de espectro hi-fi:* un analizador de espectro multibanda con picos flotantes que caen.
  - *Portada:* la imagen de la toma, en grande, con su título debajo, sobre una copia difuminada de sí misma que se mueve con la música. Una toma sin imagen muestra la escena Yeufonic hasta que se haga una.
- **Detrás de las escenas:** las escenas Portada, Yeufonic, Mandala, Rejilla, Líquido y Barras suenan sobre la imagen de la toma, que se mueve suavemente con la música, cuando la toma tiene una. Encima también puede moverse algo, en los colores de la imagen: *Respiración* (la imagen sola), *Rayos de luz* que giran desde el centro, *Ondas* lanzadas con el pulso, *Color a la deriva*, *Profundidad* (más copias de la imagen que giran unas contra otras) o un *Halo espectral*. Cada escena empieza con el suyo (color a la deriva detrás de Portada, el halo detrás de Mandala, rayos detrás de Rejilla, ondas detrás de Líquido, la imagen sola detrás de Yeufonic y Barras); pulsa **B** para recorrerlos, y la escena recuerda tu elección.
- **La forma de onda:** bajo las escenas Yeufonic y Portada, la forma de onda de la toma muestra cuánto ha sonado la canción; haz clic en ella para saltar ahí.
- **Portada y dinámica del vinilo:** muestra la portada de la toma al estilo Hipgnosis en una funda 3D interactiva que se inclina y gira con el puntero. Un disco de vinilo realista gira a 33⅓ RPM y sale de la funda con los golpes de bajo, con un brillo holográfico y anillos de onda expansiva que reaccionan al ritmo. Cambia de modo con el botón **Portada**: *Funda*, *Aura* (fondo difuminado) o *Desactivado*.
- **Una imagen nueva:** el botón de imagen arriba a la derecha, en cada escena, hace una imagen nueva para la toma que suena, donde este PC puede hacer imágenes. Late mientras se hace la imagen, y la nueva toma el relevo cuando está lista.
- **Letra en pantalla:** pulsa **L** o haz clic en **Letra** para mostrar u ocultar el panel de letra independiente y desplazable. Arrástralo por la barra de arriba para apartarlo; se queda donde lo pongas, y un doble clic en la barra lo devuelve a su sitio.
- **Cinta del minirreproductor:** mientras el visualizador completo está cerrado, un minivisualizador reactivo de doble onda suena dentro de la barra de transporte inferior. Se activa o desactiva en **Configuración → Apariencia**.

### Listas de reproducción y favoritas {#playlists-liked-songs}

Haz clic en **Listas** en la barra superior para pasar a la vista Listas.

- **Disposición en dos columnas:** la columna izquierda lista tus listas junto a la lista de sistema fijada **Me gusta**, con el número total de canciones. La columna principal muestra la cabecera de la lista activa (portada en alta resolución, título, descripción, total de canciones y duración) y la tabla de pistas.
- **Sincronización automática de favoritas:** cualquier toma marcada con estrella en la biblioteca, en cualquier espacio, aparece automáticamente en la lista de favoritas. Quitar la estrella la quita de esa lista.
- **Añadir a una lista:** pulsa **P** o haz clic en el icono **Lista** de cualquier tarjeta para abrir el selector de listas, marcar o desmarcar la pertenencia a listas, o crear una nueva. **Escape** cierra el selector.
- **Orden y búsqueda interactivos:** haz clic en un encabezado de columna (**Título**, **Duración** o **Añadida**) para ordenar con indicador de sentido e invertir el orden con un clic, y filtra las pistas con el cuadro de búsqueda.
- **Ir al espacio en la biblioteca:** haz clic en el título de una canción en la tabla de pistas para pasar al instante a la vista Biblioteca, abrir el espacio donde vive esa toma y resaltar su tarjeta.
- **Atajos en las listas:** los atajos propios de las tomas se ignoran en la vista Listas para evitar cambios involuntarios, salvo **M** (rack de masterización), que actúa sobre la pista que suena o está cargada, además de los controles de transporte habituales (**Espacio**, flechas, **?** y **L**).
- **Reproducción continua y aleatoria:** haz clic en **Reproducir** en la cabecera de la lista para escuchar desde la pista 1, o en **Aleatorio** para un orden aleatorio. La reproducción pasa automáticamente a la siguiente pista de la lista cuando termina cada canción.

### Atajos de teclado {#hot-keys}

En la página principal, las teclas sueltas actúan sobre la **toma elegida**: la del panel izquierdo. Haz clic en su tarjeta para
elegirla. Cada tecla hace lo que hace su botón, así que una tecla que borraría pregunta antes, y una toma
que no puede hacer lo que pide una tecla (Variaciones en una toma sin partitura, por ejemplo) deja una línea en la barra
de estado que dice por qué.

| Tecla | Hace |
|---|---|
| Espacio | reproducir o pausar |
| Izquierda, Derecha | retroceder o avanzar cinco segundos |
| Mayús+Izquierda, Mayús+Derecha | la toma anterior o siguiente; en la vista Listas, la canción anterior o siguiente de la lista |
| Arriba, Abajo | volumen |
| M | abrir el rack de masterización de la toma; otra vez para cerrarlo |
| E | abrir la toma en el editor |
| I | los detalles de la toma: todo aquello con lo que se hizo, en palabras, con **Copiar** |
| N | normalizar la toma, o deshacerlo si está normalizada |
| V | abrir o cerrar el visualizador mientras suena, o Variaciones en reposo |
| T | Probar más |
| S | poner o quitar la estrella a la toma |
| P | añadir la toma a una lista |
| D | borrar la toma, tras preguntar, como su papelera |
| L | los registros; o mostrar la letra con el visualizador abierto |
| B | en el visualizador, lo que se mueve detrás de una escena sobre la imagen de la toma |
| F | pantalla completa |
| ? | mostrar u ocultar los atajos; otra vez para cerrar |
| Escape | cerrar la ventana de delante: el visualizador, los registros, el rack de masterización sobre el editor, y después el editor o cualquier otra ventana |

Las teclas de letra no hacen nada mientras escribes en un cuadro, mientras hay una ventana abierta delante, o con Ctrl,
Alt o la tecla Windows o Comando pulsada, para que los atajos del propio navegador (Ctrl+L, Ctrl+S y los demás)
sigan funcionando. La descripción emergente de un botón nombra su tecla, como en **Variaciones (V)**. Pulsa **?** en cualquier momento para ver la lista de atajos.

En la ventana del editor, Espacio y las flechas manejan el reproductor de la ventana, para la toma abierta allí, siempre que su reproductor
se muestre: en cada paso, y con el rack de masterización abierto encima. Nunca actúan mientras escribes en un cuadro,
y las teclas de letra son solo de la página principal. El piano roll tiene sus propias teclas: consulta [El piano roll](#the-piano-roll).

---

## Configuración {#settings}

Pulsa **Yeufonic** arriba a la izquierda. La configuración se guarda en el servidor, así que te sigue a cualquier
navegador y sobrevive a una reconstrucción: el formato de audio de salida para los stems y para guardar una toma, el
modelo de separación, dónde se escriben los stems, si se conservan los checkpoints de entrenamiento, y cómo se
comprueba que los instrumentales no canten.

### Almacenamiento {#storage}

**Configuración → Almacenamiento** muestra a dónde va el espacio en disco de Yeufonic y te deja recuperar parte. Entrenar un
corpus deja muchos archivos que no vuelven a hacer falta: copias hechas para el motor mientras se analizaban las canciones,
el conjunto de entrenamiento (cada canción reescrita como FLAC sin pérdida, más grande que el original), y los checkpoints
guardados por el camino. La ventana lista cada uno con su tamaño, **qué es** y **qué cuesta
quitarlo**, y quita solo lo que marques, tras una última confirmación. **Marcar los que no cuestan nada** marca
las copias que simplemente se vuelven a hacer cuando hacen falta.

Las canciones analizadas a partir de ahora guardan su voz separada como FLAC, el mismo audio en más o menos la mitad de espacio. La
ventana puede **convertir las voces WAV que ya tienes**: cada una se convierte, se comprueba que se decodifica exactamente en el mismo
audio, y solo entonces se quita el WAV. Se ejecuta en segundo plano y se puede detener.

Los checkpoints de entrenamiento merecen una segunda mirada antes de irse: cada uno es una entrada de la lista de LoRA de estilo que
puedes elegir para tomas nuevas, así que quitar los checkpoints de un corpus saca esas entradas de la lista para siempre. Su
LoRA terminada se queda y sigue funcionando. El conjunto de entrenamiento de un corpus es distinto: quitarlo deja la LoRA y sus
checkpoints en la lista, y solo volver a entrenar ese corpus lo necesita.

Tus tomas, canciones, LoRA terminadas y modelos nunca aparecen para quitar. Todo lo que pertenece a un corpus que se está
entrenando, exportando o analizando se muestra atenuado y no se puede tocar hasta que termine.

Debajo, **Ordenar automáticamente** elige lo que Yeufonic quita por ti: las copias de trabajo de cada canción
cuando termina su análisis (activado por defecto), el conjunto de entrenamiento cuando una LoRA se ha entrenado (desactivado por defecto; el corpus
necesita entonces otro **Exportar** antes de poder entrenar de nuevo), y los checkpoints de entrenamiento (se conservan por defecto).

Las imágenes y la caché de compilación de Docker están fuera de Yeufonic y no se cubren aquí; `docker system df` las muestra.

### El modelo YuE2 {#the-yue2-model}

YuE2 viene en dos tamaños, y una instalación tiene uno: **calidad completa**, que recomendamos, o **poca
memoria**, una copia más pequeña para tarjetas gráficas con poca memoria de vídeo. **Acerca de**, en el mismo menú,
dice cuál tienes. Se elige al instalar Yeufonic, no aquí:

- **En Windows**, vuelve a ejecutar el instalador. Su página de componentes ofrece los dos tamaños y marca los
  ya descargados. Cambiar descarga el otro la primera vez y conserva los dos, así que volver atrás
  no descarga nada.
- **Con Docker**, `sh scripts/fetch-models.sh` descarga la calidad completa y
  `sh scripts/fetch-models.sh --int8` el de poca memoria. Con los dos archivos en `models/checkpoints`, la
  aplicación usa la calidad completa salvo que `YUE2_CHECKPOINT=int8` esté en `.env`.

Prueba el de poca memoria si los renders son muy lentos o el motor se queda sin memoria de GPU. Entrenar una LoRA funciona
con ambos tamaños de modelo. El ajuste **Entrenamiento con el modelo de poca memoria (int8)** elige cuál: desactivado, el entrenamiento usa
el modelo de calidad completa; activado, usa el modelo con el que renderiza la aplicación. Empieza activado cuando solo está instalado el modelo de poca
memoria. El README en GitHub tiene una sección, *Choosing a model size*, con lo que cabe esperar de cada uno.

Yeufonic también puede usar el motor **yue2.cpp** en lugar de ComfyUI, para tarjetas gráficas con menos memoria,
elegido al configurarlo: en la página de componentes del instalador de Windows, o con Docker mediante
`sh scripts/fetch-models.sh --cpp`. **Acerca de** dice qué motor está funcionando, y la tarjeta de una toma qué motor la renderizó. Hace canciones, versiones e
instrumentales y transcribe grabaciones, con tus LoRA de estilo; Gemma puede redactar letras y describir imágenes
a su lado (con Docker, `--gemma`), y FLUX.2 klein dibujarlas (`--pictures`). Entrenar necesita el motor
ComfyUI: con yue2.cpp no se ofrecen los corpus ni el entrenamiento. La página
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) en GitHub tiene la
lista completa, y cómo cambiar.

**Buscar una versión nueva** es lo único de aquí que usa internet por su cuenta: cada
cuatro horas la aplicación pregunta a yeufonic.com si ha salido una versión posterior, y lo indica con una píldora junto a la
versión arriba a la derecha. Esa píldora te da el instalador, o, para una copia Docker, los dos comandos
que la actualizan. Es una petición y nada más sale del ordenador; **No comprobar** lo
desactiva. **Buscar actualizaciones** en el menú pregunta en el acto, esté esto activado o no, y responde en
el menú: qué versión tienes, y si es la última.

Cuando hay una más nueva, el menú ofrece **Obtener x.y.z**, que descarga el instalador en una instalación de Windows o pone los dos comandos en el portapapeles para una copia Docker.

**Tema** fija el aspecto de la aplicación: **Oscuro**, **Claro**, **Como el ordenador (oscuro o claro)**, que sigue el claro u oscuro de tu
sistema y cambia con él, **Estudio**, un oscuro cálido con ámbar, o **Alto contraste**, blanco y negro
con contornos marcados. Cambia al momento, y cada navegador lo recuerda
para que la página se abra así. La ventana de registros sigue oscura en todos los temas, como un terminal. El rack de masterización también sigue el tema: en el tema claro sus paneles son de plata cepillada, mientras sus mandos,
ventanas de medidores y pantallas mantienen el aspecto oscuro del hardware.

**Color de fondo**, bajo Tema, tiñe la página detrás de las tomas con un color que elijas: marca **Tinte**, luego
mueve **Tono** por la rueda de colores y **Intensidad** de un leve velo a un color intenso. La página cambia mientras
arrastras, y la elección se guarda al soltar. Las tarjetas de las tomas, los paneles y las ventanas conservan sus propios
colores, y el tema de alto contraste sigue negro.

### LLM externo {#external-llm}

Yeufonic puede escribir borradores de letra, transcribir grabaciones, marcar las secciones de las canciones y analizar los estilos de los corpus con un LLM externo en lugar del modelo Gemma local.

Usar un LLM externo tiene dos ventajas claras:
- **Ahorra memoria de GPU:** evita cargar el modelo Gemma 4 en la VRAM de la GPU (ahorrando unos 8 GB de memoria de vídeo), dejando tu tarjeta gráfica totalmente libre para la planificación y el render de audio de YuE2.
- **Borradores y análisis más ricos:** los modelos grandes en la nube suelen redactar letras con más matices y producir etiquetas de estilo detalladas para tus corpus.

**Proveedor recomendado:** recomendamos elegir un proveedor de LLM externo cuya API no tenga facturación, si lo tienes disponible — **Google Gemini** es un buen ejemplo. La API de Gemini (a través de Google AI Studio) ofrece un nivel gratuito generoso sin facturación, admite los endpoints estándar compatibles con OpenAI (`https://generativelanguage.googleapis.com/v1beta/openai/`) y acepta audio directamente para transcribir grabaciones.

Si usas una API medida o de pago por token (como los niveles de pago de OpenAI o Anthropic), analizar un corpus entero con docenas de canciones o generar descripciones para muchas tomas puede consumir rápidamente créditos de API o activar límites de gasto. Si una API externa devuelve un error de cuota o de límite de frecuencia (HTTP 429), Yeufonic muestra un aviso y te deja pasar a modelos locales para el resto de la sesión, para que los demás trabajos sigan sin interrupción. Un proveedor sin facturación evita costes inesperados.

**Configurarlo:**
1. Abre **Yeufonic → Configuración → LLM externo y letra**.
2. Pon **LLM para escribir letras y etiquetas de estilo** en **LLM externo (API compatible con OpenAI)**.
3. Escribe la **URL de la API**, la **clave de API** y el **modelo** de tu proveedor (por ejemplo, el modelo `gemini-2.5-flash` o `gemini-1.5-flash` con la URL base compatible con OpenAI de Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Haz clic en **Probar la conexión con el LLM** para comprobar tus credenciales.
5. Si el modelo elegido admite entrada de audio (como Gemini), también puedes poner **Letra a partir de una grabación** en **LLM externo** para que escuche las voces separadas.

---

## Usar Yeufonic desde un agente de IA (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

Yeufonic puede funcionar como **servidor MCP**. Eso permite que un agente de IA en el mismo ordenador, como Claude Code o Cursor, lo use por ti:
pedir una canción, una versión o un instrumental, esperarlo, reproducirlo, probarlo de otra manera, darle una imagen, ponerlo en una lista y
ordenar la biblioteca, todo con tus propias palabras («haz un instrumental EDM de un minuto en el espacio EDM y reprodúcelo»). El agente hace lo que hace la página, por las mismas rutas, así que una toma que empieza es una
toma corriente de tu biblioteca.

### Configurarlo {#setting-it-up}

1. **Actívalo.** Abre Configuración y pon **Servidor MCP** en **Activado**. Está desactivado por defecto, porque una petición puede iniciar trabajo en la GPU.
2. **Conecta tu agente** a la dirección de la aplicación con `/mcp` al final: la dirección en la que abres Yeufonic, por ejemplo
   `http://localhost:8090/mcp`. En Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Otros clientes toman la misma dirección como servidor HTTP. Los que leen un archivo de configuración suelen querer algo como
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. No hace falta inicio de sesión ni clave.
3. **Pide.** Arranca tu agente desde cualquier carpeta y describe lo que quieres.

**¿Qué dirección?** Es la dirección en la que abres Yeufonic, con `/mcp` al final.
- **Docker:** `http://localhost:8090/mcp`.
- **La instalación de Windows:** el puerto de la aplicación está en `settings.ini` (`app_port`, 8090 salvo que lo cambiaras, por ejemplo para funcionar junto a
  una copia Docker). Con `app_port = 8091` es `http://localhost:8091/mcp`.
- **Agente en WSL, aplicación en Windows:** esto no conecta. La aplicación de Windows solo escucha en la dirección de bucle local propia de Windows, a la que WSL no puede
  llegar (Docker dentro de WSL va bien, porque también está en WSL). Ejecuta el agente desde Windows (PowerShell o la versión de Windows de
  tu agente), o activa la red en espejo de WSL (`networkingMode=mirrored` bajo `[wsl2]` en `.wslconfig`, y luego `wsl --shutdown`),
  que hace que `localhost` sea el mismo en ambos lados.

Si tu agente dice que el servidor **necesita autenticación**, casi siempre es porque el ajuste sigue desactivado: actívalo, y luego
vuelve a conectar el agente (en Claude Code, `/mcp`). Vuelve a conectar también después de reiniciar Yeufonic, porque un reinicio corta la conexión.

### Qué puedes pedir {#what-you-can-ask-for}

| Pide | Qué pasa |
|---|---|
| «Lista mis últimas tomas», «muestra las tomas del espacio EDM» | Lista las tomas, las más recientes primero, con un id corto, cuándo se hizo cada una, su duración y su estilo |
| «Haz un instrumental de un minuto en estilo synthwave» | Planifica y renderiza un instrumental. Se pueden nombrar una duración, un espacio y una [LoRA de estilo](#style-loras) |
| «Haz una canción en estilo folk con esta letra» | Lo mismo para una canción, a partir de la letra que des |
| «…con armonía atrevida, interpretación ajustada, en fa sostenido, a 100 BPM» | Cualquier ajuste de una toma nueva con los nombres que usa la página: [Armonía](#harmony), [Variedad del plan](#plan-variety), la [interpretación](#interpretation), fijar tonalidad y tempo, y para una canción **Seguir esta estructura exactamente** y **Las voces siguen las indicaciones**. Si no se dice, una toma nueva empieza donde empieza la de la página: Variada y Amplia |
| «Escribe una letra sobre un tren nocturno, en tono hablado» | El **Escribir letra** de la propia aplicación, con sus formas de canción, líneas por sección y tonos. El agente también puede escribir la letra por su cuenta |
| «Haz una versión de *la grabación* en estilo jazz» | Hace una versión a partir de una grabación que ya está en tu biblioteca. Necesita una partitura (transcríbela antes en la aplicación). Sin letra tuya, usa las palabras oídas en la grabación |
| «Reprodúcela» | Abre la toma en tu navegador, donde suena |
| «Ponle estrella a esa», «llámala Sunrise», «muévela al espacio Folk» | Pone estrella, renombra o mueve una toma |
| «Vuelve a renderizarla con una semilla nueva», «para eso» | Vuelve a renderizar una toma, o cancela una en curso |
| «Dame unas cuantas más como esa» | Vuelve a renderizar la toma con semillas nuevas, como varias tomas nuevas para escuchar juntas |
| «Cántala otra vez», «pruébala en cada interpretación» | **Cantar de nuevo** (una voz nueva para la misma partitura) o **Variaciones** (la misma partitura y semilla, tocadas de cada manera). Las variaciones se guardan dentro de la toma, como Probar más |
| «Canta esa melodía con esta letra» | **Nueva letra**: la misma melodía, tonalidad y tempo con otra letra, como toma nueva |
| «Haz un instrumental con ella» | La misma partitura con la melodía en un instrumento y sin canto, como toma nueva |
| «Escríbele un plan nuevo, más animado» | Un plan nuevo para una toma que aún no tiene audio (planificada sin renderizar, o cuyo plan falló). Una toma con audio no se toca: pide una toma nueva en su lugar |
| «Deja la suelta aparte» | **Sacar**: una toma guardada dentro de otra pasa a ser una toma propia |
| «Dale una imagen» | Hace una imagen nueva para la toma, como el botón **Imagen** del editor, y da un enlace que la abre. Una imagen dibujada en este ordenador espera a que no se esté haciendo ninguna canción |
| «Pon las tres mejores en una lista llamada Road trip» | Crea listas, muestra lo que tienen, y añade o quita tomas. Poner una toma en **Me gusta** le pone estrella |
| «Búscame un estilo synthwave», «guarda ese estilo como Night drive» | Busca entre tus estilos guardados y los incorporados, y guarda un estilo con un nombre para el menú de estilos |
| «Crea un espacio llamado Drafts» | Crea un espacio nuevo para guardar tomas |
| «Transcribe *la grabación*» | Transcribe una grabación a partitura, para poder hacer una versión. Deja en paz una grabación que ya tiene partitura salvo que se pida |
| «Separa eso en voz e instrumentos» | Separa una toma terminada en sus partes (cuatro, seis, o solo voz e instrumentos) y te da un enlace a cada archivo y otro al conjunto entero en zip |
| «Guarda la receta de esa toma», «…y la toma con ella en un zip MP3» | Da la receta de la toma (lo que la hizo, no su audio) para mostrarla, cambiarla o guardarla como archivo, con enlaces para descargarla sola o con el audio en un solo zip |
| «Importa *Night Ferry.yeufonic.json* en Drafts y renderízalo» | Una toma nueva desde un archivo de toma, con el plan, renderizada cuando lo pidas. Dice qué LoRAs nombradas en el archivo no están instaladas, y cuándo una versión llegó como canción |
| «Impórtala otra vez en estilo dream pop, misma partitura y semilla» | Cambia la receta antes de importarla, así solo cambia lo que nombras |
| «¿Qué motor hizo esa toma?», «¿qué motor está funcionando?» | Dice qué motor renderizó una toma, y cuál usa ahora Yeufonic (ComfyUI o yue2.cpp) |
| «¿Está ocupado Yeufonic?» | Dice si el motor está listo, qué se está ejecutando y con qué progreso, qué espera, y si se está entrenando una LoRA |
| «Borra esa toma» | Muestra lo que se iría y te pregunta antes; ver más abajo |

Hacer una toma lleva minutos. El agente la empieza y espera, informando del progreso, así que puedes pedir lo siguiente mientras tanto.

### Cómo puede ir: un ejemplo {#how-it-can-work-an-example}

Una conversación, de una idea a una lista. Tú hablas; el agente elige las herramientas (la columna del medio solo está para mostrar lo que
pasa) y te dice lo que volvió.

| Tú dices | El agente | Lo que obtienes |
|---|---|---|
| «Escribe una letra sobre la última noche de un farero, estilo folk, forma de historia. Luego haz una canción con ella en un espacio nuevo llamado Coast.» | `write_lyrics`, `create_space`, `make_song`, luego `wait_for_take` hasta que termina | La letra, titulada *The Last Light*, que se te muestra; un espacio llamado Coast; una canción planificada y renderizada allí, con el progreso sobre la marcha |
| «Reprodúcela.» | `get_take`, luego abre su `listen_url` | Suena en tu navegador |
| «Buena melodía. Pruébala más suelta e inquieta, y dame una sin canto.» | `make_variations` con suelta e inquieta, `instrumental_from_take` | Dos tomas dentro de la canción, y un instrumental a su lado |
| «Enséñame lo que tenemos.» | `list_takes` en Coast, y con `inside` para la canción | Una lista con un id corto para cada una, para que puedas decir «3f9a» en lugar de un título |
| «Deja 3f9a aparte, ponle estrella y dale una imagen.» | `take_out`, `star_take`, `make_picture` | La suelta como toma propia, con estrella (así que también en favoritas), con un enlace a su imagen |
| «Pon esa y el instrumental en una lista llamada Coast demos.» | `create_playlist`, `add_to_playlist` | Una lista con las dos |
| «Guarda el estilo como Coastal folk.» | `save_style` | **Coastal folk** en el menú de estilos de la aplicación, listo para la próxima vez |
| «Ahora un dúo: esta letra, con indicaciones [male voice] y [female voice], cada sección tal como está escrita.» | `make_song` con `follow_structure` (un plan nuevo, porque cambian las secciones) | Una canción nueva que planifica exactamente tus secciones, en orden, con cada línea indicada movida a donde canta esa voz |

Todo lo que hizo está en la biblioteca como si lo hubieras hecho en la página: abre cualquier toma en el editor, masterízala, o sigue allí.
Cuando un paso no se puede hacer, el agente recibe el motivo de la propia aplicación («this take is an instrumental already», «nothing here can draw a
picture») y lo transmite, así que oyes la misma respuesta que daría la página.

### Todo lo que puede hacer {#everything-it-can-do}

No necesitas estos nombres: pides con tus propias palabras y el agente elige. Están aquí para que veas lo que existe, y para que puedas
decirle a tu agente cuál quieres.

| Herramienta | Qué hace |
|---|---|
| `list_takes` | Lista las tomas, las más recientes primero, opcionalmente solo las que coinciden con unas palabras, en un espacio nombrado, o con estrella. Muestra un id corto |
| `get_take` | Una toma completa: cómo se hizo, su estado, cualquier error y, cuando tiene audio, un enlace que la reproduce. Puede incluir la partitura |
| `wait_for_take` | Espera (hasta un minuto cada vez, más o menos) a una toma que se está haciendo, y dice si ha terminado |
| `make_instrumental` | Planifica y renderiza un instrumental a partir de un estilo, con una duración, un espacio y una LoRA de estilo si los nombras, y secciones si las das |
| `make_song` | Lo mismo para una canción, a partir de una letra |
| `make_cover` | Una versión a partir de una grabación de la biblioteca, con su partitura y, salvo que des otras, su letra |
| `try_more` | Varias tomas más a partir de una existente, con semillas nuevas |
| `sing_again` | La misma partitura cantada otra vez con una semilla nueva: una voz nueva, como toma nueva |
| `make_variations` | La misma partitura y semilla en cada interpretación nombrada (o en todas), guardadas dentro de la toma |
| `new_words` | La misma partitura cantada con otra letra, como toma nueva |
| `instrumental_from_take` | La misma partitura como instrumental, como toma nueva |
| `replan_take` | Un plan nuevo para una toma sin audio, opcionalmente con otra Armonía, Variedad del plan, tonalidad o tempo |
| `take_out` | Convierte una toma guardada dentro de otra en una toma propia |
| `write_lyrics` | Una letra a partir de un encargo, con una forma y un tono de canción, escrita como lo hace Escribir letra en la página |
| `render_take` | Renderiza una toma planificada, o vuelve a renderizar una terminada (con una semilla nueva si se pide) |
| `cancel_take` | Detiene una toma en cola o en curso |
| `make_stems`, `get_stems` | Separa una toma en partes, y luego lista las partes con un enlace a cada una y al conjunto entero en zip |
| `list_recordings`, `transcribe_recording` | Muestra las grabaciones de la biblioteca y si cada una tiene partitura; transcribe la que no la tiene |
| `list_style_loras` | Las LoRA de estilo instaladas, con sus palabras disparadoras y las fuerzas guardadas con ellas |
| `list_spaces`, `move_take`, `create_space` | Los espacios y lo que contiene cada uno; mueve una toma a otro; crea un espacio nuevo |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | Las listas y las tomas de una; crea una; mete o saca tomas |
| `make_picture` | Una imagen nueva para una toma, con un enlace que la abre. `get_take` también da el enlace a la imagen de una toma |
| `list_styles`, `save_style` | Tus estilos guardados y los incorporados, buscados por palabras; guarda un estilo con un nombre |
| `star_take`, `rename_take` | Pone o quita la estrella de una toma; cambia su título |
| `delete_take` | Borra una toma para siempre, tras mostrártela y recibir tu visto bueno |
| `save_take_recipe` | La receta de una toma, con enlaces para descargarla sola o con el audio en un solo zip, en el formato pedido |
| `import_take` | Una toma nueva desde una receta, en un espacio si se nombra, lista para renderizar; dice qué LoRAs no están instaladas y cuándo una versión llegó como canción |
| `status` | Si el motor está listo, qué se ejecuta y qué espera, y si se está entrenando una LoRA; nombra el motor en uso (ComfyUI o yue2.cpp) |

### Ideas para usarlo {#ideas-for-using-it}

- **Un lote de ideas, y luego elegir.** «Haz cinco instrumentales EDM de un minuto en estilos distintos, en el espacio EDM.» Los empieza uno tras
  otro y te avisa según termina cada uno. Escuchas, y luego dices «pon estrella al segundo y al cuarto y borra el resto».
- **Iterar sobre una idea.** «Haz un instrumental en un estilo de sintetizador soñador y reprodúcelo», luego «ahora lo mismo con más batería», y
  «dame cuatro más como el segundo». El agente lleva la cuenta de qué toma es cuál, así que puedes hablar de ellas por posición o
  por lo que dijiste de ellas.
- **Versiones sin ir haciendo clic.** «Transcribe *la maqueta*, y luego haz tres versiones: folk, synthwave y jazz.» Transcribe
  primero la grabación si no tiene partitura, y luego hace las versiones en el espacio que nombres.
- **Trabajar con una LoRA.** «Lista mis LoRA de estilo, y luego haz un instrumental con la de jazz.» La palabra disparadora y las fuerzas guardadas se
  gestionan por ti, cosa fácil de hacer mal a mano.
- **Letra del agente, o de la aplicación.** El agente puede escribir la letra por su cuenta: «Escribe una letra sobre un tren nocturno y haz una canción
  con ella en estilo folk.» Yeufonic solo ve la letra terminada. O pide la de la aplicación: «usa el autor de letras de Yeufonic, forma hip-hop,
  tono hablado», que la escribe como lo hace **Escribir letra** en la página y la devuelve para una canción.
- **Misma melodía, otra letra.** «Canta esa otra vez con esta letra para la segunda estrofa»: `new_words` conserva la melodía, la tonalidad y el tempo,
  donde una canción nueva a partir de la letra escribiría una melodía nueva.
- **Comparar ajustes.** «Haz la misma canción dos veces, una con armonía Conocida y otra con Atrevida, con la misma semilla», y luego
  «ahora dale a la mejor cada interpretación». Los ajustes se piden por su nombre, así que puedes diseñar una pequeña prueba en una frase.
- **Listas a partir de la escucha.** «Pon todas las tomas con estrella de esta semana en una lista llamada Week 43», o «saca los instrumentales de
  Road trip». Favoritas son las tomas con estrella, así que la estrella y las favoritas son siempre la misma lista.
- **Stems para todo un lote.** «Separa mis cinco tomas más nuevas en voz e instrumentos y dame los enlaces.» Se ponen en cola una detrás
  de otra, y detrás de cualquier render que esté ejecutando la GPU.
- **Orden en la biblioteca.** «Encuentra las tomas con el mismo título, dime cuál es la más nueva, y borra las más antiguas», o «mueve todo
  lo que hice hoy a un espacio llamado Drafts». Trabaja con ids y pregunta antes de borrar.
- **Comprobar antes de un trabajo largo.** «¿Está ocupado Yeufonic?» antes de poner en cola un render largo o un lote, para no quedarte detrás de un entrenamiento.
- **Parte de una tarea más grande.** Como es una herramienta a la que el agente puede llamar, puede formar parte de algo mayor: hacer una pista para un vídeo y
  escribir la nota que la acompaña, o montar un lote del tamaño de una lista y nombrar las tomas según una lista.

El agente no puede oír una toma, así que no puede juzgar cómo suena: tú escuchas, y él hace el trabajo pesado. Tampoco es un
atajo para saltarse el motor: la GPU sigue haciendo un trabajo cada vez, así que un lote grande es una cola larga.
- **Compartir una toma.** «Guarda mi toma con estrella con su receta en un zip FLAC» da un archivo que otra persona puede escuchar y rehacer:
  pide a su agente que «importe este archivo de toma y lo renderice». O «impórtala otra vez con la LoRA de jazz, misma partitura y
  semilla», para oír el mismo plan de otra manera.

### Conviene saber {#things-to-know}

- **Las tomas pueden compartir título,** así que el agente trabaja con el **id** de una toma y muestra uno corto (la columna `short_id`) cuando lista tomas.
  Puedes nombrar una toma por el comienzo de su id, cuatro caracteres o más, siempre que solo una toma empiece así. Si son dos, te lo dice
  y pide más.
- **Borrar pregunta dos veces.** El agente te muestra primero lo que borraría, incluida cualquier otra toma con el mismo título, y solo borra
  cuando dices que sí. Una toma con estrella necesita que lo digas explícitamente. Una toma borrada, con su audio, no se puede recuperar.
- **Los espacios y las LoRA de estilo se nombran,** no se numeran: «en el espacio EDM», «con la LoRA de jazz». Un nombre que no coincide con nada recibe la lista de
  lo que hay, y no se crea nada. La palabra disparadora de una LoRA se añade al estilo por ti, ya que una LoRA hace muy poco sin ella.
- **Una toma nueva empieza donde empieza la de la página:** Armonía en Variada y la interpretación Amplia, salvo que nombres otras. En un motor
  sin el nodo de armonía empieza en Conocida, ya que la Armonía no puede subir más allí.
- **Las imágenes y las letras esperan su turno.** Una imagen dibujada o descrita en este ordenador espera a que no se esté haciendo ninguna canción, y las letras
  escritas en este ordenador hacen cola con el resto del trabajo de GPU, así que el agente puede decir «aún se está haciendo» y volver a mirar después.
- **Un instrumental siempre se planifica con una estructura con tiempos,** calculada a partir de la duración que pides (unos dos minutos y medio
  si no dices nada). Sin tiempos, el planificador escribe planes demasiado largos para usarse. Nombra tus propias secciones y se usan tal cual.
- **Solo en este ordenador.** Se aplican las mismas comprobaciones de nombre de host y de origen que en la página, y no hay inicio de sesión, así que desactiva el ajuste
  cuando no lo uses, y no expongas el puerto a una red en la que no confíes.

## Registros del sistema {#system-logs}

La aplicación escribe un registro consolidado en tiempo real de cada acción importante — planificación de partitura, render, transcripción de audio, separación de stems y entrenamiento de LoRA — con los prefijos `INFO`, `WARN` y `ERROR`.

- **Consola en el navegador:** haz clic en el botón **Registros** de la barra superior (o pulsa **L**) para abrir una consola flotante, que se puede arrastrar y cambiar de tamaño. Se queda abierta sin bloquear la página, lo que te permite poner tomas en cola y seguir la generación en tiempo real.
- **Ventana aparte:** haz clic en **↗ Separar** en la cabecera de la consola (o ve directamente a `/logs`) para abrir una ventana dedicada a los registros.
- **En el terminal:** los registros rotan automáticamente en `data/logs/yeufonic.log` en el anfitrión, donde puedes seguirlos en directo:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## La página propia del motor {#the-engine-s-own-page}

El motor es ComfyUI (salvo que esta instalación use yue2.cpp, cuya página es un simple banco de pruebas), y su propia interfaz es accesible: <http://localhost:8189> con Docker, o
<http://localhost:8188> con la instalación de Windows (el `engine_port` en `settings.ini`). Solo responde
en esta máquina, sin inicio de sesión.

- **Es el mismo motor y la misma GPU que la aplicación.** Un trabajo ejecutado allí aparece en la cola de la aplicación como venido
  de fuera, y los trabajos de la propia aplicación lo esperan.
- **Su historial muestra cada grafo que envió la aplicación**: el plan, el render y las transcripciones, con
  cada ajuste tal como lo recibió el motor. Es un buen sitio para ver exactamente a partir de qué se hizo una
  toma.

---

## Cuando algo va mal {#when-something-is-wrong}

**La cabecera dice que falta el motor.** La aplicación funciona sin él y lo dice. Los renders esperan.
Comprueba que el contenedor del motor está en marcha.

**Una canción no termina.** Normalmente demasiada fuerza de planificador. Baja el Planificador de la LoRA a 0.5. El
límite de duración la detendrá de todos modos.

**Una LoRA parece no hacer nada.** Comprueba que la palabra disparadora está en el Estilo, y que la fuerza que
subiste es una que el archivo tiene de verdad — el selector atenúa la otra.

**Una toma dice *Render débil*.** Salió mucho más baja de lo normal de principio a fin. Algunas tomas
así solo son bajas; otras suenan finas o distorsionadas. Haz clic en el aviso para normalizarla, lo que
la sube a la sonoridad habitual y la marca *Normalizada*. Si sigue sonando mal, prueba otra
semilla, y mantén el Sonido de esa LoRA en 0.5 o menos. Pasa sobre todo en versiones a través de una LoRA de estilo
entrenada aquí.

**Normalizar el volumen.** Márcalo en el editor y cada toma hecha mientras esté marcado se lleva a la
sonoridad habitual al terminar, y se marca *Normalizada*. Una toma hecha sin él se puede normalizar
después con el botón del altavoz en la parte superior de su tarjeta. El archivo tal como se renderizó se guarda a su lado, y
hacer clic en *Normalizada* vuelve a él. Lo fuerte que se hace se fija en Configuración, en *Normalizar a*.
Sin marcar, una toma conserva el nivel con el que se renderizó.

**Un instrumental cantó.** Consulta *Cuando un instrumental canta* más arriba. Es un fallo del modelo; una semilla nueva
suele arreglarlo.

**Una toma no se vuelve a renderizar.** Puede que se haya borrado su grabación. Las versiones conservan su audio y su
partitura, pero no se pueden volver a renderizar a partir de una grabación que ya no existe.

**No suena nada, pero la forma de onda se mueve.** Comprueba el control de volumen y que no esté seleccionado un stem —
el reproductor sigue lo último en lo que se hizo clic.
