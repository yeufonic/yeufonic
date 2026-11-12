# Yeufonic — o guia

Este guia é sobre **usar** o app. A instalação, e tudo o que você precisa antes de ele funcionar, está no
[README](https://github.com/yeufonic/yeufonic#readme).

O app faz músicas com o YuE2, um modelo que trabalha em duas etapas: primeiro escreve um **plano de partitura** —
a melodia, os acordes e as seções, como texto — e depois **renderiza** esse plano em áudio.
Quase tudo o que vem a seguir decorre dessa divisão. Um plano custa segundos e pode ser lido, editado e
descartado; um render custa minutos. Por isso o app deixa você ver o plano primeiro.

---

## Sua primeira música {#your-first-song}

1. Clique em **+ Música** no topo do painel esquerdo. A janela do editor se abre.
2. **Escreva um estilo.** Uma frase, não uma lista de tags: *“warm indie rock, expressive female lead, jangly
   guitars, 96 BPM”*. É o que mais influencia o resultado.
3. **Adicione uma letra**, ou clique em **Escrever letra** e deixe o Gemma rascunhá-la a partir de uma descrição.
4. Clique em **Escrever o plano da partitura**. A janela se fecha e o take aparece no painel esquerdo. Com
   **Renderizar assim que o plano estiver pronto** marcado ao lado do botão, como vem de início, o plano
   segue direto para o render.

Para ler o plano antes de qualquer render, desmarque primeiro **Renderizar assim que o plano estiver pronto**. O
take então para no plano: abra-o, e na página **Partitura** dele, **Escrever um plano novo** joga os dados de novo para uma melodia de que você não
gostou pelo preço de alguns segundos, e **Renderizar esta partitura** a renderiza. Um take que ainda não tem áudio
é completado; um que já tem áudio é renderizado como um take novo ao lado, então um render nunca
sobrescreve um que você queira guardar.

O take aparece na biblioteca à direita e toca na barra de baixo.

### O painel do take e o editor {#the-take-panel-and-the-editor}

O **painel esquerdo** mostra o último take em que você clicou, só para leitura: o estilo, os ajustes de som, as
primeiras linhas da letra e a partitura como tom, andamento, duração e os acordes de cada seção.
**+ Música**, **+ Cover** e **+ Instrumental** no topo começam algo novo; o do tipo
do take fica em destaque. A seta ao lado do painel o recolhe, para que os takes fiquem com a largura,
e o traz de volta. Teclas simples agem sobre o take que o painel mostra (M para o rack de masterização, E para
o editor e outras): veja [Atalhos de teclado](#hot-keys).

Criar e mudar um take acontece na **janela do editor**. O botão principal dele no painel diz o que
cabe: *Editar e renderizar de novo*, ou *Revisar o plano e renderizar* quando há um plano esperando. Os botões
**Partitura** e **De novo** de um cartão também o abrem, assim como um clique duplo em um cartão. Ele tem três
colunas (a música, a letra e o som), tudo à vista, com a partitura em uma aba própria.

Fechar a janela, com **Fechar**, o X ou Esc, mantém o que você escreveu.

O botão depois de **Fechar**, no canto superior direito, faz a janela ocupar toda a janela do navegador, e
um segundo clique a devolve ao tamanho habitual. A janela abre como você a deixou da última vez. Ocupando a janela toda,
a coluna da letra ganha toda a altura: a caixa da letra (quando já tem palavras) e a estrutura crescem no
espaço, e o player fica no pé da coluna.

A linha de cima da janela tem, maiores, os botõezinhos do cartão do take: Cantar de novo, Variações,
Tentar mais, Dentro, Tirar, Normalizar e Mover, cada um onde o cartão o mostraria. Normalizar fica verde
enquanto o take está normalizado, e um clique então o devolve ao nível em que foi renderizado; Dentro
acende enquanto o take contém outros, e fecha a janela para mostrá-los sob o take.

### Uma voz gravada {#a-recorded-voice}

Um take pode ser cantado com uma voz treinada a partir de gravações de alguém cantando: a sua, ou a de quem canta num corpus. O take é renderizado como sempre; depois o vocal é separado, cantado de novo com a voz e mixado de volta sobre o resto. As vozes são criadas e gerenciadas na página **Vozes**, pelo menu. É preciso o serviço de voz opcional (no README, “Recorded voices”); sem ele, os campos de voz ficam ocultos.

#### Criar uma voz {#making-a-voice}

**Nova voz** cria uma voz a partir das suas próprias gravações, ou uma treinada com as músicas de um corpus. Uma voz de gravações começa vazia, e a página dela as reúne:

- **Gravar…** abre o gravador. Cada take que você guarda vai para a voz do jeito que foi cantado, nunca afinado automaticamente.
- **Enviar…** aceita arquivos de áudio.
- **Da biblioteca…** adiciona gravações que você já tem, como um vocal gravado para um cover. Cada uma tem um player para ouvir antes, e é ligada, não copiada.

Cada gravação diz se é uma voz sozinha (**só vocal**, marcado no que você gravou aqui) ou uma música, que é separada primeiro. A página conta o canto: uns dez minutos ao longo da sua extensão são de sobra, e uma gravação curta já dá uma voz reconhecível. Depois pressione **Treinar**.

O treino espera a vez na GPU e mostra o progresso no indicador de tarefas e no registro. **Treinar de novo** treina outra vez com as gravações como estão agora, ou com as músicas do corpus. **Do que ela aprendeu** guarda o vocal separado de cada música e os trechos treinados, para ouvir. Configurações → *Treinamento de vozes* define de quanto canto uma voz aprende e com quantas passadas.

#### Configurações de uma voz {#settings-for-a-voice}

São os padrões da voz, definidos na página dela. Um take pode ter os próprios (abaixo).

| Configuração | O que faz |
|---|---|
| **Oitava** | Sobe ou desce a voz uma oitava inteira, para quem canta numa extensão longe da do take. |
| **Nível do vocal**, **Nível dos instrumentos** | O equilíbrio do remix. |
| **Semelhança** | Quanto a voz se mantém nos sons próprios de quem canta. Mais alto soa mais parecido, e pode soar mais processado. Em 100% a voz pode perder a letra: palavras que ela nunca ouviu cantadas podem sair embaralhadas, e o editor avisa. |
| **Formante** | O tamanho da voz, com a mesma altura: *Mais grave* soa maior, *Mais brilhante* menor. |
| **Mistura** | Quanto do vocal a voz canta; o resto é o vocal renderizado de onde ela saiu. |
| **Sala** | Uma sala curta sob o vocal convertido (*Seco*, *Sutil* ou *Mais*), para ele se assentar na mixagem. |
| **Brilho** | *Auto* levanta a parte aguda até igualar a do vocal renderizado; *Desligado* deixa como saiu da conversão. |
| **Respirações e consoantes** | Quanto elas mantêm os sons do vocal renderizado: *Mantidas* ficam nítidas mas carregam um traço dele, *Convertidas* podem rasgar. |
| **Dinâmica** | De quem o vocal segue o volume de frase em frase: do take, como renderizado, ou das próprias variações da voz. |

#### Usar uma voz num take {#using-a-voice-in-a-take}

No editor, escolha a voz em **Voz gravada**. **Configurações**, ao lado, abre as configurações acima só para este take; o take as mantém, e o botão indica *configurações próprias* quando elas diferem das da voz.

#### Ouvir uma voz antes de usá-la {#hearing-a-voice-before-you-use-it}

**Ouvir**, nessas configurações, toca a voz cantando um loop curto, *Um homem cantando* ou *Uma mulher cantando*, sem parar enquanto você muda as configurações, assim você ouve cada mudança ao fazê-la. **Salvar como nova voz…** guarda o que você ouve como uma voz própria, no mesmo modelo.

**Seus próprios loops.** Os dois loops vêm com o app; você pode adicionar os seus:

1. Encontre ou grave de 15 a 30 segundos de uma só voz cantando sozinha: seca, sem acompanhamento, reverberação nem harmonias.
2. Salve como FLAC, WAV, MP3, M4A, OGG ou Opus, com o nome que quer ver na lista.
3. Coloque na pasta *voice-loops* da biblioteca: `data/voice-loops` com Docker; no Windows, dentro da pasta `data` da instalação, a menos que `data_dir` em `settings.ini` indique outra pasta de biblioteca.
4. Abra **Configurações** de novo: ele aparece pelo nome do arquivo.

#### Compartilhar e importar vozes {#sharing-and-importing-voices}

- **Baixar voz** salva uma voz treinada como zip para dar a alguém.
- **Importar uma voz…** adiciona uma: esse zip, ou um modelo RVC de outro lugar (o zip dele, ou o .pth e o .index escolhidos juntos). Uma voz importada sem o índice pode recebê-lo depois com **Adicionar o índice…**: Semelhança se baseia nele.
- **Vozes prontas**, modelos RVC treinados por outras pessoas, podem ser encontradas em sites como [voice-models.com](https://voice-models.com/): **Importar uma voz…** aceita o zip como foi baixado.
- A receita de um take nomeia a voz dele e as configurações do take para ela, e importá-la recupera a voz com esse nome nesta instalação, se houver.

#### Conseguir uma voz limpa {#getting-a-clean-voice}

O resultado é um vocal convertido sobre um acompanhamento separado, então encaixa com menos naturalidade que um vocal que o próprio modelo cantou.

- Uma voz aprende a reverberação e a produção da gravação junto com quem canta, então um canto limpo e seco com um vocal principal claro dá uma voz mais limpa que um corpus de músicas mixadas.
- Uma única música ou uma gravação curta dá uma voz reconhecível, mas que pode borrar palavras que nunca ouviu cantadas.
- Uma voz treinada com muito mais canto, por muito mais passadas, como costumam ser as vozes prontas, mantém as palavras mesmo com uma Semelhança alta.

### Ajustes avançados {#advanced-settings}

O botão **Avançado** no cabeçalho do editor abre ajustes só para este take. A maioria das músicas
nunca precisa deles. Eles são salvos com o take, então *Editar e renderizar de novo* os encontra como você os deixou.
O botão acende quando algum ajuste difere do padrão, e **Restaurar padrões** devolve
todos.

Alguns agem sobre o plano, e outros sobre o render e o arquivo final:

- **Passos de difusão** (16–64, padrão 32): quantos passos o decodificador de áudio dá. Mais passos demoram
  mais para renderizar.
- **Seguir o estilo** (0–100, padrão 1.0): com que firmeza a música segue o estilo e a letra, a orientação
  da etapa que transforma a partitura em som (CFG). Acima de 1.0 ela se aproxima deles; abaixo, se afasta. A
  diferença é sutil em valores pequenos, e um render leva um pouco mais. Qualquer valor que o motor aceite pode ser digitado:
  uma orientação muito alta tende a soar áspera mais do que fiel. Aparece quando o motor tem o recurso: yue2.cpp, ou o motor ComfyUI
  na versão mais recente (reconstrua um motor Docker antigo para tê-lo).
- **Evitar:** palavras de que se afastar, como “drums” ou “rap vocals”. Elas são acrescentadas ao estilo
  como “avoid: …”. É uma dica para o planejador, não uma garantia: o renderizador não tem prompt negativo.
- **Fixar tom:** o plano é transposto para este tom depois que o planejador o escreve. O planejador ignora
  um tom citado no estilo, então isso é feito na própria partitura: cada nota e cada acorde se desloca o
  mesmo intervalo e a armadura é reescrita. Um plano menor continua menor, e só a
  tônica se move. Um plano que o app não consegue ler com certeza, como um em um modo ou com uma mudança de tom
  no meio, fica no tom do planejador e o log diz isso.
- **Fixar andamento** (BPM): o plano é fixado neste andamento, que substitui qualquer andamento do estilo ou da
  própria partitura do planejador, e o render o segue.
- **Limite de tokens da partitura** (padrão 8192): o máximo que o planejador pode escrever. Um limite menor impede que o plano de uma música curta
  se estenda.
- **Limite de acorde sustentado** (compassos, padrão 8): o máximo de compassos que o planejador fica em uma mesma fundamental antes
  de ter que mudar.
- **Bônus de harmonia fora do tom** (0–10, padrão 0): com que força o planejador é empurrado para acordes
  emprestados e fundamentais fora do tom principal. Esses dois agem sobre as escolhas do planejador, então aparecem como
  uma diferença nos acordes do plano mais do que como uma diferença clara ao ouvido. Compare na janela
  Partitura.
- **As vozes seguem as indicações** (uma caixa de seleção sob a caixa da letra, que aparece quando a letra tem uma indicação de voz como
  `[male voice]`; ligada para um take novo): a melodia de cada linha indicada se move por oitavas até onde canta a voz que
  a indicação nomeia. Veja [A letra](#the-words).
- **Seguir esta estrutura exatamente** (uma caixa de seleção sob a caixa da letra, não em Avançado; músicas; desligada por padrão): o plano escreve exatamente as seções que a letra nomeia, em
  ordem, e nenhuma outra. Desligada, o planejador dá forma à música por conta própria e muitas vezes acrescenta uma intro, um outro ou um
  interlúdio, ou deixa uma seção de fora. Um plano ainda pode terminar antes da lista.
- **As seções começam diferente** (Seguir a harmonia, Sempre, Nunca): se uma seção pode começar com os mesmos
  acordes da anterior. *Seguir a harmonia* liga a partir de Colorida e deixa desligado abaixo disso; *Sempre* e
  *Nunca* decidem para este take em qualquer nível, para comparar dois planos com e sem.
- **Volume alvo:** o nível para o qual um take é normalizado. Só se aplica quando a normalização está ligada.
- **Fade final** (segundos, padrão 3): a duração do fade quando um take é cortado no limite de
  duração.

### O que pôr na caixa Estilo {#what-to-put-in-the-style-box}

O YuE2 lê isto como a descrição de uma gravação, então descreva uma gravação. Idioma, gênero, voz,
instrumentos, clima, andamento e produção, mais ou menos nessa ordem, tudo em uma frase. Listas de tags soltas
funcionam pior, e marcadores de seção como `[Verse]` vão na letra, não aqui.

Os chips **Vocal** abaixo escrevem no estilo por você: feminina, masculina ou dueto, e um caráter
como soprosa ou rouca. São um atalho de digitação, e você pode editar o resultado à mão.

### Rascunhar a letra {#drafting-the-lyrics}

**A estrutura.** Acima da caixa da letra, enquanto ela não tem palavras, uma música tem uma **estrutura** para montar, como um instrumental: uma lista de seções que você pode reordenar, remover e acrescentar (intro, verso, pré-refrão, refrão, ponte, interlúdio, outro).

- **Começar de…** a preenche com uma forma comum, e a dica de cada forma diz para que ela serve.
- Um **interlúdio** é uma passagem instrumental: quem escreve põe a tag dele numa linha própria, e o planejador o toca com a voz instrumental.
- **Colocar seções na caixa da letra** coloca as tags como seções vazias para escrever embaixo à mão.
- Assim que a caixa tem palavras, a letra é o que é cantado e a estrutura sai do caminho.

**Escrever letra**, ao lado da caixa da letra, pergunta sobre o que é a música e escreve palavras para as seções que você montou.

- **Linhas por verso ou refrão** define o tamanho de cada um: mais linhas numa seção fazem uma música mais longa, porque o planejador escreve mais ou menos tanta música quanto há palavras.
- O estilo acima define o clima.
- O Gemma escreve o rascunho no mesmo motor, e ele chega à caixa com um título se você não tinha dado um; um [LLM externo](#external-llm) pode escrevê-lo no lugar, configurado em Configurações.
- A janela fecha assim que o rascunho começa, e o progresso aparece ao lado da caixa da letra.

Os botões do editor de letras também adicionam qualquer uma dessas seções, além de indicações de voz (+ Homem, + Mulher, + Ambos).

**Como as linhas soam** define o ritmo e a rima que quem escreve busca, de *Natural* (o padrão) a *Curto e direto* ou *Longo e fluido*: [A letra](#the-words) lista cada opção.

É um primeiro rascunho. As linhas têm métrica e rima, mas um modelo recorre a imagens conhecidas, e nada verifica se uma linha já é de outra pessoa. Leia e torne-a sua antes de planejar.

---

## Escrever uma música a partir de um prompt: todas as opções {#writing-a-song-from-a-prompt-every-option}

**+ Música** já tem muitas opções. Nenhuma é obrigatória: um estilo e um pouco de letra bastam, como em
[Sua primeira música](#your-first-song). Este capítulo passa por todas na ordem em que o editor as mostra,
nas três colunas (a música, a letra e o som), e depois pelo que fazer após o plano. Termina com uma
tabela dos desejos comuns, como uma música mais longa ou um refrão que soe diferente do verso.

### A música {#the-song}

- **Título.** Opcional. Em branco, a primeira linha da letra é usada.
- **Estilo.** A lista **Escolher um estilo…** tem 200 pontos de partida, do afrobeats ao zydeco, em ordem alfabética.
  Escolher um preenche a caixa Estilo com uma descrição completa, que você pode editar depois. Os chips abaixo são dez
  começos rápidos para uma música: warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B e dance pop. Veja [O que pôr na caixa Estilo](#what-to-put-in-the-style-box).
- **Salvar um estilo seu.** **Salvar**, ao lado da lista, salva o que está na caixa Estilo com um nome que você
  der. A primeira entrada da lista, **Estilos salvos**, abre os que você salvou; a lixeira ao lado de um o exclui, e a
  busca da lista os encontra junto com os 200. Salvar com um nome já usado substitui aquele estilo. A palavra-gatilho de um
  LoRA de estilo não é salva, e é posta de novo para o LoRA escolhido quando você usa o estilo.
- **Um andamento no estilo é só uma dica.** O planejador costuma escolher o dele. Para fixar o andamento, use **Fixar andamento** em
  Avançado.
- **Vocal.** Os chips escrevem uma voz (feminina, masculina, dueto e um caráter) no estilo por você.
- **LoRA de estilo.** Na parte de baixo da coluna do som. Veja [LoRAs de estilo](#style-loras).

### A letra {#the-words}

**A estrutura.** Acima da caixa da letra, enquanto ela não tiver palavras, há uma lista de seções: a ordem que
a música vai seguir. Cada linha pode ser trocada por outra seção, movida para cima ou para baixo (ou arrastada), ou removida, e os
chips sob a lista acrescentam uma seção. As seções são intro, verso, pré-refrão, refrão, ponte, interlúdio e outro.
Um **interlúdio** é uma passagem instrumental: não tem palavras, e o planejador o toca com a voz instrumental.
(`solo` não é uma seção que o planejador conheça; o interlúdio é a forma de pedir um.)

**Começar de…** preenche a lista com uma forma comum. Passe o mouse sobre uma opção para ver a que ela se adapta:

| Forma | Seções | Combina com |
|---|---|---|
| Verso, refrão, ponte | verso, refrão, verso, refrão, ponte, refrão | a canção clássica: pop, rock, country |
| Curta | verso, refrão, verso, refrão | folk, punk, primeiro rock and roll |
| Intro e outro | intro, verso, refrão, verso, refrão, outro | baladas, soft rock, cantautores |
| História | verso, verso, refrão, verso, refrão, outro | músicas narrativas, folk, country |
| Pop com pré-refrão | verso, pré-refrão, refrão, verso, pré-refrão, refrão, ponte, refrão | pop moderno, dance-pop, pop rock |
| Gancho primeiro | refrão, verso, refrão, verso, refrão, ponte, refrão | pop da era do streaming, indie pop |
| Curta e simples | verso, refrão, verso, refrão, refrão | punk, garage rock, rockabilly |
| Hip-hop | intro, verso, refrão, verso, refrão, verso, outro | rap, hip-hop, trap, R&B |
| Ponte dupla | verso, refrão, verso, refrão, ponte, ponte, refrão, refrão | power ballads, rock progressivo e sinfônico |
| Interlúdio | verso, refrão, interlúdio, verso, refrão, ponte, refrão | rock, pop rock, indie |
| Todas as partes | intro, verso, pré-refrão, refrão, interlúdio, verso, pré-refrão, refrão, outro | pop, dance-pop |

**Quantas seções.** O planejador costuma escrever de 8 a 10 seções seja o que for que a letra peça, então uma lista com mais
de 10 é condensada e as palavras das seções que ele descarta não são cantadas. O montador avisa quando a lista está
tão longa. Uma música não fica mais longa com mais seções; cada uma simplesmente fica mais curta. Veja
[Deixar a música mais longa](#making-the-song-longer).

**Colocar seções na caixa da letra** insere as seções como tags vazias, prontas para escrever embaixo à mão. Assim que a caixa tem
palavras, a letra é cantada, e o montador sai do caminho.

**Escrever letra.** Descreva sobre o que é a música e um modelo escreve palavras para as seções que você montou. Ele pede
três coisas:

- **Linhas por verso ou refrão** (4, 6 ou 8; 6 por padrão). Mais linhas em uma seção dão uma música mais longa,
  porque o planejador escreve mais ou menos tanta música quanto há palavras. Uma intro, uma ponte ou um outro ficam em 2 a 4 linhas,
  e um interlúdio não tem nenhuma.
- **Como as linhas soam.** A lista mostra as sílabas que cada linha busca. O autor antigo produzia quase sempre as mesmas
  linhas rimadas de oito sílabas, e isto muda isso:

| Opção | Busca | O que você recebe |
|---|---|---|
| Natural (padrão) | 3-13 sílabas | Uma mistura de linhas curtas e longas, algumas rimas, sem pulsação fixa |
| Rima regular | 6-10 sílabas | Linhas iguais que rimam de duas em duas: a forma tradicional, e o que o autor fazia antes |
| Ritmo falado | 5-14 sílabas | Coloquial e rítmico, como a fala ou o rap, com rimas internas |
| Rima solta | 4-13 sílabas | Algumas rimas, algumas toantes, algumas nenhuma, e linhas de tamanhos variados |
| Curto e direto | 3-6 sílabas | Linhas curtas e frases repetidas |
| Longo e fluido | 10-14 sílabas | Linhas longas que fluem como um pensamento |

  A última opção é lembrada. São metas, não garantias: um modelo de linguagem as segue de perto nos
  extremos (curto e direto, longo e fluido) e com mais folga nos meios-termos.
- **O pedido** em si, com suas próprias palavras, e o estilo acima, que dá o clima. O pedido é salvo com o take,
  então abrir um take e clicar em **Escrever letra** mostra sobre o que se pediu que fosse, pronto para mudar e escrever de novo.

O rascunho chega à caixa da letra, e a janela se fecha assim que ele começa. É um primeiro rascunho: leia e torne-o
seu.

**Seguir esta estrutura exatamente** (a caixa de seleção sob a caixa da letra, desligada por padrão). O planejador toma as tags
de seção da letra como orientação, e por conta própria escreve sua própria forma: muitas vezes acrescenta uma intro e um outro,
troca uma ponte por um interlúdio e um verso, ou condensa uma lista longa. Com isto ligado, o plano escreve exatamente as
seções que a letra nomeia, nessa ordem, e nenhuma outra. Ele não pode acrescentar uma intro ou um outro que você não
tenha posto. O planejador continua decidindo como é a música e quando cada seção começa. Só se aplica a músicas.

**Quem canta cada linha: indicações de voz.** Uma linha sozinha entre colchetes que nomeia uma voz diz quem canta as
linhas seguintes, até a próxima indicação ou a próxima seção:

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

Escreva uma indicação como `[male voice]`, `[female voice]` ou `[both voices]`, cada uma numa linha própria entre colchetes.

- O editor de letras ampliado tem os botões **+ Homem**, **+ Mulher** e **+ Ambos** no cabeçalho para inseri-las no cursor.
- Essas são as formas com que o recurso foi testado, junto com `vocal` no lugar de `voice` (`[female vocal]`) e `[male and female voices]` para ambos.
- Você pode acrescentar palavras suas depois de uma vírgula, como em `[female voice, soft and close]`; elas não mudam quem canta.
- Uma seção sem indicação fica a cargo do planejador.
- Outras grafias também são lidas, para que letras escritas em outro lugar não sejam ignoradas: `[man]`, `[woman]`, `[duet]`, uma indicação dentro da tag de uma seção como `[Verse 2 - female vocal]`, e uma indicação entre parênteses, `(female voice)`. Colchetes são o hábito mais seguro: palavras entre parênteses costumam ser backing vocals, e podem ser cantadas.

**Uma indicação sozinha não decide a voz.** Quem canta depende sobretudo de quão aguda a melodia está escrita: a mesma linha uma oitava acima é cantada por uma mulher, e o planejador gosta de escrever um verso em duas oitavas, mudando a cada quatro linhas mais ou menos, seja quem for o indicado.

- **As vozes seguem as indicações** (uma caixa de seleção sob a caixa da letra, visível assim que a letra tem uma indicação; ligada num take novo) mantém as indicações: quando o plano é escrito, cada trecho indicado da melodia é movido por oitavas inteiras para onde aquela voz canta, grave para um homem e agudo para uma mulher. Nada mais muda no plano.
- Isso é refeito antes de cada renderização, então acompanha uma mudança na letra ou na partitura.
- Na página Partitura, **Vozes pelas indicações** faz o mesmo uma vez na partitura da caixa, para um take feito sem a caixa marcada; salve a partitura e renderize.

Três coisas a saber:

- **Quem canta uma linha ainda é em parte sorte.** Com a melodia no lugar, a maioria das linhas vai para a voz
  indicada, mas um render ainda pode dar uma para a outra voz. Renderize de novo com outra seed, ou use
  **Tentar mais**.
- **Ambas** põe a linha onde uma mulher canta e deixa a segunda voz para o render, que muitas vezes põe uma
  em um refrão. Pede um dueto mais do que o cria: quanto você ouve da segunda voz varia de um
  render para outro. Ainda não há como escrever dois cantores em uma linha sem que a letra sofra.
- Um take feito antes de esta caixa existir mantém a partitura como está; marque-a, ou use **Vozes pelas indicações**, para ajustá-la.

**Escrever à mão.** O botão Expandir abre um editor em tamanho cheio com botões para intro, verso, pré-refrão,
refrão, ponte, interlúdio, outro e instrumental. Uma seção é uma linha como `[Verse]` seguida das linhas dela; uma
tag sem linhas embaixo, como `[Interlude]`, é uma passagem instrumental.

### O som {#the-sound}

- **Harmonia** (o controle deslizante): o quão ousados são os acordes. Uma música nova começa em **Variada**, com a interpretação
  em **Ampla**: nos nossos próprios testes esse par deu as versões musicalmente mais interessantes, então é um bom ponto de partida. Mova
  qualquer um dos dois como quiser. Takes existentes mantêm aquilo com que foram feitos. Por conta própria, o planejador tende a escrever um loop de
  quatro acordes e usá-lo em todas as seções, e cada nível o afasta um pouco mais disso. Os níveis se somam uns
  aos outros:

  | Nível | O que faz com os acordes | Escolha quando |
  |---|---|---|
  | Familiar | Nada: os acordes do YuE2, muitas vezes um único loop para a música toda | Você gosta da primeira ideia do planejador, ou quer o acompanhamento mais simples |
  | Variada | Desestimula repetir exatamente os acordes que acabou de usar, então os recolore (um F, depois um Fmaj7) mas fica no tom | O loop soa igual demais e você quer que a música continue convencional |
  | Colorida | O mesmo, com mais força: verso e refrão se separam, com acordes mais ricos. Uma seção também não pode começar com os mesmos acordes da anterior, então um refrão não começa mais como o verso | Você quer que o refrão seja um impulso, não uma repetição. Um bom primeiro passo |
  | Aventureira | Desestimula as *fundamentais* usadas há pouco, não só as grafias, então a harmonia precisa viajar, e pega acordes emprestados de fora do tom | Você quer movimento e surpresa, e vai ficar atento a um acorde que soe estranho |
  | Fora do tom | Ousada, com uma atração por acordes fora do tom | Experimentos. Conte com descartar alguns planos |

  A partir de Colorida, as escolhas de acordes saem mais diferentes de uma seção para outra: mais acordes diferentes em uma
  música, mais padrões de quatro compassos que não se repetem, e menos refrões que copiam o começo do verso. O plano continua
  sendo uma música normal, então vale a pena tentar um ou dois níveis acima antes de recorrer a uma Variedade do plano mais solta.
  Em **Avançado**, **As seções começam diferente** pode ser posto em *Sempre* ou *Nunca* para testar um plano com e sem
  a regra do refrão; o padrão, *Seguir a harmonia*, fica ativo a partir de Colorida. Um estilo como trap ou ambient costuma
  ser baseado em loops por natureza, então espere uma mudança menor do que em pop ou rock. Veja [Harmonia](#harmony) para as medições.
- **Variedade do plano.** Com que liberdade o planejador escreve todo o resto. Veja [Variedade do plano](#plan-variety).
- **Interpretação.** Como as notas são tocadas no render. Veja [Interpretação](#interpretation).
- **Limite de duração.** O mais tarde que a música pode terminar. Veja [Duração](#length).
- **Modo.** *Completo* mantém os acordes do plano; *melodia* deixa o acompanhamento livre. *Sem partitura*, para músicas, não escreve
  plano nenhum: veja [Uma música sem partitura](#a-song-with-no-score).
- **Seed**, e **manter esta seed**. Veja [A seed, e reproduzir um take](#seed-and-reproducing-a-take).
- **Acabamento de produção** e **Normalizar o volume.** Veja [Acabamento de produção](#production-polish).
- **Renderizar assim que o plano estiver pronto**, ao lado do botão no pé da janela, faz o plano e o render
  sem parar no meio. Vem marcado de início, e o editor lembra sua escolha. Desmarque para ler o
  plano primeiro.
- **Avançado** (o botão do cabeçalho): passos de difusão, Seguir o estilo, Evitar, Fixar tom, Fixar andamento, a partitura mais longa,
  limite de permanência em um acorde, bônus de harmonia externa, Seções que começam diferente, loudness alvo e o fade final. Veja
  [Ajustes avançados](#advanced-settings).
- **Masterização** (o botão à esquerda dele, quando o take tem som) abre o rack de masterização sobre o editor para o take nele. O botão fica verde enquanto o rack muda como o take soa. Os módulos do rack, em ordem:

  1. Um EQ estilo 1073
  2. Um equalizador paramétrico
  3. Um compressor
  4. Um alargador estéreo
  5. **Espaço 3D** (abaixo)
  6. Um limitador

  Cada módulo se recolhe à sua barra com a seta à esquerda, e o take lembra quais estão recolhidos.

  **O equalizador paramétrico.** Cada uma das sete bandas é um ponto no gráfico:

  - Arraste um ponto na horizontal para a frequência, e para cima ou para baixo para o ganho.
  - Gire a roda sobre ele para a largura; clique duas vezes para devolvê-lo ao lugar.
  - A faixa sob o gráfico define o tipo da banda escolhida (corte de graves, prateleira de graves, sino, notch, prateleira de agudos, corte de agudos) e a liga ou desliga.
  - **Plano** volta todas as bandas a 0 dB, e o botão no canto do gráfico muda quantos decibéis ele mostra.

  **Teclas.** Com o rack aberto, a barra de espaço toca e pausa o take, e as setas se movem nele e ajustam o volume, como na página principal. Esc fecha o rack, e de novo fecha o editor.

- **Espaço 3D**, um módulo do rack entre o alargador e o limitador, posiciona o take ao seu redor para fones, de um de dois jeitos:

  | A partir de | O que você ajusta |
  |---|---|
  | **Mix** | Dois alto-falantes virtuais na frente (**Largura**) e dois atrás (**Traseiro**), com **Surround** definindo quanto da largura e da ambiência do mix toca pelos de trás; arraste também os alto-falantes no círculo. **Altura** eleva todos e **Sala** acrescenta uma sala curta. |
  | **Stems** | Cada stem do take é posicionado sozinho: escolha um sob o círculo, depois arraste em volta do círculo para posicioná-lo, e a roda o espalha. **Criar stems** abre a janela Stems quando o take não tem. |

  **Frente**, **Ampla** e **Em volta** ajustam tudo de uma vez. O que você ouve é para fones e nunca faz parte do arquivo do take. Para guardar:

  - **Baixar**, em Fones, salva como WAV.
  - **FLAC** e **AC-3**, em Alto-falantes 5.1, salvam o take para alto-falantes surround (a partir dos stems, cada um vai para os alto-falantes dos dois lados de onde está posicionado).
  - A janela Salvar do take oferece os mesmos downloads enquanto o Espaço dele está ativo.

### Deixar a música mais longa {#making-the-song-longer}

A duração de uma música é definida pelo plano, e o render segue a duração do plano. Isto é o que a move:

| Para conseguir… | Faça isto |
|---|---|
| Uma música mais longa | Dê mais linhas a cada seção (**Linhas por verso ou refrão**: 6 ou 8) |
| Uma música mais lenta e mais longa | Ponha um **Fixar andamento** em Avançado. O mesmo plano com menos BPM dura mais |
| Uma música mais longa acrescentando seções | Não funciona: um plano tem cerca de 8 a 10 seções, então mais só ficam mais curtas ou são condensadas |
| Mais do que o plano permite | Escreva um plano novo; as durações variam muito entre execuções com a mesma letra |
| Uma música que termine no fim da letra | Aumente o limite de duração só se ela for cortada; o limite é um teto, não uma meta |

### Depois do plano {#after-the-plan}

- **Renderizar esta partitura** cria um take novo sempre que o take aberto já tem áudio, então um render nunca sobrescreve um
  que você queira comparar. Um take que ainda não tem áudio é completado.
- **Manter esta melodia** (depois de mudar a letra de um take): canta a partitura do take com a letra nova, como take novo. A
  melodia não pode ganhar seções nem notas, então se sua letra tiver mais seções que a melodia, ou muito mais ou muito menos
  sílabas do que ela tem notas (linhas longas em uma melodia feita para curtas, ou curtas em uma feita para longas), a
  caixa se desmarca sozinha e um plano novo é escrito, com uma linha dizendo por quê. Veja [Mesma melodia, letra nova](#same-tune-new-words).
- **Filtrar a biblioteca.** Os botões **Música**, **Cover** e **Instrumental** ao lado dos filtros mostram só esses
  tipos no espaço aberto; escolha mais de um, ou nenhum para todos os tipos.

---

## Ler e corrigir o plano {#reading-and-fixing-the-plan}

O plano é escrito em **notação ABC**: música como texto puro, letras no lugar de pontos em uma pauta.
Chris Walshaw a criou no começo dos anos noventa para mandar melodias folk por e-mail, e ela pegou.

Você não precisa lê-la. O app mostra o mesmo plano como **cifra** e como **notação
em pauta** de verdade sob o editor, e **Expandir** abre tudo em tamanho cheio. Mas o texto é o que o YuE2
escreveu e a partir do que renderiza, então vale a pena saber se orientar nele.

### Ler um plano {#reading-a-plan}

Um plano começa com um cabeçalho, uma letra e dois-pontos por linha:

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Linha | Significa |
|---|---|
| `X:1` | o número da melodia. Todo arquivo ABC começa com um |
| `M:4/4` | a fórmula de compasso — quatro tempos por compasso |
| `L:1/32` | a duração unitária: uma letra sozinha dura uma fusa |
| `Q:1/4=120` | o andamento — uma semínima a 120 batidas por minuto |
| `V:` | declara uma voz. O YuE2 escreve duas, uma linha vocal e uma instrumental |
| `K:D#m` | o tom, ré sustenido menor. `K:` sempre vem no fim do cabeçalho |

Depois, a música em si:

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **As notas são letras.** `d16` é um ré que dura 16 unidades. As minúsculas soam uma oitava acima das maiúsculas,
  e `'` ou `,` as deslocam mais.
- **`-` liga** uma nota à seguinte, para que soem como uma só.
- **`z` é uma pausa**, com uma duração como uma nota. Um `Z` maiúsculo é uma pausa de compasso inteiro.
- **Os acordes ficam entre aspas duplas**, como `"D#m"`, e vêm antes da nota em que começam. É isto
  que **localizar e substituir** edita.
- **`|` é uma barra de compasso**, e **`%` abre um comentário** — é assim que as seções são marcadas:
  `% intro`, `% verse`, `% chorus`.

Então esse trecho diz: ré sustenido menor, quatro por quatro, 120 batidas por minuto, e durante a intro a
voz fica calada carregando o acorde, enquanto o instrumento toca um ré e um lá ligados, e depois sol e lá.

Duas consequências práticas. **Editar os acordes é seguro** mesmo que as notas pareçam opacas — são só
as partes entre aspas, e todo o resto pode ficar como está. E **se você editar o plano, o render
usa o que você editou**, então consertar um costuma ser mais rápido do que jogar de novo até sair um bom.

### Ouvir o plano {#hearing-it}

A aba **Notação** tem um player acima das pautas. Clique em **Tocar** para ouvir o plano como está na
caixa, com edições e tudo, para julgar de ouvido uma melodia de que você duvida antes de gastar um render
com ela. As notas tocadas são destacadas ao longo da reprodução, e o controle de andamento dele muda só a prévia,
não a partitura. Tocá-lo para o que estiver na barra do player, porque duas coisas ao mesmo tempo não
servem a ninguém, e fechar a janela — ou passar para Cifra ou Letra — também o para, para que nada fique
tocando sem um controle à mão.

**Instrumentos** toca cada voz com um instrumento que o estilo nomeia, em vez de um piano o tempo todo:

- Um estilo que diz *electric guitar, drums* é ouvido com uma guitarra, os acordes tocados por outra, e um baixo embaixo. Uma linha cantada é substituída por uma voz, e a melodia de um instrumental não.
- Um estilo que nomeia bateria ganha também uma parte de bateria, escrita sobre o compasso da própria partitura — um backbeat para o rock, o quatro por quatro para música de pista, um ride para o jazz, algo mais esparso para uma balada — e ela toca do começo ao fim, já que a partitura não tem seções em que possa ficar quieta.
- A linha ao lado do player diz o que foi escolhido, e desmarcar volta ao piano que você ouviria de outro jeito.

É uma leitura do estilo, não da renderização: o YuE2 decide a interpretação real e acrescenta partes que a partitura nunca teve, então trate isso como o plano tocado nas cores certas e não como o som que o take terá.

**Baixar MIDI** salva a partitura para uma DAW:

- Cada parte é uma faixa própria, no próprio canal, com o instrumento que a prévia usou definido nesse canal: a linha vocal, a linha instrumental e, a menos que você desmarque **Acordes**, as cifras como uma parte de acordes com o baixo ao lado (o único lugar onde a harmonia é escrita como notas), e bateria no canal 10 quando o estilo pede.
- Os instrumentos são números de programa General MIDI, então sua DAW os toca com os próprios sons, e o tempo e o compasso estão no arquivo.
- Um plano que muda de compasso no meio é escrito no compasso em que começa — só esse fica registrado — enquanto as notas mantêm as próprias durações.

Clicar numa nota da pauta põe o cursor no ABC que a escreveu.

**Fora da extensão.** Uma partitura com uma nota acima ou abaixo do que esses instrumentos tocam é tocada deslocada por oitavas inteiras até caber, e a linha ao lado do player diz quanto; a pauta, o arquivo MIDI e a própria partitura não mudam. Os instrumentos não têm todos o mesmo tamanho — um baixo vai bem mais grave que um piano —, por isso a linha aparece quando uma partitura é deslocada. Uma partitura sem notas não tem o que tocar e diz isso.

**Os sons.** O player precisa das amostras de notas, que não fazem parte do app: cada instrumento tem uns 7 MB, é buscado na origem na primeira vez que uma prévia o usa e guardado na biblioteca, então depois funciona offline. **Tocar** busca o que a partitura atual precisa e então começa, e **Buscar os sons** busca o mesmo sem tocar, para quem prefere deixar pronto antes.

### O piano roll {#the-piano-roll}

Clique em **Piano roll** na janela da partitura para abrir o editor MIDI visual. Em vez de editar letras ABC brutas, você vê e molda a melodia diretamente em uma grade interativa de altura e tempo.

O editor mostra as duas vozes da partitura ao mesmo tempo — **Vocal** (a melodia cantada principal em azul-celeste) e **Ins** (o acompanhamento instrumental em âmbar quente). As duas vozes estão sempre totalmente ativas, visíveis, selecionáveis e editáveis. Os botões **Desenhar** no canto superior esquerdo escolhem a que voz as notas novas são atribuídas quando você clica para adicioná-las.

#### Editar notas {#editing-notes}

- **Adicionar uma nota:** clique em uma célula vazia da grade para criar uma nota nessa altura e nesse momento. A nota toca na hora para você ouvir o tom.
- **Selecionar notas:** clique em uma nota para selecioná-la. Segure <kbd>Shift</kbd> ou <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> ao clicar para selecionar várias notas nas partes vocal e instrumental. Clique e arraste uma **caixa de seleção** sobre uma área vazia para selecionar uma frase ou passagem em todas as vozes. Pressione <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> no macOS) ou clique em **Selecionar tudo** para selecionar todas as notas da partitura. Para selecionar todas as notas do cursor de reprodução até o fim da música, pressione <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> ou <kbd>Alt</kbd>+<kbd>A</kbd> (ou clique em **Do cursor ▶** na barra de ferramentas).
- **Mover notas:** arraste uma nota selecionada para adiantá-la ou atrasá-la, ou na vertical para transpor a altura. Quando várias notas estão selecionadas — vocais, instrumentais ou de ambas — elas se movem juntas, mantendo o tempo relativo, as melodias e a letra.
- **Duração:** arraste a borda direita de uma nota para alongá-la ou encurtá-la. O seletor **Ajuste** (1/16, 1/8 ou 1/4 de nota) prende os movimentos e redimensionamentos a divisões musicais limpas.
- **Excluir notas:** clique duas vezes em uma nota para excluí-la, ou selecione uma ou várias e pressione <kbd>Delete</kbd> ou <kbd>Backspace</kbd>.
- **Desfazer e refazer:** cada edição, movimento, redimensionamento, adição e exclusão de uma nota fica no histórico. Pressione <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) para desfazer, e <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> ou <kbd>Ctrl</kbd>+<kbd>Y</kbd> para refazer.
- **Ouvir teclas:** clique em uma tecla do teclado de piano à esquerda para ouvir a altura dela.
- **Maximizar:** clique em **Maximizar** na barra de cima para estender o piano roll por toda a largura da janela do navegador.

#### Linha do tempo, seções e acordes {#timeline-sections-and-chords}

Ao longo da régua de cima, a linha do tempo mostra os números de compasso e os limites das seções:
- **Renomear seções:** clique em um marcador de seção (`intro`, `verse`, `chorus` etc.) para editar o nome ou reatribuí-la.
- **Editar acordes:** logo abaixo da régua de compassos, a faixa de acordes mostra a progressão harmônica da música. Clique em um acorde existente para renomeá-lo (por exemplo, trocar `C` por `Am7` ou `G/B`), ou em um compasso vazio para pôr um acorde novo.
- **Harmonizar compassos vazios (Preencher lacunas):** clique em **Preencher lacunas** na barra de ferramentas para preencher os compassos vazios do acompanhamento instrumental com notas geradas a partir da progressão de acordes.
- **Remover compassos vazios (Compactar lacunas):** clique em **Compactar lacunas** para remover os compassos vazios e silenciosos nas duas vozes, deslocando para a esquerda as notas e acordes seguintes para eliminar buracos indesejados no arranjo.

#### Letra e acompanhamento karaokê {#lyrics-and-karaoke-tracking}

Na parte de baixo do piano roll, uma faixa de letra própria alinha cada sílaba com a melodia vocal:
- **Ajuste por frases:** clique em **Associar letra** para distribuir a letra sobre a melodia vocal. O alinhamento detecta as respirações naturais e as pausas entre frases melódicas, e atribui cada linha de letra à sua frase sem derramar palavras por cima das pausas nos compassos seguintes. Palavras de várias sílabas são divididas de forma limpa entre notas.
- **Editar sílabas:** clique em um rótulo de letra (ou selecione uma nota vocal e pressione <kbd>L</kbd>) para editar o texto. Se você digitar sílabas separadas por espaços ou hifens (por exemplo `Hel- lo world`), elas são distribuídas automaticamente pelas notas vocais consecutivas.
- **Destaque ao passar o mouse:** passar o mouse sobre um rótulo de letra destaca a nota correspondente na grade, e passá-lo sobre uma nota vocal destaca o rótulo dela embaixo.
- **Bolinha de karaokê:** durante a reprodução, uma bolinha animada pula sobre cada nota enquanto é cantada, e a sílaba ativa e a nota da grade acendem em tempo real.

#### Reprodução e acompanhamento harmônico {#playback-and-harmony-accompaniment}

Pressione <kbd>Space</kbd> ou clique em **▶ Tocar** para começar a tocar do cursor. A linha de reprodução percorre a grade, atualizando o compasso, o tempo e o contador de tempo decorrido.

- **Clique audível (metrônomo):** a reprodução inclui por padrão um clique audível, com uma batida de woodblock acentuada no primeiro tempo de cada compasso e cliques mais suaves nos demais. Pressione <kbd>C</kbd> ou <kbd>M</kbd> (ou clique em **Clique** na barra de transporte) para ligar ou desligar o metrônomo a qualquer momento.
- **Acompanhamento harmônico de acordes:** a reprodução sintetiza pads de acordes polifônicos quentes diretamente da progressão de acordes da partitura. Mesmo quando as faixas vocal ou instrumental estão em silêncio, o espaço harmônico continua musical e quente em vez de cair num silêncio morto. Pressione <kbd>H</kbd> (ou clique em **Acordes** na barra de transporte) para ligar ou desligar o acompanhamento de acordes.
- **Navegar por compassos:** pressione <kbd>Seta para a esquerda</kbd> e <kbd>Seta para a direita</kbd> para voltar e avançar compasso a compasso, ou <kbd>Home</kbd> para voltar direto ao começo.

#### Atalhos de teclado {#keyboard-shortcuts}

| Tecla | Ação |
|---|---|
| <kbd>Space</kbd> | Tocar / pausar |
| <kbd>Seta para a esquerda</kbd> | Voltar um compasso |
| <kbd>Seta para a direita</kbd> | Avançar um compasso |
| <kbd>Home</kbd> | Voltar ao começo (compasso 1) |
| <kbd>C</kbd> ou <kbd>M</kbd> | Ligar / desligar o clique audível (metrônomo) |
| <kbd>H</kbd> | Ligar / desligar o acompanhamento de acordes |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Excluir as notas selecionadas |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Desfazer a última edição |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Refazer |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Selecionar todas as notas das duas vozes |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Selecionar todas as notas do cursor ao fim nas duas vozes |
| <kbd>+</kbd> ou <kbd>=</kbd> | Aumentar a escala horizontal |
| <kbd>-</kbd> ou <kbd>_</kbd> | Diminuir a escala horizontal |
| <kbd>0</kbd> | Rolar até as notas (ajustar a vista) |
| <kbd>L</kbd> | Editar a letra da nota vocal selecionada |
| <kbd>Escape</kbd> | Limpar a seleção, ou fechar a janela da partitura |

### Harmonia {#harmony}

Por conta própria, o YuE2 tende a escrever um loop de quatro acordes e ficar nele. O controle **Harmonia** o afasta
dos acordes que acabou de usar, sem quebrar a estrutura da música.

| Nível | O que você recebe |
|---|---|
| Familiar | Os acordes do YuE2. Muitas vezes um único loop para a música toda |
| Variada | Evita repetir os mesmos acordes. Fica no tom |
| Colorida | Verso e refrão recebem progressões diferentes, com acordes mais ricos. Uma seção não pode começar como a anterior |
| Aventureira | Mantém a harmonia em movimento e pega acordes emprestados de fora do tom |
| Fora do tom | Ousada, e se afasta mais do tom |

**Escrever um plano novo** usa a posição atual do controle, então você pode jogar de novo com a mesma letra e acordes mais
ousados e comparar.

Isto foi medido em vez de suposto — uma única letra, dois estilos, três seeds cada:

| | Familiar | Variada | Colorida | Aventureira | Fora do tom |
|---|---|---|---|---|---|
| Acordes diferentes em uma música | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Compassos com um acorde de fora do tom | 0% | 0% | 0% | 13% | 24% |
| Padrões de quatro compassos que não se repetem | 29% | 38% | 50% | 63% | 64% |

Cada plano, em cada nível, manteve as seções e acordes válidos. Pedir uma harmonia ousada no
texto do estilo em vez disso — “jazz harmony”, “borrowed chords” — não teve nenhum efeito mensurável.

### Variedade do plano {#plan-variety}

Em *Avançado*, **Variedade do plano** define com que liberdade o planejador escreve. Onde a Harmonia age sobre os
acordes, isto age sobre tudo: melodia, estrutura e duração.

- **Tranquila:** a mais estável. Poucos acordes, e uma melodia que não se afasta.
- **Normal:** o padrão.
- **Animada:** alguns acordes e voltas a mais.
- **Ousada:** uma harmonia mais rica, cerca de três vezes o vocabulário de acordes normal, enquanto a melodia continua
  reconhecivelmente do mesmo tipo.
- **Peculiar:** inquieta. Os acordes não param de mudar, e a melodia salta entre registros de uma
  seção para a outra. Para músicas estranhas e excêntricas.
- **Selvagem:** a mais inquieta de todas, e pode mudar de tom no meio.

### Uma música sem partitura {#a-song-with-no-score}

**Sem partitura**, a terceira opção de **Modo**, canta a letra sem plano nenhum: o YuE2 escreve a melodia e
os acordes enquanto canta, como o YuE original fazia, e a música é renderizada na hora com **Cantar sem partitura**.
Muitas vezes soa bem diferente de uma música planejada.

O que orienta um plano não tem aqui sobre o que agir, então **Harmonia**, **Variedade do plano**, **Manter esta melodia** e **Seguir esta estrutura exatamente**
ficam esmaecidos enquanto ela está escolhida, e não há partitura para ler nem editar. O YuE2 decide
a duração, até o limite. Fixar tom e Fixar andamento só chegam a ele como palavras no estilo. Cantar de novo,
Variações, Tentar mais e a letra nova funcionam todos, cada um cantado de novo sem partitura. **Escrever um plano novo** dá ao take uma
partitura, e Modo volta a *completo*. É só para músicas a partir de um prompt: um cover é a partitura da gravação dele, e um
instrumental precisa de uma para manter a voz de fora. Os dois motores conseguem fazer isso.

---

## Renderizar {#rendering}

### Interpretação {#interpretation}

A partitura define as notas. A **interpretação** define como são tocadas.

| Interpretação | O que você ouve |
|---|---|
| Padrão | A leitura habitual do YuE2 |
| Precisa | mais controlada e polida |
| Solta | mais crua e espontânea |
| Assentada | livre para repetir uma figura e ficar num groove |
| Inquieta | mantém as partes em movimento, evita se repetir |
| Ampla | busca sons menos óbvios |

### Variações {#variations}

O botão de brilho de um cartão renderiza **a mesma partitura e a mesma seed** nas outras
interpretações. Como só a interpretação muda, o que você ouve entre elas é a
interpretação — não outra jogada de dados. Cada uma é um take próprio, intitulado
*Night drive · Loose* e guardado dentro do take de onde veio (veja **Takes dentro de um take**,
em A biblioteca). A janela tem o próprio limite de duração, que parte do do editor e só se aplica
a estes takes.

### Tentar mais {#try-more}

O botão de dado de um cartão renderiza **a mesma partitura e a mesma letra de novo como vários takes novos**, para
ouvir juntos. Variações só muda a interpretação e mantém a seed; isto muda a
jogada:

- **Seeds novas:** uma seed nova para cada um, todo o resto igual.
- **Intensidades do Planejador:** para um take com um LoRA de estilo que tem metade de planejador, a mesma seed com
  outras forças de Planejador (a dele é deixada de fora). O planejador muda a interpretação em si, não só
  a voz, então funciona como outra seed.

Os takes novos são intitulados *Night drive · try 1* ou *Night drive · planner 0.60* e guardados dentro
do take de onde vieram, cujo painel se abre para mostrá-los à medida que terminam. Para ouvi-los uns contra
os outros, clique em **Selecionar tudo** enquanto o painel está aberto e depois em **Comparar**. A janela tem o
próprio limite de duração, que parte do do take.

### A seed, e reproduzir um take {#seed-and-reproducing-a-take}

Cada take registra a seed e cada ajuste que lhe deu forma. O cartão os nomeia, clicar em um cartão
os mostra no painel do take, e abri-lo no editor carrega tudo de novo. **De novo** abre o
editor com exatamente isso, seed incluída, para reproduzir um take de que você gostou, e mudar um ajuste por vez em um de que você quase
gostou.

Nos menus do editor, passar o mouse sobre uma interpretação mostra o que ela faz.

Marque **manter esta seed** para manter a mesma seed entre renders; desmarcada, cada render sorteia uma
nova.

Um render usa o que o editor mostra: o estilo, o LoRA de estilo e as forças dele, o limite de duração, o modo,
a interpretação e a seed, mesmo ao renderizar de novo a própria partitura de um take.

### Mesma melodia, letra nova {#same-tune-new-words}

O planejador lê a letra inteira antes de escrever uma nota, então a mesma seed dá o mesmo plano só
com a mesma letra. Mude uma linha e o próximo plano é uma melodia nova: outra melodia, muitas vezes outro
tom e outro andamento, e a voz muda junto.

Para manter uma melodia de que você gosta:

1. Abra o take e mude a letra. **Manter esta melodia** aparece marcado sob a letra, e o botão principal vira **Cantar com a letra nova**.
2. Mude antes tudo o mais que quiser: o estilo, o LoRA e as intensidades, o limite de duração, a interpretação. Mantenha a semente marcada para a voz ficar o mais parecida possível.
3. Pressione **Cantar com a letra nova**. A partitura do take é cantada com a letra nova, como um take novo ao lado do original, que fica como está.

Desmarque **Manter esta melodia** para escrever no lugar um plano novo, e uma melodia nova, para a letra.

Uma letra nova que mantém o número de sílabas das linhas antigas encaixa melhor na melodia. Quando não encaixa, **Manter esta melodia** se desmarca sozinho com uma linha dizendo por quê, e um plano novo é escrito para a letra. Marque de novo para cantar a melodia mesmo assim. A letra não encaixa quando há:

- **Mais seções, ou muito mais sílabas do que a melodia tem notas:** linhas longas numa melodia feita para curtas saem repetidas ou cortadas.
- **Muito menos sílabas:** linhas curtas numa melodia feita para longas deixam notas sobrando, que quem canta preenche com palavras próprias.

### Acabamento de produção {#production-polish}

**Acabamento de produção** aplica o LoRA de decodificador Realaudio, de Mothersuperior. O YuE2 puro costuma soar abafado
nos médios; isto separa com mais limpeza instrumentos e vozes. Ligado por padrão.

### Duração {#length}

O limite de duração é um teto rígido, não uma meta. O YuE2 decide quando uma música termina, e ela costuma terminar
sozinha; o limite para a que não termina. Ele começa em 360 segundos, ou no que **Limite de duração de um take novo**
disser em Configurações. Depois abre espaço para a música, para que uma música longa não seja cortada:

- Uma **música ou instrumental a partir de um prompt** tem o limite aumentado quando o plano é escrito, se o plano
  for mais longo: para a duração do plano com cerca de dez segundos de folga. Ele nunca é reduzido.
- Com uma **gravação** escolhida, para um cover ou um instrumental, o limite segue a partitura da gravação,
  arredondado para cima do mesmo jeito.

Um limite que você digita fica como você definiu, e a página Partitura então avisa quando um plano é mais longo.

Quando uma música não termina como deveria:

- **Um plano muito mais longo que o limite** (mais de um terço acima, e com mais de oito minutos) nem é tomado como música e é escrito de novo.
- **Uma renderização que continua além da partitura** até o limite tem os últimos segundos esmaecidos em vez de cortados, e o cartão dela diz que chegou ao limite.
- **Uma renderização que termina antes de começar a última seção da partitura** (mais rara ainda) é renderizada mais uma vez com uma semente nova antes de ser dada como pronta. Se essa também parar cedo, o cartão diz que ela parou antes da última seção: pressione **Renderizar** de novo para outra tentativa.

---

## Fazer um cover de uma gravação {#covering-a-recording}

1. Solte um arquivo de áudio, de até 2 GB. Ele é guardado uma vez e tem o hash calculado, então o mesmo arquivo nunca é
   guardado duas vezes. Um arquivo de vídeo (MP4, MOV, MKV, WebM e similares) também serve: só o som é mantido, como FLAC.
2. Clique em **Transcrever**. O SheetSage2 escreve a melodia e os acordes na caixa da partitura. Isso fica
   em cache por gravação, então fazer outro cover da mesma música pula essa etapa.
3. Corrija o que ele tiver ouvido errado.
4. Adicione uma letra, escolha um estilo, clique em **Criar cover**.

Um cover segue a melodia e os acordes do original enquanto o estilo decide todo o resto, que é
o que faz dele um cover e não uma cópia.

### Gravar uma melodia sua {#recording-a-tune-of-your-own}

> [!NOTE]
> O quanto uma melodia é bem detectada depende da gravação, e um plano construído em torno dela ainda pode falhar ou
> divagar: escreva um plano novo, ou grave a melodia de novo.

No modo **Cover**, **Gravar melodia** abre o gravador. Escolha o que você está gravando em **Entrada**:

- **Voz:** cante ou cantarole em um microfone. **Autotune** pode ajustar a gravação a um tom e uma escala; o
  botão de uma gravação alterna entre a versão afinada e a original para você ouvir o que ele fez.
- **Instrumento:** toque a melodia em um instrumento, por exemplo uma guitarra ligada a uma interface de áudio.
  Toque **nota por nota**: a linha que você toca vira a melodia que é cantada, e acordes
  dedilhados não dão melodia para cantar. Escolha a interface em **Dispositivo**, e em **Canal** o lado
  em que seu instrumento está ligado (a entrada 1 de uma interface costuma ser **Esquerda**). Aumente **Ganho de entrada**
  para um instrumento fraco, mantendo o medidor fora do CLIP. Não há autotune: um instrumento já
  está afinado. O Yeufonic lembra essas escolhas neste navegador.

O metrônomo, a contagem regressiva e o retorno pelo fone funcionam igual para os dois. **Usar como cover** salva a
gravação como gravação, marcada **MIC** ou **INST** na lista. Transcreva-a como qualquer gravação; uma
melodia gravada é transcrita só como melodia, porque acordes adivinhados a partir de uma melodia solta ficariam em
cada refrão de uma música feita com ela (uma gravação transcrita antes disso mantém os acordes até ser
transcrita de novo). De dez a trinta segundos de melodia são mais que suficientes.
**Extrair a letra** não é oferecido para uma gravação de instrumento, porque não há palavras para ouvir: use
**Escrever letra**.

**Você se ouve com atraso?** O navegador acrescenta um pequeno atraso entre o que você canta ou toca e o que
ouve no fone. Se sua interface de áudio tem monitoramento direto (sem latência), use-o
e desligue o **Retorno** do gravador, para se ouvir direto da interface, e uma vez
só. Use fones com fio: o Bluetooth acrescenta o próprio atraso.

#### Expandir para uma música completa {#expand-to-full-song}

Uma melodia gravada costuma ter só alguns compassos. **Desenvolver em música completa** faz o YuE2 planejar uma música inteira
com sua melodia dentro: o plano fica no tom, na fórmula de compasso e no andamento da sua melodia, cada refrão (ou cada verso,
se você escolher) contém sua melodia, e o resto da música é escrito em volta dela. Depois ela é renderizada
como um cover da sua gravação.

- **Cantada por:** um homem ou uma mulher. Sua melodia se move por oitavas inteiras até onde essa voz canta,
  porque a oitava em que a melodia está escrita decide quem a canta. Se o estilo não nomeia nenhum cantor,
  a voz é acrescentada a ele.
- **Acordes:** uma melodia sozinha costuma voltar do transcritor sem acordes. O Yeufonic então lhe dá
  acordes a partir das próprias notas, para que o planejador tenha uma harmonia a seguir. Acordes que você escrever na
  partitura da gravação são mantidos.
- **Sua melodia** é sempre a partitura da gravação, mesmo que o editor esteja mostrando um take feito a partir
  dela.
- **Estrutura da música:** usada quando a caixa da letra está vazia. Com palavras na caixa, as seções delas são
  a estrutura, e precisam de um **[Chorus]** (ou um **[Verse]**) onde pôr sua melodia.
- **Letra:** um cantarolar pode ser planejado sem letra. Uma melodia tocada em um instrumento precisa de letra para
  ser cantada, então escreva-a primeiro: **Escrever letra** a rascunha para você.

### Arquivos MIDI e covers {#midi-files-and-covers}

> [!NOTE]
> Os arquivos MIDI servem para gerar takes diferentes, muitas vezes excêntricos, de melodias originais.

Além de arquivos de áudio gravados, você pode soltar ou enviar arquivos MIDI padrão (`.mid`, `.midi`) diretamente no modo **Cover**.

Quando um arquivo MIDI é enviado:
- **Transcrição automática da partitura:** o Yeufonic analisa faixas e canais para identificar a melodia vocal principal, o acompanhamento e a progressão de acordes, os transcreve para notação ABC e os carrega direto no piano roll. Leads de sintetizador ou melodias vocais sequenciadas em registros mais graves são transpostos automaticamente para uma oitava natural de canto.
- **Letra embutida:** eventos de letra ou de texto embutidos na sequência MIDI são extraídos e alinhados às sílabas da melodia.
- **Onde caem os compassos:** um arquivo MIDI não tem barras de compasso próprias, e alguns começam com a primeira palavra no tempo *antes* do tempo forte. O Yeufonic lê a bateria e o baixo para achar a barra de compasso real e, quando o arquivo começa com essa anacruse, põe as primeiras palavras em um compasso curto próprio para que os acordes e as marcas de compasso caiam onde caem os da música. Um arquivo sem um padrão claro de bateria e baixo fica como está.
- **Letra colada:** as palavras que você cola são encaixadas na melodia inteira de uma vez, uma sílaba por nota, e as notas que sobram ficam na sílaba anterior. As linhas terminam onde a melodia para e começam onde uma frase começa, então uma seção mais longa ou mais curta do que os títulos da letra não desloca mais o resto. Se as palavras forem mais longas do que a melodia comporta, as últimas linhas ficam de fora.
- **Audição completa com SoundFonts:** o player sintetiza o arranjo MIDI em áudio de alta fidelidade com o **FluidSynth** e SoundFonts General MIDI (`.sf2`). A saída é normalizada pelo pico para que gravações MIDI multipista fracas soem presentes e claras sem distorção.
- **Escolher SoundFonts:** em **Configurações** você pode escolher seu banco SoundFont `.sf2` ativo preferido (como *Arachno SoundFont 1.0* ou *JNS-GM 2.0*). Arquivos `.sf2` adicionais postos em `data/models/soundfonts/sf2/` são detectados automaticamente.
- **Retoques no piano roll:** abra o **Piano roll** para revisar ou mudar notas, escolher que faixa é a melodia vocal principal, harmonizar buracos do acompanhamento com **Preencher lacunas**, ou alinhar uma letra recém-colada com **Associar letra**.

### Fazer um cover de uma música de um corpus {#covering-a-song-from-a-corpus}

A análise de um corpus já fez o que um cover precisa: a partitura, as palavras ouvidas na música e
a voz separada. Então, abaixo das suas gravações, a lista oferece **Dos seus corpus**, recolhida por
corpus, com o tom e o andamento de cada música, e um filtro para um grande. Escolha uma música e ela vira na hora uma
das suas gravações, com a partitura e a letra, e nada é executado de novo. As palavras são postas
sob as seções da partitura, como **Extrair a letra** as põe, a menos que você as tenha revisado no corpus,
caso em que chegam como você as deixou. Elas vão para a caixa da letra, substituindo palavras que vieram de
outra gravação; palavras que você digitou ou editou ali só são substituídas se você disser. A caixa Estilo recebe o
estilo com que a música foi aprendida no corpus, o mesmo do chip dela sob um LoRA treinado com ele.

O arquivo é vinculado em vez de copiado quando o disco permite, então não ocupa mais espaço, e fica
se o corpus for excluído. Algumas músicas estão marcadas *score: melody only* ou *score: first 4 min*: a
transcrição completa delas falhou durante a análise, o que basta para o treinamento. Clique em **Transcrever** para a
partitura completa com os acordes.

**Com um LoRA.** É aqui que as músicas de um corpus mais servem: uma música e um LoRA feitos da mesma
obra, ou de obras diferentes.
1. No modo **Cover**, abra a lista de gravações e escolha a música em **Dos seus corpus**. A
   partitura dela define a melodia e os acordes, e a letra está na caixa.
2. Escolha um **LoRA de estilo**. O LoRA do próprio corpus faz o cantor dele regravar a própria música, o mais perto do
   original. O LoRA de outro corpus a regrava naquele outro estilo e naquela outra voz.
3. Ajuste as forças como para qualquer cover: a gravação já define a melodia, então mantenha **Som**
   perto de **0.50**, e aumente para mais da voz e do som do LoRA.
4. A caixa Estilo já contém o estilo da própria música, e escolher um LoRA põe a palavra-gatilho dele
   na frente. Isso mantém o gênero e o clima da música; outro chip, ou as tags do filtro, a levam
   para outro lugar. O andamento e o tom vêm da partitura, diga o estilo o que disser.
5. Clique em **Criar cover**. **Variações** a renderiza depois nas outras interpretações, e
   **Cantar de novo** dá outra voz sobre a mesma partitura, como com qualquer take.

### Extrair a letra {#extracting-the-lyrics}

**Extrair a letra**, ao lado de *Transcrever*, escreve o que a gravação canta: separa o vocal, escuta e coloca as linhas sob as seções da partitura. É feito quando você pede, não a cada transcrição, porque leva alguns minutos onde transcrever uma partitura leva segundos.

- **Onde roda.** O vocal é separado, e as palavras ouvidas, na GPU quando o motor tem Demucs e Whisper, e na CPU caso contrário (Configurações, **Usar a GPU para stems e letras**). A barra diz em qual das duas etapas está. O Whisper na GPU e na CPU nem sempre escreve as mesmas palavras para o mesmo vocal, já que nenhum é exato: um vocal difícil, como backing vocals sobre uma voz principal, pode diferir em um quinto das palavras.
- **Fazer de novo.** O vocal separado é guardado, então extrair de novo a mesma gravação vai direto para a escuta, o que poupa a maior parte da espera.
- **A letra fica com a gravação.** Pressione **Extrair a letra** de novo e ela volta direto para a caixa, e você é perguntado se quer extrair de novo, o que vale a pena depois de mudar o método em Configurações. Escolher outra gravação traz a letra dela do mesmo jeito, e uma gravação sem letra apaga a da anterior. Palavras que você digitou ou editou ficam, a menos que você aceite substituí-las.

Espere um bom rascunho, não uma transcrição. Comparado com a letra real de duas músicas, o Whisper errou **1,5% das palavras** numa e **25%** na outra, onde voz principal e backing vocals se sobrepõem no último refrão. Ele ouve o vocal inteiro: antes pulava o que o detector de voz tomava por silêncio, o que em vocais cantados era quase a música toda. Leia o rascunho e corrija o que ele ouviu errado, principalmente onde as vozes se sobrepõem.

**Deixar um LLM externo ouvir.** Se um [LLM externo](#external-llm) é o seu provedor, Configurações tem uma opção em *Letra de uma gravação*. Coloque em **LLM externo** e o vocal separado é enviado ao modelo para ouvir as palavras, enquanto o Whisper continua calculando quando cada linha é cantada.

- Precisa de um modelo que aceite áudio, como o Gemini. Nas mesmas duas músicas o Gemini teve **1,5% e 23%**, então os dois estão perto; teste ambos numa música em que o Whisper sofre.
- Quando a resposta do modelo parece uma letra, as palavras dele são usadas, mesmo onde diferem bastante das do Whisper: um vocal enterrado na mixagem é onde o Whisper mais sofre, e o modelo não.
- Se o modelo recusa o áudio, se segura (cortando linhas, ou mandando você para um site de letras, como um modelo pode fazer com uma música que reconhece) ou devolve quase nada, você recebe a versão do Whisper.
- A mensagem no fim diz quem ouviu as palavras.
- Para isso o vocal sai da sua máquina; o Whisper o mantém aqui.

**Numa música de corpus, as duas versões são guardadas.** Quando existem as duas, o painel de revisão da música mostra **Palavras de** com cada versão e o número de palavras, a do modelo externo em uso por padrão. Escolha a outra e as palavras dela vão para a caixa. Na primeira vez que uma versão é escolhida, a letra dela é rascunhada, o que marca as seções com o modelo externo; depois cada versão guarda as próprias palavras, edições e marcação **conferida**, então alternar entre elas é instantâneo e não chama o modelo. Nas linhas do próprio Whisper, qualquer palavra repetida mais de oito vezes seguidas, como um “la” sustentado que ele escreveu centenas de vezes, é cortada para oito.

---

## Instrumentais {#instrumentals}

O terceiro modo escreve uma peça sem voz. Em vez de letra, ele recebe uma **estrutura**:

| Estrutura | O que o YuE2 recebe | Quem decide |
|---|---|---|
| Deixar o YuE2 decidir | `[instrumental]` | o YuE2 escolhe as seções e a duração delas |
| Seções | `[intro] [verse] [chorus] …` | você escolhe as seções, o YuE2 a duração delas |
| Seções cronometradas | `[intro 0:00-0:15] …` | você escolhe as duas coisas |

Adicione seções com os chips **+**, reordene-as com as setas, e dê a cada uma uma duração no modo com tempos.
**Enviado ao YuE2:** mostra exatamente o que o modelo recebe. A estrutura é uma orientação: o YuE2 pode renomear uma
seção, acrescentar um interlúdio, ou passar dos tempos que você deu, então o limite de duração é o teto rígido.

### Um instrumental a partir de uma gravação {#an-instrumental-from-a-recording}

**A partir de uma gravação (opcional)** no topo do editor pega uma das suas gravações, como um cover. A
transcrição dela é a partitura, então não há plano a escrever, e o render toca a melodia e os
acordes dela com o LoRA instrumental.

As seções também vêm da partitura: uma por seção da partitura, com os nomes que o LoRA conhece (um *interlúdio* vira ponte). Uma renderização pareia cada seção da estrutura com uma da partitura, por isso o montador sai do caminho delas.

**Reorganizar a música.** Cada mudança reescreve a partitura (a janela Partitura mostra):

- Arraste uma seção para outro lugar, ou mova com as setas.
- Acrescente uma **cópia** de uma seção logo depois dela.
- Tire uma seção com o **✕**.
- **Restaurar as seções originais** as devolve, até outra partitura ser carregada.

**Acompanhar.** Enquanto o take toca no editor, a seção em que ele está fica acesa, e clicar duas vezes numa seção pula para ela. Os tempos vêm dos compassos e do andamento da partitura, que a renderização segue de perto na primeira parte de um take e num take renderizado inteiro. Uma renderização que termina bem antes da partitura tocou menos música do que a partitura tem, então a lista pode sair de sincronia com o áudio ao longo da música; uma linha sob a lista diz isso, e quanto.

**A letra e a duração.** Um cover mostra a mesma lista sob a letra, e a letra é associada às seções em ordem, então mude-a como quiser: a lista diz o que ela precisa depois que você acrescenta, remove ou reorganiza seções. A lista também mostra o total contra o limite de duração, e oferece subir o limite quando uma música mais longa seria cortada. Pressione **Criar instrumental** para renderizar.

Um instrumental escrito a partir de uma estrutura também tem partitura, e depois de planejado as seções dele são listadas do mesmo jeito. O
montador de estrutura é o pedido de um plano ainda não escrito, então dá lugar à lista. Reordene as seções e clique em
**Renderizar esta partitura**: as tags de seção do render seguem a partitura editada. Um take que já tem áudio é renderizado como um
take novo ao lado, mude o que mudar, então o original mantém o seu. **Escrever um plano novo** (sob a partitura) continua pedindo
uma melodia diferente a partir da estrutura com que o take foi escrito.

**Uma música com voz também funciona.** A partitura dela tem a melodia cantada na parte vocal, que sairia
cantada, então a melodia é dada a um instrumento: onde nenhum instrumento toca, as notas cantadas
passam para um, e a parte vocal fica só com os acordes. O editor avisa isso sob a gravação. Para uma música
costuma ser a melhor escolha: sem a voz, o transcritor tende a perder a
diferença entre verso e refrão, e ouve a música inteira como um único loop de acordes. O LoRA
a arranja como instrumental, então espere partes próprias, como guitarra a mais.

Escolha **Sem gravação: escrever um plano da partitura** na lista para voltar a escrever um plano.

### Quando um instrumental canta {#when-an-instrumental-sings}

De vez em quando o modelo põe uma voz em um instrumental. É uma falha do modelo, não um ajuste
que você errou. Antes de renderizar, se o plano põe notas na voz vocal, um diálogo oferece um plano
novo, uma seed nova, ou renderizar mesmo assim. Um take pronto não é verificado: ouça-o.

### Um instrumental a partir da partitura de uma música {#an-instrumental-from-a-song-s-score}

**Fazer um instrumental**, sob a partitura de uma música ou de um cover na página Partitura do editor (ao lado de **Renderizar esta partitura**
em uma música), faz da
mesma partitura um instrumental, em um take novo: o original fica como estava. A melodia cantada passa
para um instrumento, só as tags de seção da partitura são enviadas ao modelo em vez da letra, o
LoRA instrumental é usado, e o estilo perde as tags que descrevem uma voz (“soft male vocal”).
É o jeito de conseguir “esta melodia, sem voz”. Esvaziar à mão a parte Vocal da partitura de uma música não
basta: o render de uma música continua cantando as palavras que recebe.

---

## Vozes {#voices}

Os chips **Vocal** definem o sexo e o caráter do cantor escrevendo no estilo, para a música inteira.

Para um dueto, ou um cantor nos versos e outro no refrão, ponha indicações de voz na letra e marque
**As vozes seguem as indicações**: veja [A letra](#the-words) em “Escrever uma música a partir de um prompt”. Também funciona para a letra
de um cover.

## Corpus e treinar um LoRA {#corpora-and-training-a-lora}

Um **corpus** é uma pasta de músicas, preparada como conjunto de treinamento para um LoRA de estilo: geralmente um
artista, um gênero ou alguns artistas parecidos.
Abra **Corpus** pelo menu. Vem ligado por padrão; `TRAINING_ENABLED=0` para o app, ou um
motor construído com `WITH_TRAINER=0`, o remove.

**O que o treino precisa.** É a coisa mais exigente que o app faz:

- **O modelo de qualidade total (BF16)**, o recomendado, precisa de pelo menos uns 12,5 GB de memória de GPU (num corte de 3½ minutos; um corte mais longo precisa de mais), quase toda enquanto prepara as músicas. Então uma placa de 16 GB é o mínimo prático, com 32 GB de RAM: o ComfyUI carrega os pesos completos do YuE2 e os caches do conjunto de dados na memória do sistema (no WSL2, ponha `memory=32GB` em `.wslconfig`).
- **O modelo de pouca memória (INT8)** deixa uma placa de 8 GB treinar.
- **Uma placa que não consegue treinar** ainda pode usar LoRAs treinados em outro lugar (**Instalar um LoRA**).
- A janela Treinar avisa quando há menos memória de GPU ou do sistema disponível, então feche antes tudo o mais que use a GPU.

**Os passos:**

1. **Novo corpus.** Dê um nome e uma **palavra-gatilho**, diga se a voz é masculina ou feminina (**nenhuma** para músicas sem vocal: veja abaixo), descreva o som que todas as músicas compartilham e abra a pasta que as contém. Confirme que você tem o direito de treinar com elas e pressione **Ler a pasta**. A pasta é só lida.

   **Um corpus sem vocal.** Escolha **nenhuma** em **Voz** quando as músicas são instrumentais, como música eletrônica e de pista:

   - O app não separa vocal nem escuta palavras, então nada inventa palavras sobre os sintetizadores.
   - A letra de cada música são as tags de seção encontradas na partitura (ou `[instrumental]` quando não tem), a legenda deixa de fora a parte do vocal, e não há revisão de letra: a caixa **Seções** pode ser editada, e uma edição é mantida.
   - O som de cada música é descrito pelo modelo local quando ele está instalado, já que o externo teria só um título.
   - Um LoRA treinado assim pode escrever notas na parte Vocal de um plano, o que faz uma renderização cantar ou cantarolar; o aviso “pode cantar” de um plano mostra isso.
   - Mudar a Voz de um corpus já analisado muda a letra dele de acordo.
2. **Escolher as músicas.** Desmarque as que quer deixar de fora.
   - Quando uma música é preparada, o app guarda uma cópia própria da gravação completa no armazenamento interno de corpus, então um corpus continua inteiro mesmo que a pasta de origem seja esvaziada ou movida depois.
   - Uma gravação de mais de 25 minutos fica de fora, já que muito provavelmente é um álbum ou show inteiro num arquivo. Se houver uma folha `.cue` ao lado, **Dividir em faixas** a corta nas músicas, que tomam o lugar dela no corpus. As faixas vão para a pasta do app; a sua não muda.
   - Músicas mais longas que o limite de GPU do treinador, como faixas de 15 minutos, são cortadas e esmaecidas com segurança num limite de seção musical ao exportar.
3. **Analisar.** O vocal de cada música é separado, a tonalidade, o andamento e as seções são encontrados, e a letra é rascunhada, marcada por seção.
   - Com um LLM externo definido em Configurações, as seções são marcadas pelas palavras ouvidas: os refrões porque as palavras deles voltam, as seções novas pelas pausas. Só as linhas e os tempos são enviados, e as palavras e a ordem nunca mudam. Sem ele, ou se a resposta não contém todas as linhas, as tags vêm da análise musical.
   - **Esboçar de novo**, ao lado de Salvar na revisão de uma música, marca as seções de novo do mesmo jeito sem ouvir a música outra vez, para uma música rascunhada antes, e substitui o que está na caixa.
   - Uma linha sob os botões diz o que está rodando, e a análise ativa aparece no cartão de tarefas e na fila da tela principal. **Parar** termina. Os passos concluídos ficam guardados, então **Analisar** continua de onde parou.
   - **Analisar de novo.** Quando todas as músicas estão analisadas, o botão mostra **Analisado ✓**. Clicar pergunta se você quer reanalisar as sugestões de estilo de todas as músicas com os prompts e as configurações de LLM mais recentes (útil depois de renomear um corpus ou trocar de provedor). Shift-clique em **Analisado ✓** oferece uma reanálise completa do zero (separação de stems, tonalidade, andamento, transcrição e estilos de novo). Cada música também pode ser reestilizada com **Analisar de novo** na revisão dela.
4. **Revisar.** Abra uma música para conferir a letra e marcar **conferida**, e para descrever o som onde ele difere do resto. A legenda de estilo mostra o que o treinador vai ler.
5. **Exportar o conjunto de treino.** Escreve o áudio, a letra e a legenda de cada música. Uma linha sob os botões mostra até onde chegou.
   - O treinador pega só uma parte de cada música, que o app calcula pela memória livre da sua placa de vídeo (uns 5½ minutos numa placa de 16 GB; a janela de registros diz o que escolheu).
   - Uma música mais longa é cortada no fim da última seção dentro disso, esmaecida, e mantém só as palavras ainda cantadas. A linha dela diz “primeiros 3:12 treinados”.
   - Se o treino ficar sem memória, defina a variável de ambiente `TRAIN_MAX_MINUTES` com um número menor, como 3.5: veja o README.
6. **Treinar um LoRA.** Demora bastante, e a GPU fica indisponível para o app até terminar.
   - O progresso aparece sob os botões e na tela principal, onde você pode pará-lo, e o selo do corpus no alto da página pulsa enquanto treina.
   - Treinar de novo guarda o LoRA da última execução com um nome datado, em **Execuções anteriores**, ou o exclui, como você escolher.

### Uma execução que termina antes da hora {#a-run-that-ends-early}

Uma execução pode terminar antes do último passo: **Parar**, uma falha ou a GPU sem memória. A linha sob os botões diz então quando e por quê, e depois de qual passo. A maior parte do trabalho normalmente continua lá: no caminho, o treinador salva um checkpoint a cada 50 passos, e guarda uma cópia do melhor até agora pela perda do planejador.

- **Concluir com o que ele salvou** faz, a partir desses arquivos, o que uma execução completa faz: a melhor cópia, ou senão o último checkpoint, vira o LoRA com o nome do corpus, com a palavra-gatilho, e os checkpoints se recolhem sob ele na lista de LoRAs de estilo. Leva segundos e nenhum tempo de GPU.
- Os últimos passos de uma execução são os que menos mudam o LoRA, então um concluído assim costuma ficar perto de uma execução completa; **Checkpoints** renderiza uma música uma vez em cada passo se você quiser comparar de ouvido.
- Para treinar a execução inteira de novo, pressione **Treinar um LoRA**.

### Executar tudo {#run-all}

**Executar tudo**, ao lado dos três, faz Analisar, Exportar e Treinar um depois do outro, para um corpus que você prefere não esperar: um grande leva horas para analisar. Ele pergunta primeiro o que fazer com um LoRA anterior, e depois continua com a página fechada.

- Ele analisa só o que ainda precisa. Uma música cuja análise falha fica de fora do conjunto de treino e é nomeada sob os botões, e letras que ninguém conferiu são usadas como foram rascunhadas.
- Ele espera qualquer coisa que já esteja usando o motor antes de treinar.
- **Parar** o termina onde está, guardando o que está pronto; parado durante a exportação, ele termina primeiro o conjunto de treino.
- Reiniciar o app o termina, e **Executar tudo** de novo continua.

### Quando a memória da GPU acaba {#running-out-of-gpu-memory}

Um trabalho que fica sem memória de GPU diz isso, com o que tentar: feche outros programas que usem a GPU,
baixe o limite de duração, ou, para treinar, deixe de fora as músicas mais longas. Se o motor falhar e
reiniciar, o trabalho que estava rodando se perde, e isso também é dito.

### O LoRA treinado {#the-trained-lora}

Quando o treino termina, o LoRA aparece na lista **LoRA de estilo** com a palavra-gatilho.

- **As músicas dele.** Escolhê-lo mostra um chip para cada música de que ele aprendeu, sob a caixa Estilo, e clicar num deles põe o estilo daquela música na caixa. Passando de uma dúzia de músicas, uma caixa de filtro e uma fileira das tags que se repetem no corpus (gêneros, climas e instrumentos) as restringem; clique em duas tags para achar músicas com as duas. A lista mostra a primeira dúzia até **Mostrar tudo**.
- **Intensidades iniciais:** veja **Equilibrando Planejador e Som** abaixo.
- **Compartilhar:** pressione **Baixar LoRA** na página do corpus, ou **Baixar** sob o seletor; veja **Compartilhando um LoRA** abaixo.
- **Um LoRA de outra pessoa:** pressione **Importar LoRA** ao lado de **Novo corpus** e escolha o zip dela.
- **Um LoRA treinado em outro lugar com o conjunto exportado:** pressione **Instalar um LoRA** e escolha o arquivo. Ele é adicionado à lista de LoRAs de estilo com a palavra-gatilho deste corpus.

**Excluir um corpus** remove as cópias das músicas que o app fez, as vozes separadas, as letras e
as partituras. A pasta que você indicou, e qualquer LoRA feito com ele, não são tocados.

---

## Direitos autorais e consentimento {#copyright-and-consent}

Com o que você treina, e o que faz com o resultado, é responsabilidade sua pela lei do lugar onde
você mora. O app pede que você declare isso e não verifica: criar um corpus exige que você confirme
que tem o direito de treinar com essas gravações.

Vale saber duas coisas:

- Os pesos do YuE2 estão sob **CC BY-NC 4.0** — uso não comercial, seja o que for que você treine a partir deles.
- Treinar em particular com um corpus e publicar o LoRA ou o que ele produz são atos diferentes. O segundo
  é o que costuma precisar de permissão: de quem tem os direitos das gravações, e para
  uma voz reconhecível, do cantor.

LoRAs que você não treinou têm as próprias licenças: leia-as na página de onde cada um vem
(veja **Onde encontrar LoRAs de estilo** em LoRAs de estilo).

## LoRAs de estilo {#style-loras}

Um LoRA é um arquivo pequeno que inclina o modelo para um som. Ponha um em `models/loras/` e clique em
**Ler de novo** sob o seletor, ou use **Instalar**, e ele aparece na lista **LoRA de estilo**.

Um LoRA de estilo pode ter duas metades, e o seletor mostra quais um arquivo tem:

- **Planejador** molda o que é tocado — o plano de partitura (forma, harmonia, fraseado), e depois a música
  que o render escreve a partir dessa partitura. Age nas duas etapas.
- **Som** molda o áudio — timbre e produção.

Uma força que o arquivo não pode usar fica esmaecida, e um arquivo que este motor não consegue carregar de jeito nenhum é sinalizado
como tal em vez de falhar em silêncio dentro de um render.

### Onde encontrar LoRAs de estilo {#where-to-find-style-loras}

O mais rápido é na instalação: marque **LoRAs de estilo** na página de componentes do instalador (ou, com Docker, rode
`sh scripts/fetch-models.sh --loras`). Isso baixa 39 LoRAs de estilo dos autores deles, 3,8 GB no total, cada um com uma
descrição que dá a palavra-gatilho e as forças sugeridas: os conjuntos abaixo, dois do atomtanstudio (dream pop
e hip-hop old school), e dezesseis sliders de conceito do ntc-ai, que só moldam a partitura (Som não faz nada,
e eles não precisam de palavra-gatilho). Eles estão reunidos, sem alterações, em
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), cujo README dá crédito a cada autor
e aponta para a página de origem. Um LoRA que já esteja na sua pasta com o mesmo nome fica como está.

Há mais no Hugging Face. Estes são os conjuntos reunidos lá, cada um na página do autor:

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), um único LoRA só com a metade de Som

Para adicionar um, baixe o arquivo `.safetensors` dele na aba **Files** do repositório, ponha-o em `models/loras/`
e clique em **Ler de novo**, ou clique em **Instalar** e escolha o arquivo. A página do repositório dá a
palavra-gatilho e as forças sugeridas de cada LoRA: escreva-as em um `.txt` ao lado do arquivo (veja **Descrições** abaixo) e
o seletor as mostra, e põe a palavra-gatilho no começo do Estilo por você. Um LoRA de outro lugar
pode estar salvo em um formato que este motor não sabe carregar: o seletor o sinaliza como tal, e ele não faz mal nenhum.

Cada LoRA traz a licença do autor, que esses conjuntos dão como CC BY-NC 4.0: uso pessoal e não
comercial, como os próprios pesos do YuE2. Leia a licença na página de um LoRA antes de usá-lo, ou de compartilhar o que
ele produz.

### Equilibrar Planejador e Som {#balancing-planner-and-sound}

- **Corpus coesos:** um LoRA treinado com um único álbum ou um som acústico unificado (por exemplo, folk rock dos anos sessenta) aceita forças mais altas, normalmente em torno de **Planejador ~0.85 / Som ~0.80**.
- **Corpus diversos:** se o corpus de treinamento abrange vários gêneros, estilos de produção ou épocas (por exemplo, folk acústico, rock e synth-pop), pesos altos de Som podem causar choques acústicos. Até cerca de **Planejador 0.70 / Som 0.70** o áudio fica limpo mantendo o fraseado melódico e o caráter vocal do artista.
- **Covers:** sua gravação define a melodia, então o LoRA tem menos a moldar e a metade de Som é forçada mais. Mantenha Som perto de **0.50**.
- **Variedade do plano:** com um LoRA treinado a partir de um corpus, **Tranquila** ou **Normal** dão o resultado mais reconhecível. **Tranquila** pode entrar em loop com um LoRA de estilo e um estilo curto, e o plano então dura
  minutos com longas intros repetidas, ou sem nada cantado. Descreva o estilo com mais detalhe (gênero, instrumentos e sensação), ou use **Normal**. Um plano assim, ou um muito mais longo que uma música, é escrito de novo uma vez
  com uma seed nova, e o take falha com uma dica se o segundo sair igual.
- **Achar um bom take:** o caráter do LoRA depende da jogada tanto quanto das forças.
  Entre 0.3 e 0.6 mais ou menos, **Som** muda pouco a voz, então não precisa aumentá-lo.
  **Planejador** muda a interpretação em si, não só a voz, então um valor que vai bem para uma música
  pode ser o mais fraco para outra. Trate-o como a seed: tente alguns (por exemplo 0.6, 0.8 e 1.0) e algumas
  seeds com **Cantar de novo**, e fique com o take de que gostar.
- **Salvar intensidades:** quando achar o par certo para um LoRA, clique em **Salvar intensidades** sob o
  seletor. Escolher esse LoRA então começa com elas, e elas viajam com ele quando você o compartilha.

### Palavras-gatilho {#trigger-words}

A maioria dos LoRAs de estilo é treinada com descrições que **começam** com uma palavra-gatilho, e faz muito pouco
sem ela. O app cuida disso: escolher um LoRA põe o gatilho dele no começo do Estilo,
trocar por outro o substitui, escolher Nenhum o remove, e um render o põe de volta se ele
foi apagado. Você vai ver a palavra aparecer na caixa Estilo — pode editá-la ou movê-la.

### Descrições {#descriptions}

A lista é agrupada por conjuntos. Clique em um título para abri-lo ou recolhê-lo; o seletor lembra quais
você deixou abertos, e o grupo com sua escolha atual sempre abre com ele.

Passe o mouse sobre uma entrada para ler o que ela é, nas palavras do autor, e as forças sugeridas dela. Essas
descrições vêm de um arquivo de texto ao lado do LoRA:

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

A primeira linha dá o nome, uma linha `Trigger:` vira a palavra-gatilho, e o resto é a
descrição. Um LoRA seu tem uma se você escrever um `.txt` ao lado dele. `families.txt` na mesma
pasta dá aos grupos os títulos, um `prefix = label` por linha.

### LoRAs treinados a partir de um corpus {#loras-trained-from-a-corpus}

Um LoRA treinado a partir de um dos seus corpus é um LoRA de estilo comum: aparece nesta lista com os
outros, com a palavra-gatilho ao lado, e as mesmas duas forças se aplicam.

### Testar os checkpoints {#trying-the-checkpoints}

Uma execução de treino salva um checkpoint a cada 50 passos: cada um é o LoRA como estava naquele ponto do treino. Eles soam mais ou menos igualmente bem, mas cada um pesa de forma diferente o que aprendeu, então cada um tem o próprio gosto, mantendo o estilo e o som característico com que o LoRA foi treinado.

**Onde ficam.** Ficam sob o LoRA no seletor: **▸ 9 passos** ao lado do nome do LoRA os abre (Configurações pode excluí-los no lugar, para poupar espaço). Um checkpoint cujo LoRA foi excluído fica em **Checkpoints de treino**.

**Tirar alguns.** Pressione **Editar** no corpus: **Checkpoints de treino** lá lista os de cada execução, desta e das anteriores, com os tamanhos. Marque os que vão sair e pressione **Excluir**. O LoRA pronto não aparece na lista; ele tem o próprio **Excluir LoRA**.

**Ouvi-los lado a lado:**

1. Escolha o LoRA e prepare o editor como faria para um take.
2. Pressione **Checkpoints**, ao lado de **Excluir LoRA** (em cinza para um LoRA sem checkpoints).
3. Marque os passos que quer, defina se quiser um limite de duração para esses takes, e pressione **Renderizar**.

A própria ação do editor roda uma vez em cada checkpoint, todas com uma semente, e cada take leva o nome do passo: *Night drive · step 250*, *Night drive · full*. Eles ficam dentro do take aberto no editor ou, para uma música nova, dentro do último deles (veja **Takes dentro de um take**, em A biblioteca). O editor fecha, então você volta à biblioteca onde os takes estão sendo feitos. Uma música ou um instrumental escreve o plano e segue direto para a renderização.

Em uma música ou um instrumental, o LoRA escreve a melodia além de moldar o som, então a mesma
seed não dá a mesma música: cada checkpoint escreve a própria melodia e estrutura. A seed
escolhe entre o que o modelo considera provável, e cada checkpoint pensa um pouco diferente desde a
primeira nota, então os planos se separam em poucos compassos. O que fica é o som. Para comparar só o
som, carregue um plano com **Partitura** e clique em **Renderizar esta partitura** com cada checkpoint por vez.

Arquivos novos aparecem quando o motor olha de novo `models/loras/`, o que ele faz quando as
opções são recarregadas.

### Compartilhar um LoRA {#sharing-a-lora}

Escolha um LoRA e clique em **Baixar** sob o seletor: você recebe um zip com o LoRA e a nota dele.
Para um LoRA treinado a partir de um corpus, a nota traz os estilos aprendidos, então os chips vão com ele.

Para adicionar um que lhe mandaram, clique em **Instalar** e escolha o zip dele, ou um arquivo `.safetensors`
avulso. Ele vai para `models/loras` sob o título **Instalados**, com o nome, a palavra-gatilho e os
chips. **Excluir LoRA** remove o LoRA escolhido, a nota e a linha de grupo dele; **Ler de novo** lê a pasta de novo
depois que você adiciona um arquivo à mão.

---

## Stems {#stems}

Clique em **Stems** em qualquer take. Escolha um modelo, marque as partes que quiser — voz, bateria, baixo, outros,
e guitarra e piano em alguns modelos — e rode.

A separação é feita na **GPU** quando o motor tem Demucs, como um trabalho na fila do motor: espera um
render em andamento, depois vai rápido, e um render na fila atrás dela espera por sua vez. Um motor construído antes
disso, um LoRA em treinamento (que ocupa a GPU), **Usar a GPU para stems e letras** em Não em Configurações, ou `STEMS_ON_GPU=0` a deixa na **CPU**, que é mais lenta
e nunca atrasa um render. *Ajustado* roda quatro modelos seguidos para uma separação melhor e leva umas quatro vezes
mais.

Para uma faixa de acompanhamento, escolha **Voz e instrumentos**. Divide a música em duas: a voz, e
os **instrumentos**, todo o resto como um único stem. Desmarque **voz** para ficar só com os instrumentos. É
a mesma separação dos quatro stems, somados de novo, então leva o mesmo tempo e soa igualmente limpa.
A versão *ajustada* é a que deixa menos voz para trás.

Os stems vão para `data/stems/<title>-<id>/`, tocam pelos chips do cartão, e são baixados um a um ou em
zip. Ficam até você excluí-los.

---

## Parar, excluir e começar de novo {#stopping-deleting-and-starting-again}

O que o motor está fazendo aparece na barra de cima, ao lado do nome: uma pílula com o trabalho, o tempo dele, uma linha
na base mostrando até onde chegou, e quantos trabalhos esperam atrás. Nada mais na página muda quando um
trabalho começa ou termina. Clique nela para o cartão de trabalhos: a etapa, **parar**, e **A seguir**, os trabalhos em espera, cada um com
**cancelar**.

Um take na fila ou em andamento mostra **Cancelar** no cartão, e **parar** no cartão de trabalhos para aquilo em
que o motor estiver trabalhando. O título de um take no cartão de trabalhos, na lista **A seguir** dele, ou no player no
pé da página leva você ao take: ao espaço dele, limpando qualquer busca ou filtro que o esconda. Excluir um take para o trabalho dele e remove os stems. **Excluir** ao lado de uma
gravação remove o arquivo e os stems dele; os covers feitos a partir dela mantêm o áudio e a partitura, mas não podem
ser renderizados de novo.

**+ Música**, **+ Cover** e **+ Instrumental** no painel do take, ou **Nova música** ao lado do
título do editor, começam de novo a partir do take mostrado. Eles limpam o título, a letra e a partitura,
e partem dos padrões: um estilo vazio (com a palavra-gatilho de um LoRA escolhido), o limite de duração
habitual, Harmonia Variada, variedade do plano normal, interpretação Ampla, acabamento de produção ligado,
normalização desligada, e uma seed nova não fixada. Um LoRA escolhido e uma gravação escolhida continuam escolhidos.
O take mostrado solta o editor, para que Renderizar não possa agir sobre ele por engano.

Palavras que você tinha escrito mas não usou não são jogadas fora: uma barra oferece restaurá-las.

## A biblioteca {#the-library}

### Espaços {#spaces}

Os takes moram em **espaços**: um espaço por música, por álbum, ou para rascunhos. O nome do espaço acima dos takes é o que está sendo mostrado, e tudo o que você faz vai para lá.

- **Escolher um:** clique no nome para ver a lista de espaços. Digite para achar um pelo nome, ou escolha com as setas e Enter. Os cinco usados por último vêm primeiro, depois todos os espaços, cada um com quantos takes tem.
- **Novo espaço**, **Renomear este espaço**, **Importar take** e **Excluir este espaço** ficam no pé da lista. Excluir um espaço nunca exclui takes — eles vão para Default.
- **Mover um take:** o botão de pasta num cartão move aquele take para outro espaço, com os takes que ele contém.
- As gravações são compartilhadas por todos os espaços, então uma gravação pode virar cover em vários.

### Takes dentro de um take {#takes-inside-a-take}

**Variações**, **Tentar mais** e **Checkpoints** fazem cada um vários takes de uma música. Eles são guardados
**dentro** do take de onde vieram, para que o espaço liste suas músicas e não cada render de cada uma.
Checkpoints é clicado no editor: com um take aberto ali, os takes dele vão para dentro desse take; para
uma música nova, que ainda não tem take, o take do último checkpoint marcado (o LoRA concluído, quando
está entre eles) contém os outros.

- **O botão Dentro** aparece entre os botõezinhos no topo de um cartão quando o take dele contém
  takes, prontos ou ainda em andamento, e fica **aceso em laranja**. Passe o mouse sobre ele para ler quantos estão
  prontos e quantos faltam. O próprio cartão é bem mais claro que os outros (no
  tema claro, um tom quente), para que um take com takes dentro se destaque em uma lista. (O botão do rack de masterização ao lado acende em verde do
  mesmo jeito quando o take está masterizado.)
- **Clique nele** e um painel se abre sob o cartão com os takes que ele contém, cada um no próprio cartão. Um
  take aparece ali quando está pronto; enquanto é feito, só o take a que pertence é mostrado.
  Clique de novo no botão, ou em **Fechar**, para fechá-lo.
- **Um take dentro de outro é um take como qualquer outro.** Toque-o, marque com estrela, salve, separe em
  stems, renomeie, e clique duas vezes para abrir a música e a partitura dele.
- **Um nível só.** Um take dentro de outro não contém nenhum, então o cartão dele não tem Variações nem Tentar
  mais, e **Checkpoints** no editor fica esmaecido enquanto ele for o take aberto ali. **Tirar** (a seta saindo de uma caixa) o transforma em um take próprio na lista do espaço, e aí ele pode.
- **As ferramentas da lista seguem o painel.** Enquanto há um aberto, **Selecionar tudo**, **Favoritos**, os botões
  de tipo, **Comparar**, **Excluir** e anterior e próximo do player agem sobre os takes do
  painel. O take cujo painel está aberto fica na página digam os filtros o que disserem.
- **O que toca dentro aparece fora.** Se você fechar o painel enquanto um dos takes dele toca,
  o botão Tocar do take que o contém brilha em dourado, para você ver de onde vem o
  som. O verde continua indicando que é esse mesmo take que está tocando.
- **A busca os encontra** como a qualquer outro take, onde quer que estejam. Enquanto há uma busca, o que ela
  encontra aparece como cartões simples, e um take que está dentro de outro diz em qual.
- **Excluir um take exclui os takes que ele contém.** O aviso diz quantos. Tire antes os que quiser
  manter.

Takes feitos antes de isto existir ficam onde estão, lado a lado na lista.

### Cartões {#cards}

Cada cartão nomeia as configurações que deram forma ao take — Harmonia, Interpretação, a voz gravada, Variedade do plano, o LoRA e as intensidades, a semente, o motor que o renderizou e a idade dele —, então um cartão se lê como a receita que o fez. Um título fica sempre numa linha, terminando em … quando é longo; passe o ponteiro sobre o título, as configurações ou o estilo de um cartão para ler tudo.

**Salvar** pergunta em que formato baixar o take. Começa com o que você salvou da última vez, e sem nada escolhido na primeira.

- **FLAC, WAV ou MP3:** o áudio.
- **Vídeo**, para um take com imagem: um MP4 da música que mostra a imagem que o cartão mostra (vídeo H.264, áudio AAC a 192 kbps). Apps de mensagem como o WhatsApp enviam e tocam como vídeo, onde um arquivo de áudio vai como documento.
- **Take**, ao lado deles: a receita do take, um arquivo pequeno (`<title>.yeufonic.json`) com a letra, o estilo e a partitura, as sementes e configurações, os LoRAs pelo nome e as configurações do rack de masterização, mas não o áudio. Com um formato escolhido também, os dois vêm num zip; pressione de novo o formato escolhido para salvar só a receita. O arquivo não contém nada da sua instalação (nem caminhos, nem ids, nem chaves), então pode ser guardado, ou compartilhado com outra pessoa que use o Yeufonic.
- Com o rack de masterização ligado, todos os formatos têm o som masterizado.

**Importar take**, na lista de espaços, cria um take novo no espaço mostrado a partir de um arquivo assim; soltar o arquivo na biblioteca faz o mesmo. O take contém o plano, pronto para renderizar, então pode ser conferido ou mudado antes.

- Qualquer um dos motores pode renderizá-lo: a mesma partitura e semente no mesmo motor dão um take muito parecido, no outro motor um diferente.
- Um LoRA que ele cita e que não está instalado aqui é avisado na importação, para você instalá-lo ou escolher outro antes de renderizar.
- A gravação de um cover não vai no arquivo, então um cover compartilhado chega como música com a partitura e a letra do cover, deixando para trás as configurações que eram da gravação (a trava de andamento, Harmonia, indicações de voz e o limite de duração): um plano novo a partir dele começa como uma música a partir de um prompt.

**Pesquisar takes** acha os takes com cada palavra que você digita em algum lugar do título, do estilo, da letra ou do nome do LoRA, sem diferenciar maiúsculas. Procura no espaço mostrado; **Todos os espaços**, ao lado assim que você digita, procura em todos, e um cartão de outro espaço diz de qual. × ou Esc limpam. A caixa começa vazia toda vez que a página abre, e oferece suas últimas pesquisas que acharam algo: clique numa, ou escolha com as setas e Enter.

**Escolher o que aparece, e como:**

| Controle | O que faz |
|---|---|
| **Música**, **Cover**, **Instrumental** | Mostram takes desses tipos: acenda um ou mais, ou nenhum para todos. |
| **Favoritos** | Mostra só os takes com estrela; clique de novo para mostrar todos. |
| Os ícones de layout | Cartões **confortáveis** mais largos com mais do prompt, ou **compactos** mais estreitos; a **largura toda** da janela ou uma coluna centralizada; cada take **recolhido** à linha de título. Os que estão em uso ficam acesos em verde; passe o ponteiro sobre um ícone para ler o que um clique faz. |

Enquanto os takes estão recolhidos, o botão no canto superior direito de um cartão abre só aquele cartão, e um clique em qualquer lugar fora dele o recolhe de novo. Um cartão recolhido com stems mostra uma etiqueta **Stems**, que o abre do mesmo jeito.

**Selecionar takes.** Marque takes e a fileira oferece o que dá para fazer com eles, no lugar dos tipos e do layout: quantos estão escolhidos, **Comparar**, **Excluir** e **Concluído**, que os desmarca. **Selecionar tudo**, no fim da fileira, marca todos os takes mostrados.

### Uma imagem para cada take {#a-picture-for-each-take}

Cada take novo ganha uma imagem da música.

- **Onde aparece:** de leve atrás do cartão do take, no alto do painel do take quando você o escolhe, e atrás do editor quando o take está aberto lá.
- **Quando é feita:** desenhada neste PC, espera até nenhuma música estar sendo feita, então nunca atrasa um plano nem uma renderização, e aparece pouco depois de a música ficar pronta. Desenhada por um LLM externo, é feita enquanto o take renderiza.
- **Como é feita,** em dois passos: o título, o estilo e as primeiras palavras do take viram uma **descrição** de uma imagem, depois um modelo de imagem a **desenha** sobre branco, e o branco é tirado, deixando a imagem com fundo transparente.
- **Um take feito dentro de outro** (Tentar mais, Variações, Checkpoints) mostra a imagem do take em que está, em vez de ter uma própria.
- Um modelo de imagem não desenha uma banda ou pessoa real, então a descrição deixa os nomes de fora; e as letras da própria imagem ficam suaves, para não brigar com as do cartão.

#### Dois jeitos de desenhar: FLUX.2 klein neste PC, ou um LLM externo {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

As imagens precisam de algo que saiba desenhar. Há dois, e você pode ter um, os dois ou nenhum.

| | FLUX.2 klein, neste PC | O modelo de imagem do seu LLM externo |
|---|---|---|
| O que é | um modelo de imagem pequeno que roda no motor, ao lado do YuE2 | o próprio modelo de imagem do provedor, como o do Gemini |
| Quanto custa | nada; cerca de 8 GB de disco | cada imagem é uma requisição ao provedor, que pode ser cobrada |
| O que sai do PC | nada: a descrição é escrita pelo Gemma neste PC, ou feita a partir do próprio take | o título, o estilo e as primeiras palavras do take, e a descrição |
| Quando roda | na GPU quando nenhuma música está sendo feita: depois da sua música, nunca no caminho dela | ao lado dos renders, enquanto rodam |
| O que você configura | uma opção na instalação | o LLM externo em Configurações, com um provedor que ofereça um modelo de imagem |

**Para desenhar neste PC, instale o FLUX.2 klein.**

- **Windows:** marque **FLUX.2 [klein]** na página de componentes do instalador. Ele não vem marcado
  a menos que você o escolha. Um app instalado recebe a mesma página ao atualizar, ou rode o instalador de novo
  pela página da versão: a caixa é lembrada depois, e uma atualização nunca o baixa duas vezes. São
  três arquivos, cerca de 8 GB no total.
- **Docker:** rode `sh scripts/fetch-models.sh --pictures`, que põe os três arquivos em `models/`
  (`diffusion_models`, `text_encoders` e `vae`) e verifica cada um, e depois reinicie o app com
  `docker compose restart app` para que ele os encontre.

**FLUX.2 klein 9B, se você tiver a placa de vídeo para isso.** O klein tem um tamanho maior, um modelo de mais qualidade
que desenha mais detalhe e mãos e rostos melhores, pensado só para placas de vídeo com mais memória
de vídeo. O Yeufonic nunca o baixa, porque os arquivos dele têm acesso restrito no Hugging Face e estão sob a **licença não comercial**
da Black Forest Labs, mas ponha-os no lugar e eles são usados.

- **Disco:** cerca de 18 GB para o par habitual, o modelo FP8 e o codificador de texto FP8 dele (16 GB com o codificador
  FP4), ao lado dos arquivos do 4B. Ele precisa do VAE do 4B (`flux2-vae.safetensors`), então instale o 4B primeiro.
- **Memória de vídeo:** roda em uma placa de 16 GB, mas ocupa quase toda enquanto desenha, com a memória livre
  perto de zero. As imagens esperam até nenhuma música estar sendo feita, então ele não deixa suas músicas mais lentas, mas outros
  programas que usem a placa de vídeo ao mesmo tempo podem ter problemas. Com menos memória ele ainda funciona, mais
  devagar, enquanto o motor põe e tira o modelo; ali o 4B é a melhor escolha.

1. **O modelo.** Entre no Hugging Face, aceite a licença em
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   e baixe `flux-2-klein-9b-fp8.safetensors` (9,4 GB). Ou pegue o de precisão total
   `flux-2-klein-9b.safetensors` de [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   o do Mac, que tem mais ou menos o dobro do tamanho e precisa do dobro de memória.
   Ele vai na pasta `diffusion_models`.
2. **O codificador de texto dele.** Em [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   que não exige login, baixe um destes e ponha na pasta `text_encoders`:
   `qwen_3_8b_fp8mixed.safetensors` (8,7 GB, a escolha habitual em uma placa NVIDIA), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 GB, o menor) ou `qwen_3_8b.safetensors` (16,4 GB, precisão total, para um Mac).
   **Com o motor yue2.cpp** o servidor de imagens não consegue ler esses codificadores: pegue no lugar `Qwen3-8B-Q4_K_M.gguf`
   (5,0 GB) de [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (`-Q8_0.gguf`, 8,7 GB, também funciona), e ponha na mesma pasta.
3. **Onde ficam as pastas:** sob `models/` na pasta do Yeufonic para **Docker**; sob
   `engine\ComfyUI\models` na pasta de instalação no **Windows**; sob `engine/ComfyUI/models/` na
   pasta de instalação em um **Mac**.
4. **Deixe o app vê-los, e escolha.** Reinicie o Yeufonic (com Docker, `docker compose restart app`),
   e depois ponha **Imagens dos takes: modelo** em Configurações em *FLUX.2 klein 9B*. O 4B desenha até você fazer isso, e
   Configurações avisa quando o 9B está escolhido mas não consegue desenhar aqui. Escolha
   *4B* para voltar sem remover nada. A nota da imagem no editor diz qual a desenhou
   (*drawn by FLUX.2 klein 9B on this PC*).

O modelo e o codificador só são encontrados com estes nomes, então mantenha os nomes de arquivo como foram baixados.

**FLUX 3 klein, para escrever texto e uma placa de 12 GB ou mais.** O FLUX 3 Image Klein da Black Forest Labs desenha a partir de uma
descrição completa da cena, que é exatamente o que são os prompts de imagem que o Gemma ou o LLM externo escrevem, e
escreve texto bem, o que combina com **Imagens dos takes: título da música na imagem**. Como o 9B, o Yeufonic nunca o baixa: os arquivos dele têm
acesso restrito no Hugging Face e estão sob a **FLUX Kommunity License** (uso não comercial, e uso comercial do que
ele desenha para quem está abaixo do limite de receita da licença; leia antes de aceitar). Ponha os arquivos no lugar e ele
pode ser escolhido.

- **Disco:** cerca de 11 GB para o par int8, ao lado dos arquivos do 4B. Ele usa o VAE do 4B (`flux2-vae.safetensors`),
  então instale o 4B primeiro.
- **Memória de vídeo:** cerca de 11 GB enquanto desenha. Ele dá várias vezes mais passos que os FLUX.2 klein, então cada
  imagem leva mais tempo.
- **Motor:** só o motor ComfyUI, por enquanto; com o motor yue2.cpp ele não é oferecido.

1. **Entre no Hugging Face** e aceite a licença em
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **O modelo,** na pasta `diffusion_models`: `flux3-image-klein-int8-convrot.safetensors` (5,8 GB, a escolha
   habitual em uma placa NVIDIA), `flux3-image-klein-nvfp4.safetensors` (5,3 GB, para uma placa RTX 50) ou
   `flux3-image-klein-bf16.safetensors` (11,1 GB, precisão total, para um Mac).
3. **O codificador de texto dele,** na pasta `text_encoders`: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) ou
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, para um Mac).
4. **Deixe o app vê-los, e escolha:** reinicie o Yeufonic (com Docker, `docker compose restart app`), e depois ponha
   **Imagens dos takes: modelo** em Configurações em *FLUX 3 klein*. A nota da imagem no editor diz *drawn by
   FLUX 3 klein on this PC*.

As pastas são as mesmas que para o 9B, e os arquivos só são encontrados com estes nomes.

**FIBO 2.0, para o visual de uma fotografia e uma placa de 16 GB.** O FIBO 2.0 da Bria desenha o mais perto de uma
fotografia real das capas de disco em que as imagens se inspiram: detalhes mais nítidos, uma profundidade de campo
natural, as cores do filme e mais do que a descrição pede. O Yeufonic também nunca o baixa. **A licença dele é
CC BY-NC 4.0: só uso não comercial.** A licença do FLUX 3 permite que quem está abaixo do limite de receita dela use
comercialmente o que ele desenha; com o FIBO, qualquer uso comercial, incluindo a capa de uma música que você vende,
precisa de um acordo com a Bria. Leia a licença antes de usá-lo.

- **Disco:** cerca de 10,4 GB, o modelo e o complemento turbo. Ele lê o codificador de texto do FLUX 3 e o VAE do 4B,
  então com o FLUX 3 instalado não é preciso mais nada.
- **Memória de vídeo:** cerca de 12,5 GB enquanto desenha, então uma placa de 16 GB. Uma placa menor descarrega uma
  parte, o que é bem mais lento.
- **Tempo:** com o complemento turbo, mais ou menos o mesmo que o FLUX 3. Sem ele, o FIBO desenha com as próprias
  configurações, cerca de oito vezes mais.
- **A capa:** desenhada pelo FIBO, a borda em volta da fotografia não tem a linha escura fina, que o FIBO desenhava como
  barras grossas e uma caixa em volta do título.
- **Motor:** só o motor ComfyUI.

1. **O modelo,** de [Comfy-Org/Fibo-2.0](https://huggingface.co/Comfy-Org/Fibo-2.0), sem login, na pasta
   `diffusion_models`: `fibo2_dev_int8_convrot.safetensors` (8,4 GB, a escolha habitual numa placa NVIDIA) ou
   `fibo2_dev_bf16.safetensors` (16,5 GB, precisão total, para um Mac).
2. **O complemento turbo,** da mesma página, na pasta `loras`:
   `fibo_2.0_turbo_lora_avg_rank_270_bf16.safetensors` (2 GB). Não é um LoRA de estilo e não é oferecido como tal.
3. **O codificador de texto,** se o FLUX 3 não estiver instalado: `qwen3vl_4b_int8_convrot.safetensors` (4,9 GB) ou
   `qwen3vl_4b_bf16.safetensors` (8,9 GB, para um Mac), da mesma página, na pasta `text_encoders`.
4. **Deixe o app vê-los, e escolha:** reinicie o Yeufonic (com Docker, `docker compose restart app`), e depois ponha
   **Imagens dos takes: modelo** em Configurações em *FIBO 2.0*. A nota da imagem no editor diz *drawn by
   FIBO 2.0 on this PC*.

**Para desenhar com um LLM externo,** abra Configurações e ponha **LLM para escrever letras e tags de estilo** no
[LLM externo](#external-llm), com a **URL da API**, a **chave de API** e o **modelo**, como para as letras. O provedor precisa ter um modelo
de imagem: o Gemini tem (usa-se `gemini-3.1-flash-image` a menos que você nomeie outro), e a um provedor compatível com OpenAI
pede-se `gpt-image-1`. O app pede ao provedor a lista de modelos dele, em segundo plano,
ao iniciar, quando esses ajustes mudam e a cada poucas horas, e só desenha lá quando a lista
tem o modelo de imagem.

Sem nenhum dos dois, **Imagens dos takes** em Configurações diz **Sem imagens: o fundo padrão**, com uma linha sobre como
tê-las, e a opção de fazê-las não pode ser escolhida.
Configure qualquer um dos dois e elas são ligadas: a partir daí são feitas imagens para os takes que você criar.

#### Gerenciar as imagens em Configurações {#managing-pictures-in-settings}

| Ajuste | Faz |
|---|---|
| **Imagens dos takes** | *Fazer uma para cada take novo* (o padrão quando algo consegue desenhar), ou *Só quando pedido*, em que um take mantém o fundo padrão até você fazer uma pelo quadrado dele ou pelo botão Imagem do editor. Os ajustes abaixo moldam uma imagem feita de qualquer um dos dois jeitos. Fica em *Sem imagens* enquanto nada aqui consegue desenhar. |
| **Imagens dos takes: desenhadas por** | *Este PC se o klein estiver instalado, senão o LLM externo* (padrão), *Este PC (o modelo abaixo)* ou *O modelo de imagem do LLM externo*. Qual klein desenha neste PC (FLUX.2 klein 4B ou 9B, ou FLUX 3 klein) é escolhido em **modelo**. O FIBO 2.0 também é escolhido aí. |
| **Imagens dos takes: modelo** | *FLUX.2 klein 4B* (padrão), *FLUX.2 klein 9B*, *FLUX 3 klein*, ou *9B onde os arquivos dele estiverem instalados, senão 4B*. Só para imagens desenhadas neste PC. O 9B e o FLUX 3 nunca são instalados por você: veja [FLUX.2 klein 9B e FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) acima. Se o pedido não estiver lá, outro desenha, e Configurações diz qual. O *FIBO 2.0* também é adicionado à mão e é só para uso não comercial: veja acima. |
| **Imagens dos takes: descritas por** | quem escreve o prompt de imagem, a partir do título do take, do estilo artístico abaixo, do estilo e da letra dele (até 50 linhas). *Gemma local se instalado, senão o próprio take* (padrão), seja quem for que desenhe. *Gemma local*: escrito neste PC; precisa da opção Rascunhos de letra. *A partir do próprio take*: sem LLM; uma descrição feita com o título, o estilo e as primeiras palavras do take, a mais rápida, e nada é enviado. Ou o *LLM externo*, uma requisição por imagem; quando ele não está disponível, ou você passa para LLMs locais na sessão, o Gemma as escreve no lugar se estiver instalado. |
| **Imagens dos takes: estilo artístico** | como a imagem deve parecer, dado ao LLM que escreve o prompt de imagem (esmaecido quando o take se descreve sozinho). Por padrão um design abstrato e surrealista no estilo das capas dos anos setenta e oitenta, sem texto nem pessoas. Esvaziado, volta a isso. |
| **Imagens dos takes: seu próprio prompt** | palavras com que o prompt de imagem de cada imagem começa, como *salt marsh, overcast*, até 512 caracteres; o prompt que o LLM escreve vem depois. Vazio (padrão): nenhuma. Só quando um LLM escreve o prompt de imagem (esmaecido quando o take se descreve sozinho). |
| **Imagens dos takes: título da música na imagem** | *Não* (padrão) ou *Sim*: o título da música é escrito em negrito na capa, em maiúsculas ou minúsculas, como você o digitou, mesmo quando é o nome de um artista (a imagem em si continua sendo descrita sem ele). Quase sempre a imagem é emoldurada por uma linha escura fina dentro de uma borda branca quebrada, como em muitas capas dos anos setenta, com o título centralizado em uma faixa mais larga em cima ou embaixo. Mais ou menos uma em cada cinco não tem borda: o título fica sobre a imagem, em um canto ou centralizado em cima ou embaixo, em uma cor apagada tirada da imagem, e pede-se ao LLM que deixe essa parte da imagem livre para ele. Tudo isso é sorteado para cada imagem. O FLUX.2 klein pode escrevê-lo com algum erro. Só quando um LLM escreve o prompt de imagem. |
| **Imagens dos takes: modelo de imagem** | qual dos modelos do provedor desenha. Só para imagens desenhadas pelo LLM externo (escolha-o em **Desenhado por**; esmaecido senão), e vazio para o habitual do provedor, que é quase sempre o que você quer. |

Então com o FLUX.2 klein instalado e os ajustes como vêm, as imagens são feitas inteiramente neste PC, mesmo
quando o LLM externo escreve suas letras: o Gemma escreve cada prompt de imagem onde os Rascunhos de letra estão instalados, e
sem ele a descrição é feita a partir do próprio take, sem LLM, o que não leva tempo. Escolha *O modelo de imagem do
LLM externo* para que o provedor as desenhe, ou ponha **descrito por** em *A partir do próprio take* para as
imagens mais rápidas, ou em *LLM externo* (uma requisição por imagem).

#### A imagem de um take no editor {#a-take-s-picture-in-the-editor}

O ícone **Imagem** na fileira de cima da janela do editor, ao lado dos outros botões do take, mostra a imagem com duas opções:

- **Fazer uma imagem nova** a refaz em segundo plano.
- **Usar o fundo padrão** a tira para sempre: nenhuma imagem é feita de novo para aquele take, a menos que você peça.

Clique na imagem ali para vê-la inteira, tão grande quanto a janela permite; um clique em qualquer lugar ou Esc a guarda e deixa o editor como estava. A imagem inteira tem as mesmas duas opções embaixo: escolha ali **Fazer uma imagem nova** e a imagem continua à vista enquanto a nova é feita, com o que está acontecendo entre os botões, e então troca para a nova quando fica pronta.

No cartão de um take, o quadrado no canto superior esquerdo mostra a imagem quando você aponta para ele. Um take sem imagem oferece ali **Fazer uma imagem nova**, onde este PC pode fazer imagens.

### Comparar takes {#comparing-takes}

Marque de dois a seis takes e pressione **Comparar** (aparece ao lado de Selecionar tudo assim que dois estão marcados, e espera os takes que ainda renderizam). Os takes se empilham numa janela numa posição compartilhada:

- Pressione **1** a **6**, ou clique num, para trocar: ele continua do mesmo momento da música, tocando ou pausado.
- A **barra de espaço** toca e pausa, e as setas andam 5 segundos.
- A estrela marca o que você prefere.
- **Igualar o volume** abaixa os takes mais altos ao nível do mais baixo, já que um take mais alto tende a parecer melhor.
- **Ocultar nomes** embaralha os takes e os chama de Take A, B, C para uma escuta às cegas.

### O player {#the-player}

Clique ou arraste na forma de onda para navegar. Anterior e próximo percorrem os cartões na ordem mostrada.

| Tecla | Faz |
|---|---|
| Espaço | tocar ou pausar |
| Esquerda, Direita | voltar ou avançar cinco segundos |
| Shift+Esquerda, Shift+Direita | o take anterior ou próximo; na vista Playlists, a música anterior ou próxima da playlist |
| Cima, Baixo | volume |

As teclas de mídia do sistema também funcionam. As teclas próprias do take estão em [Atalhos de teclado](#hot-keys).

### O visualizador de áudio e a letra sincronizada {#the-audio-visualizer-and-synced-lyrics}

Clique em **Visualizador** na barra de transporte (ou **V** enquanto uma faixa toca) para abrir o palco do visualizador em tela cheia.

O palco mostra visualizações de áudio em tempo real sincronizadas com a reprodução:

- **Modos do visualizador:** escolha entre onze visualizadores na barra de cima:
  - *Yeufonic:* o próprio logotipo, respirando — o ladrilho brilha com os graves e se expande com a batida, cada braço do diapasão é um medidor com a metade dele do espectro, e o ponto verde acende com a batida.
  - *Fita de onda:* duas fitas harmônicas flutuantes que reagem ao som.
  - *Aurora boreal:* cortinas ondulantes de aurora etérea que reagem aos médios e agudos.
  - *Nebulosa cósmica:* um campo de estrelas e uma nebulosa de partículas interestelares que gira e pulsa no ritmo.
  - *Caleidoscópio:* simetrias geométricas radiais que pulsam com o andamento.
  - *Grade neon:* um plano em wireframe synthwave retrofuturista em perspectiva que ondula com as linhas de baixo.
  - *Distorção líquida:* uma superfície fluida deslocada por ondas harmônicas.
  - *Enxame de partículas:* aglomerados de partículas gravitacionais que se dispersam com as batidas de percussão.
  - *Barras de espectro hi-fi:* um analisador de espectro multibanda com picos flutuantes que caem.
  - *Arte:* a imagem do take, grande, com o título embaixo, sobre uma cópia desfocada de si mesma que se move com a música. Um take sem imagem mostra a cena Yeufonic até que uma seja feita.
  - *Nenhum:* só a imagem do take, parada, sobre um fundo escuro, ou o símbolo do Yeufonic quando não há imagem. Nada se move: para um computador que sofre com as outras cenas.
- **Atrás das cenas:** as cenas Arte, Yeufonic, Mandala, Grade, Líquido e Barras tocam sobre a imagem do take, que se move suavemente com a música, quando o take tem uma. Por cima também pode se mover algo, nas cores da imagem: *Respiração* (só a imagem), *Raios de luz* girando a partir do centro, *Ondulações* lançadas com a batida, *Cor à deriva*, *Profundidade* (mais cópias da imagem girando umas contra as outras) ou um *Halo espectral*. Cada cena começa com o seu (cor à deriva atrás de Arte, o halo atrás de Mandala, raios atrás de Grade, ondulações atrás de Líquido, só a imagem atrás de Yeufonic e Barras); pressione **B** para percorrê-los, e a cena lembra sua escolha.
- **A forma de onda:** sob as cenas Yeufonic e Arte, a forma de onda do take mostra quanto da música já tocou; clique nela para pular para lá.
- **Arte e dinâmica do vinil:** mostra a capa do take no estilo Hipgnosis em uma capa 3D interativa que se inclina e gira com o ponteiro. Um disco de vinil realista gira a 33⅓ RPM e sai da capa com as batidas de baixo, com um brilho holográfico e anéis de onda de choque que reagem ao ritmo. Mude de modo com o botão **Capa**: *Capa*, *Aura* (fundo desfocado) ou *Desligado*.
- **Uma imagem nova:** o botão de imagem no canto superior direito, em cada cena, faz uma imagem nova para o take que está tocando, onde este PC consegue fazer imagens. Ele pulsa enquanto a imagem é feita, e a nova assume quando fica pronta.
- **Letra na tela:** pressione **L** ou clique em **Letra** para mostrar ou esconder o painel de letra independente e rolável. Arraste-o pela barra de cima para tirá-lo do caminho; ele fica onde você o puser, e um clique duplo na barra o devolve ao lugar.
- **Fita do miniplayer:** enquanto o visualizador completo está fechado, um minivisualizador reativo de onda dupla toca dentro da barra de transporte de baixo. Liga e desliga em **Configurações → Aparência**.

### Playlists e curtidas {#playlists-liked-songs}

Clique em **Playlists** na barra de cima para passar para a vista Playlists.

- **Layout em duas colunas:** a coluna da esquerda lista suas playlists junto com a playlist de sistema fixada **Curtidas**, com o total de músicas. A coluna principal mostra o cabeçalho da playlist ativa (capa em alta resolução, título, descrição, total de músicas e duração) e a tabela de faixas.
- **Sincronização automática das curtidas:** qualquer take marcado com estrela na biblioteca, em qualquer espaço, aparece automaticamente na playlist de curtidas. Tirar a estrela o remove dela.
- **Adicionar a uma playlist:** pressione **P** ou clique no ícone **Playlist** de qualquer cartão para abrir o seletor de playlists, marcar ou desmarcar a participação em playlists, ou criar uma nova. **Esc** fecha o seletor.
- **Ordenação e busca interativas:** clique em um cabeçalho de coluna (**Título**, **Duração** ou **Incluída**) para ordenar com indicador de direção e inverter a ordem com um clique, e filtre as faixas com a caixa de busca.
- **Ir ao espaço na biblioteca:** clique no título de uma música na tabela de faixas para passar na hora para a vista Biblioteca, abrir o espaço onde esse take vive e destacar o cartão dele.
- **Atalhos nas playlists:** os atalhos próprios dos takes são ignorados na vista Playlists para evitar mudanças acidentais, exceto **M** (rack de masterização), que age sobre a faixa que está tocando ou carregada, além dos controles de transporte habituais (**Espaço**, setas, **?** e **L**).
- **Reprodução contínua e aleatória:** clique em **Tocar** no cabeçalho da playlist para ouvir a partir da faixa 1, ou em **Aleatório** para uma ordem aleatória. A reprodução passa automaticamente para a próxima faixa da playlist quando cada música termina.

### Atalhos de teclado {#hot-keys}

Na página principal, teclas simples agem sobre o **take escolhido**: o do painel esquerdo. Clique no cartão dele para
escolhê-lo. Cada tecla faz o que o botão dela faz, então uma tecla que excluiria pergunta antes, e um take
que não pode fazer o que uma tecla pede (Variações em um take sem partitura, por exemplo) deixa uma linha na barra
de status dizendo por quê.

| Tecla | Faz |
|---|---|
| Espaço | tocar ou pausar |
| Esquerda, Direita | voltar ou avançar cinco segundos |
| Shift+Esquerda, Shift+Direita | o take anterior ou próximo; na vista Playlists, a música anterior ou próxima da playlist |
| Cima, Baixo | volume |
| M | abrir o rack de masterização do take; de novo para fechá-lo |
| E | abrir o take no editor |
| I | os detalhes do take: tudo com que ele foi feito, em palavras, com **Copiar** |
| N | normalizar o take, ou desfazer se estiver normalizado |
| V | abrir ou fechar o visualizador enquanto toca, ou Variações quando parado |
| T | Tentar mais |
| S | pôr ou tirar a estrela do take |
| P | adicionar o take a uma playlist |
| D | excluir o take, depois de perguntar, como a lixeira dele |
| L | os registros; ou mostrar a letra com o visualizador aberto |
| B | no visualizador, o que se move atrás de uma cena sobre a imagem do take |
| F | tela cheia |
| ? | mostrar ou esconder os atalhos; de novo para fechar |
| Escape | fechar a janela da frente: o visualizador, os registros, o rack de masterização sobre o editor, e depois o editor ou qualquer outra janela |

As teclas de letra não fazem nada enquanto você digita em uma caixa, enquanto há uma janela aberta na frente, ou com Ctrl,
Alt ou a tecla Windows ou Command pressionada, para que os atalhos do próprio navegador (Ctrl+L, Ctrl+S e os outros)
continuem funcionando. A dica de um botão nomeia a tecla dele, como em **Variações (V)**. Pressione **?** a qualquer momento para ver a lista de atalhos.

Na janela do editor, Espaço e as setas controlam o player da janela, para o take aberto ali, sempre que o player
estiver à vista: em cada etapa, e com o rack de masterização aberto por cima. Elas nunca agem enquanto você digita em uma caixa,
e as teclas de letra são só da página principal. O piano roll tem as próprias teclas: veja [O piano roll](#the-piano-roll).

---

## Configurações {#settings}

Clique em **Yeufonic** no canto superior esquerdo. As configurações são salvas no servidor, então seguem você para qualquer
navegador e sobrevivem a uma reconstrução: o formato de áudio de saída para os stems e para salvar um take, o
modelo de separação, onde os stems são escritos, se os checkpoints de treinamento são mantidos, e como se
verifica que os instrumentais não cantam.

### Armazenamento {#storage}

**Configurações → Armazenamento** mostra para onde vai o espaço em disco do Yeufonic e deixa você recuperar parte dele. Treinar um
corpus deixa muitos arquivos que não serão mais necessários: cópias feitas para o motor enquanto as músicas eram analisadas,
o conjunto de treinamento (cada música reescrita como FLAC sem perdas, maior que o original), e os checkpoints
salvos no caminho. A janela lista cada um com o tamanho, **o que é** e **o que custa
removê-lo**, e remove só o que você marcar, depois de uma última confirmação. **Marcar os que não custam nada** marca
as cópias que simplesmente são refeitas quando necessário.

As músicas analisadas daqui em diante guardam a voz separada como FLAC, o mesmo áudio em mais ou menos metade do espaço. A
janela pode **converter as vozes WAV que você já tem**: cada uma é convertida, verificada para decodificar exatamente no mesmo
áudio, e só então o WAV é removido. Roda em segundo plano e pode ser interrompido.

Os checkpoints de treinamento merecem uma segunda olhada antes de saírem: cada um é uma entrada da lista de LoRAs de estilo que
você pode escolher para takes novos, então remover os checkpoints de um corpus tira essas entradas da lista para sempre. O
LoRA concluído fica e continua funcionando. O conjunto de treinamento de um corpus é diferente: removê-lo deixa o LoRA e os
checkpoints dele na lista, e só treinar esse corpus de novo precisa dele.

Seus takes, músicas, LoRAs concluídos e modelos nunca aparecem para remoção. Tudo o que pertence a um corpus que está sendo
treinado, exportado ou analisado aparece esmaecido e não pode ser tocado até terminar.

Abaixo, **Arrumar automaticamente** escolhe o que o Yeufonic remove por você: as cópias de trabalho de cada música
quando a análise dela termina (ligado por padrão), o conjunto de treinamento quando um LoRA foi treinado (desligado por padrão; o corpus
então precisa de outro **Exportar** antes de poder treinar de novo), e os checkpoints de treinamento (mantidos por padrão).

As imagens e o cache de build do Docker ficam fora do Yeufonic e não são cobertos aqui; `docker system df` os mostra.

### O modelo YuE2 {#the-yue2-model}

O YuE2 vem em dois tamanhos, e uma instalação tem um: **qualidade total**, que recomendamos, ou **pouca
memória**, uma cópia menor para placas de vídeo com pouca memória de vídeo. **Sobre**, no mesmo menu,
diz qual você tem. Ele é escolhido ao instalar o Yeufonic, não aqui:

- **No Windows**, rode o instalador de novo. A página de componentes dele oferece os dois tamanhos e marca os
  já baixados. Trocar baixa o outro na primeira vez e mantém os dois, então voltar
  não baixa nada.
- **Com Docker**, `sh scripts/fetch-models.sh` baixa o de qualidade total e
  `sh scripts/fetch-models.sh --int8` o de pouca memória. Com os dois arquivos em `models/checkpoints`, o
  app usa o de qualidade total a menos que `YUE2_CHECKPOINT=int8` esteja em `.env`.

Experimente o de pouca memória se os renders estiverem muito lentos ou o motor ficar sem memória de GPU. Treinar um LoRA funciona
com os dois tamanhos de modelo. O ajuste **Treino com o modelo de pouca memória (int8)** escolhe qual: desligado, o treinamento usa
o modelo de qualidade total; ligado, usa o modelo com que o app renderiza. Começa ligado quando só o modelo de pouca
memória está instalado. O README no GitHub tem uma seção, *Choosing a model size*, com o que esperar de cada um.

O Yeufonic também pode usar o motor **yue2.cpp** em vez do ComfyUI, para placas de vídeo com menos memória,
escolhido na configuração: na página de componentes do instalador do Windows, ou com Docker por
`sh scripts/fetch-models.sh --cpp`. **Sobre** diz que motor está rodando, e o cartão de um take qual motor o renderizou. Ele faz músicas, covers e
instrumentais e transcreve gravações, com seus LoRAs de estilo; o Gemma pode rascunhar letras e descrever imagens
ao lado dele (com Docker, `--gemma`), e o FLUX.2 klein desenhá-las (`--pictures`). Treinar precisa do motor
ComfyUI: com o yue2.cpp os corpus e o treinamento não são oferecidos. A página
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) no GitHub tem a
lista completa, e como trocar.

**Procurar uma versão nova** é a única coisa aqui que usa a internet por conta própria: a cada
quatro horas o app pergunta ao yeufonic.com se saiu uma versão mais nova, e avisa com uma pílula ao lado da
versão no canto superior direito. Essa pílula dá o instalador, ou, para uma cópia Docker, os dois comandos
que a atualizam. É uma requisição e nada mais sai do computador; **Não verificar** a
desliga. **Procurar atualizações** no menu pergunta na hora, esteja isto ligado ou não, e responde no
menu: que versão você tem, e se é a mais recente.

Quando há uma mais nova, o menu oferece **Obter x.y.z**, que baixa o instalador em uma instalação Windows ou põe os dois comandos na área de transferência para uma cópia Docker.

**Tema** define a aparência do app. Muda na hora, e cada navegador lembra, para a página abrir com ele.

| Tema | Aparência |
|---|---|
| **Escuro** | A aparência escura própria do app. |
| **Claro** | Painéis claros; os painéis do rack de masterização são prata escovada, enquanto os botões, as janelas dos medidores e os mostradores mantêm o visual escuro do hardware. |
| **Igual ao computador** | Segue o claro ou escuro do seu sistema, e muda junto. |
| **Estúdio** | Um escuro quente com âmbar. |
| **Alto contraste** | Preto e branco, com contornos fortes. |

A janela de registros fica escura em todos os temas, como um terminal, e o rack de masterização também segue o tema.

**Cor do fundo**, sob Tema, tinge a página atrás dos takes com uma cor que você escolher: marque **Tom**, depois
mova **Matiz** pela roda de cores e **Intensidade** de um véu leve a uma cor intensa. A página muda enquanto
você arrasta, e a escolha é salva quando você solta. Os cartões dos takes, os painéis e as janelas mantêm as próprias
cores, e o tema de alto contraste continua preto.

### LLM externo {#external-llm}

O Yeufonic pode escrever rascunhos de letra, transcrever gravações, marcar as seções das músicas e analisar os estilos dos corpus com um LLM externo em vez do modelo Gemma local.

Usar um LLM externo tem duas vantagens claras:
- **Poupa memória de GPU:** evita carregar o modelo Gemma 4 na VRAM da GPU (poupando cerca de 8 GB de memória de vídeo), deixando sua placa de vídeo totalmente livre para o planejamento e o render de áudio do YuE2.
- **Rascunhos e análises mais ricos:** modelos grandes na nuvem costumam rascunhar letras com mais nuances e produzir tags de estilo detalhadas para seus corpus.

**Provedor recomendado:** recomendamos escolher um provedor de LLM externo cuja API não tenha cobrança, se você tiver um disponível — o **Google Gemini** é um bom exemplo. A API do Gemini (pelo Google AI Studio) oferece um nível gratuito generoso sem cobrança, suporta os endpoints padrão compatíveis com OpenAI (`https://generativelanguage.googleapis.com/v1beta/openai/`) e aceita áudio diretamente para transcrever gravações.

Se você usa uma API medida ou paga por token (como os níveis pagos da OpenAI ou da Anthropic), analisar um corpus inteiro com dezenas de músicas ou gerar descrições para muitos takes pode consumir rapidamente créditos de API ou acionar limites de gasto. Se uma API externa devolver um erro de cota ou de limite de taxa (HTTP 429), o Yeufonic mostra um aviso e deixa você passar para modelos locais pelo resto da sessão, para que os outros trabalhos continuem sem interrupção. Um provedor sem cobrança evita custos inesperados.

**Configurar:**
1. Abra **Yeufonic → Configurações → LLM externo e letras**.
2. Ponha **LLM para escrever letras e tags de estilo** em **LLM externo (API compatível com OpenAI)**.
3. Digite a **URL da API**, a **chave de API** e o **modelo** do seu provedor (por exemplo, o modelo `gemini-2.5-flash` ou `gemini-1.5-flash` com a URL base compatível com OpenAI do Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Clique em **Testar a conexão com o LLM** para verificar suas credenciais.
5. Se o modelo escolhido aceita entrada de áudio (como o Gemini), você também pode pôr **Letra a partir de uma gravação** em **LLM externo** para que ele ouça as vozes separadas.

---

## Usar o Yeufonic a partir de um agente de IA (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

O Yeufonic pode funcionar como **servidor MCP**. Isso permite que um agente de IA no mesmo computador, como o Claude Code ou o Cursor, o use por você:
pedir uma música, um cover ou um instrumental, esperar por ele, tocá-lo, tentá-lo de outro jeito, dar-lhe uma imagem, pô-lo em uma playlist e
arrumar a biblioteca, tudo com suas próprias palavras (“faça um instrumental EDM de um minuto no espaço EDM e toque”). O agente faz o que a página faz, pelos mesmos caminhos, então um take que ele começa é um
take comum na sua biblioteca.

### Configurar {#setting-it-up}

1. **Ligue.** Abra Configurações e ponha **Servidor MCP** em **Ligado**. Vem desligado por padrão, porque uma requisição pode começar trabalho na GPU.
2. **Conecte seu agente** ao endereço do app com `/mcp` no fim: o endereço em que você abre o Yeufonic, por exemplo
   `http://localhost:8090/mcp`. No Claude Code:

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Outros clientes aceitam o mesmo endereço como servidor HTTP. Os que leem um arquivo de configuração costumam querer algo como
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. Não é preciso login nem chave.
3. **Peça.** Inicie seu agente a partir de qualquer pasta e descreva o que você quer.

**Que endereço?** É o endereço em que você abre o Yeufonic, com `/mcp` no fim.
- **Docker:** `http://localhost:8090/mcp`.
- **A instalação Windows:** a porta do app está em `settings.ini` (`app_port`, 8090 a menos que você a tenha mudado, por exemplo para rodar ao lado de
  uma cópia Docker). Com `app_port = 8091` é `http://localhost:8091/mcp`.
- **Agente no WSL, app no Windows:** isso não conecta. O app Windows só escuta no endereço de loopback do próprio Windows, que o WSL não consegue
  alcançar (Docker dentro do WSL funciona, porque também está no WSL). Rode o agente pelo Windows (PowerShell ou a versão Windows do
  seu agente), ou ligue a rede espelhada do WSL (`networkingMode=mirrored` sob `[wsl2]` em `.wslconfig`, e depois `wsl --shutdown`),
  que faz `localhost` ser o mesmo dos dois lados.

Se seu agente disser que o servidor **precisa de autenticação**, quase sempre é porque o ajuste ainda está desligado: ligue-o, e depois
reconecte o agente (no Claude Code, `/mcp`). Reconecte também depois de reiniciar o Yeufonic, porque um reinício corta a conexão.

### O que você pode pedir {#what-you-can-ask-for}

| Peça | O que acontece |
|---|---|
| “Liste meus últimos takes”, “mostre os takes do espaço EDM” | Lista os takes, os mais novos primeiro, com um id curto, quando cada um foi feito, a duração e o estilo |
| “Faça um instrumental de um minuto no estilo synthwave” | Planeja e renderiza um instrumental. Uma duração, um espaço e um [LoRA de estilo](#style-loras) podem ser nomeados |
| “Faça uma música no estilo folk com esta letra” | O mesmo para uma música, a partir da letra que você der |
| “…com harmonia ousada, interpretação controlada, em fá sustenido, a 100 BPM” | Qualquer ajuste de um take novo com os nomes que a página usa: [Harmonia](#harmony), [Variedade do plano](#plan-variety), a [interpretação](#interpretation), fixar tom e andamento, e para uma música **Seguir esta estrutura exatamente** e **As vozes seguem as indicações**. Se nada for dito, um take novo começa onde o da página começa: Variada e Ampla |
| “Escreva uma letra sobre um trem noturno, em tom falado” | O **Escrever letra** do próprio app, com as formas de música, linhas por seção e tons dele. O agente também pode escrever a letra por conta própria |
| “Faça um cover de *a gravação* no estilo jazz” | Faz um cover a partir de uma gravação que já está na sua biblioteca. Precisa de uma partitura (transcreva-a antes no app). Sem letra sua, usa as palavras ouvidas na gravação |
| “Que vozes eu tenho?”, “cante com a minha voz Night Singer, um pouco mais grave” | Lista suas vozes gravadas e faz uma música ou cover cantada com uma delas, ou renderiza um take de novo com uma, com configurações próprias para esse take (formante, mistura, semelhança e o resto), como as **configurações** da voz no editor |
| “Toque” | Abre o take no seu navegador, onde ele toca |
| “Ponha estrela nesse”, “chame de Sunrise”, “mova para o espaço Folk” | Põe estrela, renomeia ou move um take |
| “Renderize de novo com uma seed nova”, “pare isso” | Renderiza um take de novo, ou cancela um em andamento |
| “Me dê mais alguns como esse” | Renderiza o take de novo com seeds novas, como vários takes novos para ouvir juntos |
| “Cante de novo”, “tente em cada interpretação” | **Cantar de novo** (uma voz nova para a mesma partitura) ou **Variações** (a mesma partitura e seed, tocadas de cada jeito). As variações são guardadas dentro do take, como Tentar mais |
| “Cante essa melodia com esta letra” | **Letra nova**: a mesma melodia, tom e andamento com outra letra, como take novo |
| “Faça um instrumental com ela” | A mesma partitura com a melodia em um instrumento e sem canto, como take novo |
| “Escreva um plano novo para ele, mais animado” | Um plano novo para um take que ainda não tem áudio (planejado sem render, ou cujo plano falhou). Um take com áudio não é tocado: peça um take novo em vez disso |
| “Tire o solto para fora” | **Tirar**: um take guardado dentro de outro vira um take próprio |
| “Dê uma imagem a ele” | Faz uma imagem nova para o take, como o botão **Imagem** do editor, e dá um link que a abre. Uma imagem desenhada neste computador espera até nenhuma música estar sendo feita |
| “Ponha os três melhores em uma playlist chamada Road trip” | Cria playlists, mostra o que elas têm, e adiciona ou remove takes. Pôr um take em **Curtidas** põe estrela nele |
| “Ache um estilo synthwave”, “salve esse estilo como Night drive” | Busca entre seus estilos salvos e os embutidos, e salva um estilo com um nome para o menu de estilos |
| “Crie um espaço chamado Drafts” | Cria um espaço novo para guardar takes |
| “Transcreva *a gravação*” | Transcreve uma gravação em partitura, para poder fazer um cover. Deixa em paz uma gravação que já tem partitura, a menos que pedido |
| “Separe isso em voz e instrumentos” | Separa um take pronto nas partes dele (quatro, seis, ou só voz e instrumentos) e dá um link para cada arquivo e outro para o conjunto inteiro em zip |
| “Salve a receita desse take”, “…e o take junto, num zip MP3” | Dá a receita do take (o que o fez, não o áudio) para mostrar, mudar ou guardar como arquivo, com links para baixá-la sozinha ou com o áudio num só zip |
| “Importe *Night Ferry.yeufonic.json* em Drafts e renderize” | Um take novo a partir de um arquivo de take, com o plano, renderizado quando você pedir. Diz quais LoRAs citados no arquivo não estão instalados, e quando um cover chegou como música |
| “Importe de novo num estilo dream pop, mesma partitura e seed” | Muda a receita antes de importá-la, então só muda o que você citar |
| “Qual motor fez esse take?”, “qual motor está rodando?” | Diz qual motor renderizou um take, e qual o Yeufonic usa agora (ComfyUI ou yue2.cpp) |
| “O Yeufonic está ocupado?” | Diz se o motor está pronto, o que está rodando e com que progresso, o que espera, e se um LoRA está sendo treinado |
| “Exclua esse take” | Mostra o que sairia e pergunta antes; veja abaixo |

Fazer um take leva minutos. O agente o começa e espera, informando o progresso, então você pode pedir a próxima coisa enquanto isso.

### Como pode ser: um exemplo {#how-it-can-work-an-example}

Uma conversa, de uma ideia a uma playlist. Você fala; o agente escolhe as ferramentas (a coluna do meio está aí só para mostrar o que
acontece) e diz o que voltou.

| Você diz | O agente | O que você recebe |
|---|---|---|
| “Escreva uma letra sobre a última noite de um faroleiro, estilo folk, forma de história. Depois faça uma música com ela em um espaço novo chamado Coast.” | `write_lyrics`, `create_space`, `make_song`, depois `wait_for_take` até terminar | A letra, intitulada *The Last Light*, mostrada a você; um espaço chamado Coast; uma música planejada e renderizada lá, com o progresso ao longo do caminho |
| “Toque.” | `get_take`, depois abre o `listen_url` dele | Toca no seu navegador |
| “Boa melodia. Tente mais solta e inquieta, e me dê uma sem canto.” | `make_variations` com solta e inquieta, `instrumental_from_take` | Dois takes dentro da música, e um instrumental ao lado dela |
| “Mostre o que temos.” | `list_takes` em Coast, e com `inside` para a música | Uma lista com um id curto para cada um, para você poder dizer “3f9a” em vez de um título |
| “Tire 3f9a para fora, ponha estrela e dê uma imagem.” | `take_out`, `star_take`, `make_picture` | O solto como take próprio, com estrela (então também nas curtidas), com um link para a imagem dele |
| “Ponha esse e o instrumental em uma playlist chamada Coast demos.” | `create_playlist`, `add_to_playlist` | Uma playlist com os dois |
| “Salve o estilo como Coastal folk.” | `save_style` | **Coastal folk** no menu de estilos do app, pronto para a próxima vez |
| “Agora um dueto: esta letra, com indicações [male voice] e [female voice], cada seção como está escrita.” | `make_song` com `follow_structure` (um plano novo, porque as seções mudam) | Uma música nova que planeja exatamente suas seções, em ordem, com cada linha indicada movida para onde essa voz canta |

Tudo o que ele fez está na biblioteca como se você tivesse feito na página: abra qualquer take no editor, masterize, ou continue de lá.
Quando uma etapa não pode ser feita, o agente recebe o motivo do próprio app (“this take is an instrumental already”, “nothing here can draw a
picture”) e o repassa, então você ouve a mesma resposta que a página daria.

### Tudo o que ele pode fazer {#everything-it-can-do}

Você não precisa destes nomes: pede com suas próprias palavras e o agente escolhe. Eles estão aqui para você ver o que existe, e para poder
dizer ao seu agente qual quer.

| Ferramenta | O que faz |
|---|---|
| `list_takes` | Lista os takes, os mais novos primeiro, opcionalmente só os que batem com algumas palavras, em um espaço nomeado, ou com estrela. Mostra um id curto |
| `get_take` | Um take completo: como foi feito, o estado, qualquer erro e, quando tem áudio, um link que o toca. Pode incluir a partitura |
| `wait_for_take` | Espera (até mais ou menos um minuto por vez) um take que está sendo feito, e diz se terminou |
| `make_instrumental` | Planeja e renderiza um instrumental a partir de um estilo, com uma duração, um espaço e um LoRA de estilo se você os nomear, e seções se você as der |
| `make_song` | O mesmo para uma música, a partir de uma letra |
| `make_cover` | Um cover a partir de uma gravação da biblioteca, com a partitura dela e, a menos que você dê outras, a letra dela |
| `try_more` | Vários takes a mais a partir de um existente, com seeds novas |
| `sing_again` | A mesma partitura cantada de novo com uma seed nova: uma voz nova, como take novo |
| `make_variations` | A mesma partitura e seed em cada interpretação nomeada (ou em todas), guardadas dentro do take |
| `new_words` | A mesma partitura cantada com outra letra, como take novo |
| `instrumental_from_take` | A mesma partitura como instrumental, como take novo |
| `replan_take` | Um plano novo para um take sem áudio, opcionalmente com outra Harmonia, Variedade do plano, tom ou andamento |
| `take_out` | Transforma um take guardado dentro de outro em um take próprio |
| `write_lyrics` | Uma letra a partir de um pedido, com uma forma e um tom de música, escrita como Escrever letra faz na página |
| `render_take` | Renderiza um take planejado, ou renderiza de novo um pronto (com uma seed nova se pedido) |
| `cancel_take` | Para um take na fila ou em andamento |
| `make_stems`, `get_stems` | Separa um take em partes, e depois lista as partes com um link para cada uma e para o conjunto inteiro em zip |
| `list_recordings`, `transcribe_recording` | Mostra as gravações da biblioteca e se cada uma tem partitura; transcreve a que não tem |
| `list_style_loras` | Os LoRAs de estilo instalados, com as palavras-gatilho e as forças salvas com eles |
| `list_voices` | Suas vozes gravadas, se cada uma está pronta e seus padrões. `make_song`, `make_cover` e `render_take` recebem uma pelo nome, com configurações próprias para esse take; `get_take` diz qual voz cantou um take |
| `list_spaces`, `move_take`, `create_space` | Os espaços e o que cada um contém; move um take para outro; cria um espaço novo |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | As playlists e os takes de uma; cria uma; põe ou tira takes |
| `make_picture` | Uma imagem nova para um take, com um link que a abre. `get_take` também dá o link para a imagem de um take |
| `list_styles`, `save_style` | Seus estilos salvos e os embutidos, buscados por palavras; salva um estilo com um nome |
| `star_take`, `rename_take` | Põe ou tira a estrela de um take; muda o título dele |
| `delete_take` | Exclui um take para sempre, depois de mostrá-lo a você e receber seu ok |
| `save_take_recipe` | A receita de um take, com links para baixá-la sozinha ou com o áudio num só zip, no formato pedido |
| `import_take` | Um take novo a partir de uma receita, num espaço se citado, pronto para renderizar; diz quais LoRAs não estão instalados e quando um cover chegou como música |
| `status` | Se o motor está pronto, o que roda e o que espera, e se um LoRA está sendo treinado; diz qual motor está em uso (ComfyUI ou yue2.cpp) |

### Ideias de uso {#ideas-for-using-it}

- **Um lote de ideias, e depois escolher.** “Faça cinco instrumentais EDM de um minuto em estilos diferentes, no espaço EDM.” Ele os começa um depois
  do outro e avisa à medida que cada um termina. Você ouve, e então diz “ponha estrela no segundo e no quarto e exclua o resto”.
- **Iterar sobre uma ideia.** “Faça um instrumental em um estilo de sintetizador sonhador e toque”, depois “agora o mesmo com mais bateria”, e
  “me dê mais quatro como o segundo”. O agente acompanha qual take é qual, então você pode falar deles pela posição ou
  pelo que disse sobre eles.
- **Covers sem ficar clicando.** “Transcreva *a demo*, e depois faça três covers: folk, synthwave e jazz.” Ele transcreve
  primeiro a gravação se ela não tiver partitura, e depois faz os covers no espaço que você nomear.
- **Trabalhar com um LoRA.** “Liste meus LoRAs de estilo, e depois faça um instrumental com o de jazz.” A palavra-gatilho e as forças salvas são
  cuidadas por você, coisa fácil de errar à mão.
- **Letra do agente, ou do app.** O agente pode escrever a letra por conta própria: “Escreva uma letra sobre um trem noturno e faça uma música
  com ela no estilo folk.” O Yeufonic só vê a letra pronta. Ou peça a do app: “use o autor de letras do Yeufonic, forma hip-hop,
  tom falado”, que a escreve como **Escrever letra** faz na página e a devolve para uma música.
- **Mesma melodia, outra letra.** “Cante isso de novo com esta letra para o segundo verso”: `new_words` mantém a melodia, o tom e o andamento,
  onde uma música nova a partir da letra escreveria uma melodia nova.
- **Comparar ajustes.** “Faça a mesma música duas vezes, uma com harmonia Familiar e outra com Aventureira, com a mesma seed”, e depois
  “agora dê à melhor cada interpretação”. Os ajustes são pedidos pelo nome, então você pode montar um pequeno teste em uma frase.
- **Playlists a partir da audição.** “Ponha todos os takes com estrela desta semana em uma playlist chamada Week 43”, ou “tire os instrumentais de
  Road trip”. Curtidas são os takes com estrela, então a estrela e as curtidas são sempre a mesma lista.
- **Stems para um lote inteiro.** “Separe meus cinco takes mais novos em voz e instrumentos e me dê os links.” Eles entram na fila um atrás
  do outro, e atrás de qualquer render que a GPU esteja rodando.
- **Arrumar a biblioteca.** “Ache os takes com o mesmo título, me diga qual é o mais novo, e exclua os mais antigos”, ou “mova tudo
  o que eu fiz hoje para um espaço chamado Drafts”. Ele trabalha com ids e pergunta antes de excluir.
- **Verificar antes de um trabalho longo.** “O Yeufonic está ocupado?” antes de pôr na fila um render longo ou um lote, para não ficar atrás de um treinamento.
- **Parte de uma tarefa maior.** Como é uma ferramenta que o agente pode chamar, pode fazer parte de algo maior: fazer uma faixa para um vídeo e
  escrever a nota que a acompanha, ou montar um lote do tamanho de uma playlist e nomear os takes por uma lista.

O agente não consegue ouvir um take, então não pode julgar como ele soa: você ouve, e ele faz o trabalho pesado. Também não é um
atalho para pular o motor: a GPU continua fazendo um trabalho por vez, então um lote grande é uma fila longa.
- **Compartilhar um take.** “Salve meu take com estrela com sua receita num zip FLAC” dá um arquivo que outra pessoa pode ouvir e refazer:
  ela pede ao agente dela para “importar este arquivo de take e renderizar”. Ou “importe de novo com o LoRA de jazz, mesma partitura e
  seed”, para ouvir o mesmo plano de outro jeito.

### Vale saber {#things-to-know}

- **Takes podem compartilhar título,** então o agente trabalha com o **id** de um take e mostra um curto (a coluna `short_id`) quando lista takes.
  Você pode nomear um take pelo começo do id dele, quatro caracteres ou mais, desde que só um take comece assim. Se forem dois, ele avisa
  e pede mais.
- **Excluir pergunta duas vezes.** O agente mostra primeiro o que excluiria, inclusive qualquer outro take com o mesmo título, e só exclui
  quando você diz sim. Um take com estrela precisa que você diga explicitamente. Um take excluído, com o áudio dele, não pode ser recuperado.
- **Espaços e LoRAs de estilo são nomeados,** não numerados: “no espaço EDM”, “com o LoRA de jazz”. Um nome que não bate com nada recebe a lista
  do que existe, e nada é criado. A palavra-gatilho de um LoRA é acrescentada ao estilo por você, já que um LoRA faz muito pouco sem ela.
- **Um take novo começa onde o da página começa:** Harmonia em Variada e a interpretação Ampla, a menos que você nomeie outras. Em um motor
  sem o nó de harmonia ele começa em Familiar, já que a Harmonia não pode subir mais ali.
- **Imagens e letras esperam a vez.** Uma imagem desenhada ou descrita neste computador espera até nenhuma música estar sendo feita, e letras
  escritas neste computador entram na fila com o resto do trabalho de GPU, então o agente pode dizer “ainda está sendo feito” e olhar de novo depois.
- **Um instrumental é sempre planejado com uma estrutura com tempos,** calculada a partir da duração que você pede (cerca de dois minutos e meio
  se você não disser nada). Sem tempos, o planejador escreve planos longos demais para usar. Nomeie suas próprias seções e elas são usadas como estão.
- **Só neste computador.** As mesmas verificações de nome de host e de origem da página se aplicam, e não há login, então desligue o ajuste
  quando não o estiver usando, e não exponha a porta a uma rede em que você não confia.

## Registros do sistema {#system-logs}

O app escreve um registro consolidado em tempo real de cada ação importante — planejamento de partitura, render, transcrição de áudio, separação de stems e treinamento de LoRA — com os prefixos `INFO`, `WARN` e `ERROR`.

- **Console no navegador:** clique no botão **Registros** da barra de cima (ou pressione **L**) para abrir um console flutuante, que pode ser arrastado e redimensionado. Ele fica aberto sem bloquear a página, o que deixa você pôr takes na fila e acompanhar a geração em tempo real.
- **Janela separada:** clique em **↗ Destacar** no cabeçalho do console (ou vá direto a `/logs`) para abrir uma janela dedicada aos registros.
- **No terminal:** os registros giram automaticamente em `data/logs/yeufonic.log` no host, onde você pode acompanhá-los ao vivo:
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## A página do próprio motor {#the-engine-s-own-page}

O motor é o ComfyUI (a menos que esta instalação use o yue2.cpp, cuja página é uma simples bancada de testes), e a interface própria dele é acessível: <http://localhost:8189> com Docker, ou
<http://localhost:8188> com a instalação Windows (o `engine_port` em `settings.ini`). Ela só responde
nesta máquina, sem login.

- **É o mesmo motor e a mesma GPU do app.** Um trabalho rodado ali aparece na fila do app como vindo
  de fora, e os trabalhos do próprio app esperam por ele.
- **O histórico dele mostra cada grafo que o app enviou**: o plano, o render e as transcrições, com
  cada ajuste como o motor o recebeu. É um bom lugar para ver exatamente a partir do que um
  take foi feito.

---

## Quando algo dá errado {#when-something-is-wrong}

**O cabeçalho diz que o motor está faltando.** O app funciona sem ele e diz isso. Os renders esperam.
Verifique se o contêiner do motor está rodando.

**Uma música não termina.** Geralmente força demais do planejador. Baixe o Planejador do LoRA para 0.5. O
limite de duração vai pará-la de qualquer jeito.

**Um LoRA parece não fazer nada.** Verifique se a palavra-gatilho está no Estilo, e se a força que
você aumentou é uma que o arquivo realmente tem — o seletor esmaece a outra.

**Um take diz *Render fraco*.** Ele saiu muito mais baixo que o normal do começo ao fim. Alguns takes
assim são só baixos; outros soam finos ou distorcidos. Clique no aviso para normalizá-lo, o que
o leva ao volume habitual e o marca *Normalizado*. Se ainda soar mal, tente outra
seed, e mantenha o Som desse LoRA em 0.5 ou menos. Acontece sobretudo em covers por meio de um LoRA de estilo
treinado aqui.

**Normalizar o volume.** Marque no editor e cada take feito enquanto estiver marcado é levado ao
volume habitual ao terminar, e marcado *Normalizado*. Um take feito sem isso pode ser normalizado
depois com o botão de alto-falante no topo do cartão dele. O arquivo como foi renderizado é guardado ao lado, e
clicar em *Normalizado* volta a ele. O quão alto ele fica é definido em Configurações, em *Normalizar para*.
Desmarcado, um take mantém o nível com que foi renderizado.

**Um instrumental cantou.** Veja *Quando um instrumental canta* acima. É uma falha do modelo; uma seed nova
costuma resolver.

**Um take não renderiza de novo.** Talvez a gravação dele tenha sido excluída. Os covers mantêm o áudio e a
partitura, mas não podem ser renderizados de novo a partir de uma gravação que não existe mais.

**Nada toca, mas a forma de onda se move.** Verifique o controle de volume e se um stem não está selecionado —
o player segue o último em que se clicou.
