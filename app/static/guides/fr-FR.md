# Yeufonic — le guide

Ce guide porte sur l’**utilisation** de l’application. L’installation, et tout ce qu’il vous faut avant qu’elle tourne, se trouve dans le
[README](https://github.com/yeufonic/yeufonic#readme).

L’application écrit des chansons avec YuE2, un modèle qui travaille en deux temps : il écrit d’abord un **plan de partition** —
la mélodie, les accords et les sections, sous forme de texte — puis il **effectue le rendu** de ce plan en audio.
Presque tout ce qui suit découle de cette séparation. Un plan coûte quelques secondes et peut être lu, modifié et
jeté ; un rendu coûte des minutes. L’application vous laisse donc d’abord regarder le plan.

---

## Votre première chanson {#your-first-song}

1. Appuyez sur **+ Chanson** en haut du panneau de gauche. La fenêtre de l’éditeur s’ouvre.
2. **Saisissez un style.** Une phrase, pas une liste de tags : *« warm indie rock, expressive female lead, jangly
   guitars, 96 BPM »*. C’est l’influence la plus forte sur le résultat.
3. **Ajoutez des paroles**, ou appuyez sur **Écrire les paroles** et laissez Gemma les rédiger à partir d’une description.
4. Appuyez sur **Écrire le plan de partition**. La fenêtre se ferme et la prise apparaît dans le panneau de gauche. Si
   **Lancer le rendu dès que le plan est prêt** est coché à côté du bouton, comme au départ, le plan
   passe directement au rendu.

Pour lire le plan avant tout rendu, décochez d’abord **Lancer le rendu dès que le plan est prêt**. La
prise s’arrête alors à son plan : ouvrez-la, et sur sa page **Partition**, **Écrire un nouveau plan** retire une mélodie qui ne vous
plaît pas pour le prix de quelques secondes, et **Rendre cette partition** en fait le rendu. Une prise encore sans audio est
complétée ; une prise qui a déjà de l’audio est rendue en une nouvelle prise à côté, si bien qu’un rendu n’écrase jamais
une prise que vous voudriez garder.

La prise apparaît dans la bibliothèque à droite et se lit dans la barre du bas.

### Le panneau de prise et l’éditeur {#the-take-panel-and-the-editor}

Le **panneau de gauche** montre la dernière prise cliquée, en lecture seule : son style, ses réglages de son, les
premières lignes de ses paroles, et sa partition sous forme de tonalité, de tempo, de durée et des accords de chaque section.
**+ Chanson**, **+ Reprise** et **+ Instrumental** en haut commencent quelque chose de nouveau ; celui du
type de la prise est mis en valeur. Le chevron à côté du panneau le replie, pour que les prises aient la largeur,
et le fait revenir. Des touches seules agissent sur la prise que montre le panneau (M pour le rack de mastering, E pour
l’éditeur, etc.) : voir [Raccourcis clavier](#hot-keys).

Créer et modifier une prise se fait dans la **fenêtre de l’éditeur**. Son bouton principal dans le panneau dit ce qui
convient : *Modifier et relancer le rendu*, ou *Revoir le plan et lancer le rendu* quand un plan attend. Les boutons
**Partition** et **Encore** d’une carte l’ouvrent aussi, tout comme un double-clic sur une carte. Elle a trois
colonnes (la chanson, les paroles et le son), tout est visible, avec la partition dans un onglet à part.

Fermer la fenêtre, avec **Fermer**, la croix ou Échap, conserve ce que vous avez saisi.

Le bouton après **Fermer**, en haut à droite, fait occuper à la fenêtre toute la fenêtre du navigateur, et
un second clic la ramène à sa taille habituelle. La fenêtre s’ouvre comme vous l’avez laissée. En plein écran,
la colonne des paroles prend toute sa hauteur : la zone des paroles (dès qu’elle contient des mots) et la structure s’agrandissent dans
l’espace, et le lecteur reste au pied de la colonne.

La rangée du haut de la fenêtre reprend en plus grand les petits boutons de la carte de la prise : Chanter à nouveau, Variations,
Essayer encore, Contenu, Sortir, Normaliser et Déplacer, chacun là où la carte le montrerait. Normaliser est vert
tant que la prise est normalisée, et un clic la ramène alors au niveau de son rendu ; Contenu
s’allume tant que la prise en contient d’autres, et ferme la fenêtre pour les montrer sous la prise.

### Réglages avancés {#advanced-settings}

Le bouton **Avancé** dans l’en-tête de l’éditeur ouvre des réglages pour cette seule prise. La plupart des chansons
n’en ont jamais besoin. Ils sont enregistrés avec la prise, si bien que *Modifier et relancer le rendu* les retrouve comme vous les avez laissés.
Le bouton s’allume quand un réglage diffère de sa valeur par défaut, et **Rétablir les valeurs par défaut** les remet
tous.

Certains agissent sur le plan, d’autres sur le rendu et le fichier final :

- **Étapes de diffusion** (16–64, par défaut 32) : combien d’étapes fait le décodeur audio. Plus d’étapes allongent
  le rendu.
- **Suivre le style** (0–100, par défaut 1.0) : à quel point la musique suit le style et les paroles, le guidage
  de l’étape qui transforme la partition en son (CFG). Au-dessus de 1.0, elle s’en rapproche ; en dessous, elle s’en éloigne. La
  différence est subtile aux petites valeurs, et un rendu prend un peu plus de temps. Toute valeur acceptée par le moteur peut être
  saisie : un guidage très élevé sonne plutôt dur que plus fidèle. Il s’affiche quand le moteur le propose : yue2.cpp, ou le moteur ComfyUI
  dans sa version récente (reconstruisez un ancien moteur Docker pour l’obtenir).
- **Éviter :** des mots à éviter, comme « drums » ou « rap vocals ». Ils sont ajoutés au style
  sous la forme « avoid: … ». C’est une indication pour le planificateur, pas une garantie : le moteur de rendu n’a pas de prompt négatif.
- **Tonalité imposée :** le plan est transposé dans cette tonalité une fois que le planificateur l’a écrit. Le planificateur ignore
  une tonalité indiquée dans le style, donc cela se fait sur la partition elle-même : chaque note et chaque accord se décale du
  même intervalle et l’armure est réécrite. Un plan mineur reste mineur, et seule la tonique
  change. Un plan que l’application ne peut pas lire avec certitude, par exemple dans un mode ou avec un changement de tonalité
  en cours de route, reste dans la tonalité du planificateur, et le journal le signale.
- **Tempo imposé** (BPM) : le plan prend ce tempo, qui remplace tout tempo du style ou de la
  partition du planificateur, et le rendu le suit.
- **Limite de tokens de la partition** (par défaut 8192) : le maximum que le planificateur peut écrire. Une limite plus basse empêche le plan d’une chanson courte
  de s’éterniser.
- **Limite de tenue d'accord** (mesures, par défaut 8) : le nombre maximal de mesures que le planificateur reste sur une même fondamentale avant
  de devoir changer.
- **Bonus d'harmonie hors tonalité** (0–10, par défaut 0) : à quel point le planificateur est poussé vers des accords
  d’emprunt et des fondamentales hors de la tonalité. Ces deux réglages agissent sur les choix du planificateur, ils se voient donc comme
  une différence dans les accords du plan plutôt qu’à l’oreille. Comparez dans la fenêtre
  Partition.
- **Les voix suivent les repères** (une case sous la zone des paroles, affichée dès que les paroles ont une indication de voix comme
  `[male voice]` ; cochée pour une nouvelle prise) : la mélodie de chaque ligne indiquée est déplacée par octaves là où se chante la voix que
  nomme son indication. Voir [Les paroles](#the-words).
- **Suivre exactement cette structure** (une case sous la zone des paroles, pas dans Avancé ; chansons ; décochée par défaut) : le plan écrit exactement les sections que nomment les paroles, dans
  l’ordre, et aucune autre. Décochée, le planificateur façonne lui-même la chanson et ajoute souvent une intro, une outro ou un
  interlude, ou omet une section. Un plan peut tout de même finir avant la liste.
- **Les sections commencent différemment** (Suivre l’harmonie, Toujours, Jamais) : si une section peut commencer sur les mêmes
  accords que la précédente. *Suivre l’harmonie* l’active à partir de Coloré et le laisse désactivé en dessous ; *Toujours* et
  *Jamais* décident pour cette prise à n’importe quel niveau, pour comparer deux plans avec et sans.
- **Volume cible :** le niveau auquel une prise est normalisée. Il ne s’applique que si la normalisation est activée.
- **Durée du fondu de fin** (secondes, par défaut 3) : la longueur du fondu quand une prise est coupée à la limite de
  durée.

### Que mettre dans la zone Style {#what-to-put-in-the-style-box}

YuE2 lit ceci comme la description d’un enregistrement : décrivez donc un enregistrement. Langue, genre, voix,
instruments, ambiance, tempo et production, à peu près dans cet ordre, le tout en une phrase. Les simples listes de tags
fonctionnent moins bien, et les marqueurs de section comme `[Verse]` vont dans les paroles, pas ici.

Les puces **Chant** en dessous écrivent dans le style pour vous : femme, homme ou duo, et un caractère
comme soufflé ou rauque. C’est un raccourci de saisie, et vous pouvez modifier le résultat à la main.

### Rédiger les paroles {#drafting-the-lyrics}

**La structure.** Au-dessus de la zone des paroles, tant qu’elle ne contient pas de mots, une chanson a une **structure** à construire, comme
un instrumental : une liste de sections que vous pouvez réordonner, supprimer et compléter (intro, couplet, pré-refrain, refrain, pont,
interlude, outro). **Partir de…** la remplit avec une forme courante, et l’infobulle de chaque forme dit à quoi elle convient. Un
**interlude** est un passage instrumental : l’auteur met son tag sur une ligne à part, et le planificateur le joue avec
la voix instrumentale. **Mettre les sections dans la zone des paroles** insère les tags comme sections vides sous lesquelles écrire à la main.
Dès que la zone contient des mots, ce sont les paroles qui sont chantées et la structure s’efface.

**Écrire les paroles**, à côté de la zone des paroles, demande de quoi parle la chanson et écrit des paroles pour les sections que vous avez construites.
**Lignes par couplet ou refrain** fixe la longueur de chacune : plus de lignes dans une section donnent une chanson plus longue, car le
planificateur écrit à peu près autant de musique qu’il y a de mots. Le style au-dessus donne l’ambiance. Gemma rédige le brouillon sur le même
moteur, et il arrive dans la zone avec un titre si vous n’en aviez pas donné ; un [LLM externe](#external-llm) peut les écrire à la place, configuré dans les Paramètres. La fenêtre se ferme dès que la rédaction commence, et la progression s’affiche à côté de la zone des paroles.
Les boutons de l’éditeur de paroles ajoutent aussi ces sections, ainsi que des indications de voix (+ Homme, + Femme, + Les deux).

**Comment sonnent les lignes** fixe le rythme et la rime que vise l’auteur. *Naturel* (par défaut) mélange lignes courtes et longues
avec quelques rimes. *Rimes régulières* est la forme traditionnelle de lignes égales rimant deux à deux, c’est-à-dire ce
que produisait l’auteur avant ce choix. *Rythme parlé* est conversationnel, comme la parole ou le rap ; *Rimes
libres* ne fait rimer que certaines lignes ; *Court et percutant* et *Long et fluide* fixent la longueur des lignes.

C’est un premier jet. Les lignes ont du rythme et des rimes, mais un modèle se tourne vers des images familières, et rien
ne vérifie qu’une ligne n’appartient pas déjà à quelqu’un d’autre. Lisez-le et faites-le vôtre avant de planifier.

---

## Écrire une chanson à partir d’un prompt : toutes les options {#writing-a-song-from-a-prompt-every-option}

**+ Chanson** offre désormais beaucoup de choix. Aucun n’est obligatoire : un style et quelques paroles suffisent, comme dans
[Votre première chanson](#your-first-song). Ce chapitre les passe tous en revue dans l’ordre où l’éditeur les montre,
ses trois colonnes (la chanson, les paroles et le son), puis ce qu’il faut faire après le plan. Il se termine par un
tableau des souhaits courants, comme une chanson plus longue ou un refrain qui sonne autrement que le couplet.

### La chanson {#the-song}

- **Titre.** Facultatif. S’il est vide, la première ligne des paroles est utilisée.
- **Style.** La liste **Choisir un style…** contient 200 points de départ, de l’afrobeats au zydeco, par ordre alphabétique.
  En choisir un remplit la zone Style d’une description complète, que vous pouvez ensuite modifier. Les puces en dessous sont dix départs
  rapides pour une chanson : warm indie rock, soulful jazz-pop, synthwave, acoustic ballad, heavy rock, modern pop,
  country, hip hop, smooth R&B et dance pop. Voir [Que mettre dans la zone Style](#what-to-put-in-the-style-box).
- **Enregistrer votre propre style.** **Enregistrer**, à côté de la liste, garde le contenu de la zone Style sous un nom que vous lui
  donnez. La première entrée de la liste, **Styles enregistrés**, ouvre ceux que vous avez gardés ; la corbeille à côté en supprime un, et la
  recherche de la liste les trouve avec les 200. Enregistrer sous un nom déjà utilisé remplace ce style. Le mot déclencheur d’une
  LoRA de style n’est pas conservé, et il est remis pour la LoRA choisie quand vous utilisez le style.
- **Un tempo dans le style n’est qu’une indication.** Le planificateur choisit souvent le sien. Pour fixer le tempo, utilisez **Tempo imposé** dans
  Avancé.
- **Chant.** Les puces écrivent une voix (femme, homme, duo et un caractère) dans le style pour vous.
- **LoRA de style.** Sous la colonne du son. Voir [LoRA de style](#style-loras).

### Les paroles {#the-words}

**La structure.** Au-dessus de la zone des paroles, tant qu’elle ne contient pas de mots, il y a une liste de sections : l’ordre que
suivra la chanson. Chaque ligne peut être changée en une autre section, montée ou descendue (ou glissée), ou supprimée, et les
puces sous la liste ajoutent une section. Les sections sont intro, couplet, pré-refrain, refrain, pont, interlude et outro.
Un **interlude** est un passage instrumental : il n’a pas de paroles, et le planificateur le joue avec la voix instrumentale.
(`solo` n’est pas une section que connaît le planificateur ; l’interlude est la façon d’en demander un.)

**Partir de…** remplit la liste avec une forme courante. Survolez une option pour voir à quoi elle convient :

| Forme | Sections | Convient à |
|---|---|---|
| Couplet, refrain, pont | couplet, refrain, couplet, refrain, pont, refrain | la chanson classique : pop, rock, country |
| Courte | couplet, refrain, couplet, refrain | folk, punk, rock and roll des débuts |
| Intro et outro | intro, couplet, refrain, couplet, refrain, outro | ballades, soft rock, auteurs-compositeurs |
| Récit | couplet, couplet, refrain, couplet, refrain, outro | chansons narratives, folk, country |
| Pop avec pré-refrain | couplet, pré-refrain, refrain, couplet, pré-refrain, refrain, pont, refrain | pop moderne, dance-pop, pop rock |
| Accroche d’abord | refrain, couplet, refrain, couplet, refrain, pont, refrain | pop de l’ère du streaming, indie pop |
| Court et simple | couplet, refrain, couplet, refrain, refrain | punk, garage rock, rockabilly |
| Hip-hop | intro, couplet, refrain, couplet, refrain, couplet, outro | rap, hip-hop, trap, R&B |
| Double pont | couplet, refrain, couplet, refrain, pont, pont, refrain, refrain | ballades puissantes, rock progressif et symphonique |
| Interlude | couplet, refrain, interlude, couplet, refrain, pont, refrain | rock, pop rock, indie |
| Toutes les parties | intro, couplet, pré-refrain, refrain, interlude, couplet, pré-refrain, refrain, outro | pop, dance-pop |

**Combien de sections.** Le planificateur écrit en général 8 à 10 sections, quoi que demandent les paroles, donc une liste de plus
de 10 est condensée et les paroles des sections abandonnées ne sont pas chantées. Le constructeur le signale quand la liste est
aussi longue. Une chanson ne s’allonge pas en ajoutant des sections ; chacune devient seulement plus courte. Voir
[Allonger la chanson](#making-the-song-longer).

**Mettre les sections dans la zone des paroles** insère les sections comme tags vides, prêtes à recevoir vos lignes. Dès que la zone contient
des mots, ce sont les paroles qui sont chantées, et le constructeur s’efface.

**Écrire les paroles.** Décrivez de quoi parle la chanson et un modèle écrit des paroles pour les sections que vous avez construites. Il demande
trois choses :

- **Lignes par couplet ou refrain** (4, 6 ou 8 ; 6 par défaut). Plus de lignes dans une section donnent une chanson plus longue,
  car le planificateur écrit à peu près autant de musique qu’il y a de mots. Une intro, un pont ou une outro restent à 2 à 4 lignes,
  et un interlude n’en a aucune.
- **Comment sonnent les lignes.** La liste montre les syllabes que vise chaque ligne. L’ancien auteur produisait presque toujours les mêmes
  lignes rimées de huit syllabes, ce qui change ici :

| Choix | Vise | Ce que vous obtenez |
|---|---|---|
| Naturel (par défaut) | 3-13 syllabes | Un mélange de lignes courtes et longues, quelques rimes, pas de pulsation régulière |
| Rimes régulières | 6-10 syllabes | Des lignes égales rimant deux à deux : la forme traditionnelle, et ce que faisait l’auteur auparavant |
| Rythme parlé | 5-14 syllabes | Conversationnel et rythmé, comme la parole ou le rap, avec des rimes internes |
| Rimes libres | 4-13 syllabes | Quelques rimes, quelques assonances, parfois rien, et des lignes de longueurs différentes |
| Court et percutant | 3-6 syllabes | Des lignes courtes et des phrases répétées |
| Long et fluide | 10-14 syllabes | De longues lignes qui s’enchaînent comme une pensée |

  Le dernier choix est mémorisé. Ce sont des objectifs, pas des garanties : un modèle de langage les suit de près pour les
  extrêmes (court et percutant, long et fluide) et plus librement pour les nuances.
- **La consigne** elle-même, avec vos propres mots, et le style au-dessus, qui donne l’ambiance. La consigne est gardée avec la prise,
  si bien qu’ouvrir une prise et appuyer sur **Écrire les paroles** montre ce qui avait été demandé, prêt à être modifié et réécrit.

Le brouillon arrive dans la zone des paroles, et la fenêtre se ferme dès qu’il commence. C’est un premier jet : lisez-le et faites-le
vôtre.

**Suivre exactement cette structure** (la case sous la zone des paroles, décochée par défaut). Le planificateur prend les tags de section
des paroles comme une indication, et livré à lui-même il écrit sa propre forme : il ajoute souvent une intro et une outro,
remplace un pont par un interlude et un couplet, ou condense une longue liste. Avec ceci coché, le plan écrit exactement les
sections que nomment les paroles, dans cet ordre, et aucune autre. Il ne peut pas ajouter d’intro ou d’outro que vous n’avez pas
listée. Le planificateur décide toujours de la musique et du moment où commence chaque section. Cela ne vaut que pour les chansons.

**Qui chante chaque ligne : les indications de voix.** Une ligne seule entre crochets qui nomme une voix indique qui chante les
lignes suivantes, jusqu’à la prochaine indication ou la prochaine section :

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

Écrivez une indication sous la forme `[male voice]`, `[female voice]` ou `[both voices]`, chacune sur sa propre ligne entre crochets.
L’éditeur de paroles agrandi a des boutons **+ Homme**, **+ Femme** et **+ Les deux** dans son en-tête pour les insérer au curseur.
Ce sont les formes avec lesquelles la fonction a été essayée, ainsi que `vocal` pour `voice` (`[female vocal]`) et
`[male and female voices]` pour les deux. Vous pouvez ajouter vos propres mots après une virgule, comme dans
`[female voice, soft and close]` ; ils ne changent pas qui chante. Une section sans indication est laissée au planificateur.

D’autres graphies sont aussi lues, pour que des paroles écrites ailleurs ne soient pas ignorées : `[man]`, `[woman]`, `[duet]`, une indication
dans le tag d’une section comme `[Verse 2 - female vocal]`, et une indication entre parenthèses, `(female voice)`. Les crochets
sont l’habitude la plus sûre : des mots entre parenthèses sont en général des chœurs, et peuvent être chantés.

Une indication seule ne décide pas de la voix. Le chanteur dépend surtout de la hauteur à laquelle la mélodie est écrite : la même
ligne une octave plus haut est chantée par une femme, et le planificateur aime écrire un couplet sur deux octaves, en changeant toutes les quatre
lignes environ, quelle que soit l’indication. **Les voix suivent les repères** (une case sous la zone des paroles, affichée dès que les paroles ont
une indication ; cochée pour une nouvelle prise) respecte les indications : quand le plan est écrit, chaque passage indiqué de la mélodie est déplacé par
octaves entières là où chante cette voix, grave pour un homme et aiguë pour une femme. Rien d’autre ne change dans le plan. C’est
refait avant chaque rendu, donc cela suit une modification des paroles ou de la partition. Sur la page Partition,
**Voix selon les repères** fait la même chose une fois sur la partition de la zone, pour une prise faite sans la case ; enregistrez la partition
et faites-en le rendu.

Trois choses à savoir :

- **Qui chante une ligne reste en partie le hasard.** Avec la mélodie au bon endroit, la plupart des lignes vont à la voix
  indiquée, mais un rendu peut tout de même en donner une à l’autre voix. Refaites le rendu avec une autre seed, ou utilisez
  **Essayer encore**.
- **Les deux** place la ligne là où chante une femme et laisse la seconde voix au rendu, qui en fait souvent entrer une
  dans un refrain. Cela demande un duo plutôt que de le créer : la part de la seconde voix varie d’un
  rendu à l’autre. Il n’existe pas encore de moyen d’écrire deux chanteurs sur une ligne sans que les paroles en souffrent.
- Une prise faite avant l’existence de cette case garde sa partition telle quelle ; cochez-la, ou utilisez **Voix selon les repères**, pour l’ajuster.

**Écrire à la main.** Le bouton Agrandir ouvre un éditeur pleine taille avec des boutons pour intro, couplet, pré-refrain,
refrain, pont, interlude, outro et instrumental. Une section est une ligne comme `[Verse]` suivie de ses lignes ; un
tag sans ligne en dessous, comme `[Interlude]`, est un passage instrumental.

### Le son {#the-sound}

- **Harmonie** (le curseur) : à quel point les accords sont audacieux. Une nouvelle chanson démarre sur **Variée**, avec l’interprétation
  sur **Large** : dans nos propres essais, cette paire a donné les versions les plus intéressantes musicalement, c’est donc un bon point de départ. Réglez
  l’un ou l’autre à votre goût. Les prises existantes gardent ce avec quoi elles ont été faites. Livré à lui-même, le planificateur tend à écrire une boucle
  de quatre accords et à l’utiliser pour chaque section, et chaque cran l’en éloigne un peu plus. Les crans s’ajoutent les uns
  aux autres :

  | Cran | Ce qu’il fait aux accords | À choisir quand |
  |---|---|---|
  | Familière | Rien : les accords de YuE2, souvent une seule boucle pour toute la chanson | Vous aimez la première idée du planificateur, ou voulez l’accompagnement le plus simple |
  | Variée | Décourage la répétition exacte des accords qu’il vient d’utiliser, il les recolore donc (un F, puis un Fmaj7) mais reste dans la tonalité | La boucle paraît trop uniforme et la chanson doit rester conventionnelle |
  | Colorée | Pareil, en plus fort : couplet et refrain se séparent, avec des accords plus riches. Une section ne peut pas non plus commencer sur les mêmes accords que la précédente, donc un refrain ne démarre plus comme son couplet | Vous voulez que le refrain soit un élan, pas une répétition. Un bon premier cran |
  | Aventureuse | Décourage les *fondamentales* récemment utilisées, pas seulement les graphies, l’harmonie doit donc voyager, et il emprunte des accords hors de la tonalité | Vous voulez du mouvement et de la surprise, et repérerez un accord qui sonne bizarre |
  | Hors cadre | Audacieux, avec une attirance pour les accords hors tonalité | Les expériences. Attendez-vous à rejeter certains plans |

  À partir de Coloré, les choix d’accords diffèrent davantage d’une section à l’autre : plus d’accords différents dans une
  chanson, plus de motifs de quatre mesures qui ne se répètent pas, et moins de refrains qui copient le début du couplet. Le plan reste
  une chanson normale, il vaut donc la peine d’essayer un ou deux crans de plus avant d’aller chercher une Variété du plan plus sauvage.
  Dans **Avancé**, **Les sections commencent différemment** peut être réglé sur *Toujours* ou *Jamais* pour essayer un plan avec et sans
  la règle du refrain ; la valeur par défaut, *Suivre l’harmonie*, est active à partir de Coloré. Un style comme la trap ou l’ambient est souvent
  fondé sur des boucles par nature, attendez-vous donc à un changement moindre qu’en pop ou en rock. Voir [Harmonie](#harmony) pour les mesures.
- **Variété du plan.** La liberté avec laquelle le planificateur écrit tout le reste. Voir [Variété du plan](#plan-variety).
- **Interprétation.** Comment les notes sont jouées au rendu. Voir [Interprétation](#interpretation).
- **Durée maximale.** Le plus tard que la chanson puisse s’arrêter. Voir [Durée](#length).
- **Mode.** *Complet* garde les accords du plan ; *mélodie* laisse l’accompagnement libre. *Sans partition*, pour les chansons, n’écrit
  aucun plan : voir [Une chanson sans partition](#a-song-with-no-score).
- **Seed**, et **garder cette seed**. Voir [La seed, et reproduire une prise](#seed-and-reproducing-a-take).
- **Finition de production** et **Normaliser le volume.** Voir [Finition de production](#production-polish).
- **Lancer le rendu dès que le plan est prêt**, à côté du bouton au pied de la fenêtre, enchaîne le plan et le rendu
  sans s’arrêter entre les deux. C’est coché au départ, et l’éditeur retient votre choix. Décochez pour lire le
  plan d’abord.
- **Avancé** (le bouton de l’en-tête) : étapes de diffusion, Suivre le style, Éviter, Verrouillage de tonalité, Verrouillage du tempo, la partition la plus longue,
  limite de maintien d’accord, bonus d’harmonie hors tonalité, Sections qui commencent différemment, loudness cible et fondu de fin. Voir
  [Réglages avancés](#advanced-settings).
- **Mastering** (le bouton à sa gauche, quand la prise a du son) ouvre le rack de mastering par-dessus l’éditeur pour
  la prise qui y est. Le rack comprend, dans l’ordre, un égaliseur façon 1073, un égaliseur paramétrique, un compresseur, un élargisseur stéréo et
  un limiteur. Sur le graphique de l’égaliseur paramétrique, chacune des sept bandes est un point : faites-le glisser latéralement pour sa fréquence
  et verticalement pour son gain, tournez la molette dessus pour sa largeur, double-cliquez pour le réinitialiser. La bande sous
  le graphique règle le type de la bande choisie (coupe-bas, plateau grave, cloche, coupe-bande, plateau aigu, coupe-haut) et l’active
  ou la désactive, **Plat** remet chaque bande à 0 dB, et le bouton dans le coin du graphique change le nombre de décibels que montre le
  graphique. Le bouton est vert tant que le rack change le son de la prise. Rack ouvert, la barre d’espace lit
  et met en pause la prise et les flèches se déplacent dedans et règlent le volume, comme sur la page principale. Échap ferme
  le rack, puis l’éditeur.

### Allonger la chanson {#making-the-song-longer}

La durée d’une chanson est fixée par son plan, et le rendu suit la durée du plan. Voici ce qui la fait varier :

| Pour obtenir… | Faites ceci |
|---|---|
| Une chanson plus longue | Donnez plus de lignes à chaque section (**Lignes par couplet ou refrain** : 6 ou 8) |
| Une chanson plus lente et plus longue | Réglez un **Tempo imposé** dans Avancé. Le même plan à un BPM plus bas dure plus longtemps |
| Une chanson plus longue en ajoutant des sections | Cela ne marche pas : un plan a environ 8 à 10 sections, donc d’autres ne font que raccourcir ou être condensées |
| Plus que ce que permet le plan | Écrivez un nouveau plan ; les durées varient beaucoup d’une exécution à l’autre avec les mêmes paroles |
| Une chanson qui s’arrête à la fin de ses paroles | Augmentez la limite de durée seulement si elle est coupée ; la limite est un plafond, pas une cible |

### Après le plan {#after-the-plan}

- **Rendre cette partition** crée une nouvelle prise dès que la prise ouverte a déjà de l’audio, si bien qu’un rendu n’écrase jamais une prise
  que vous voudriez comparer. Une prise encore sans audio est complétée.
- **Garder cet air** (après avoir changé les paroles d’une prise) : chante la partition de la prise avec les nouvelles paroles, en une nouvelle prise. La
  mélodie ne peut pas gagner de sections ni de notes, donc si vos paroles ont plus de sections que la mélodie, ou bien plus ou bien moins
  de syllabes qu’elle n’a de notes (de longues lignes sur une mélodie faite pour des courtes, ou l’inverse), la
  case se décoche d’elle-même et un nouveau plan est écrit, avec une ligne qui dit pourquoi. Voir [Même mélodie, nouvelles paroles](#same-tune-new-words).
- **Filtrer la bibliothèque.** Les bascules **Chanson**, **Reprise** et **Instrumental** à côté des filtres n’affichent que ces
  types dans l’espace ouvert ; choisissez-en plusieurs, ou aucun pour tous les types.

---

## Lire et corriger le plan {#reading-and-fixing-the-plan}

Le plan est écrit en **notation ABC** : de la musique en texte brut, des lettres au lieu de points sur une portée.
Chris Walshaw l’a conçue au début des années 1990 pour envoyer des airs folk par e-mail, et elle est restée.

Vous n’avez pas besoin de la lire. L’application affiche le même plan sous forme de **grille d’accords** et de vraie **notation
sur portée** sous l’éditeur, et **Agrandir** ouvre le tout en grand. Mais le texte est ce que YuE2
a écrit et ce à partir de quoi il fait le rendu, il vaut donc la peine de savoir s’y repérer.

### Lire un plan {#reading-a-plan}

Un plan commence par un en-tête, une lettre et deux-points par ligne :

```
X:1
M:4/4
L:1/32
Q:1/4=120
V: Vocal clef=treble name="Vocal Melody"
V: Ins   clef=treble name="Ins Melody"
K:D#m
```

| Ligne | Signifie |
|---|---|
| `X:1` | le numéro de l’air. Tout fichier ABC en commence un |
| `M:4/4` | la mesure — quatre temps par mesure |
| `L:1/32` | la durée unitaire : une lettre seule dure une triple croche |
| `Q:1/4=120` | le tempo — une noire à 120 battements par minute |
| `V:` | déclare une voix. YuE2 en écrit deux, une ligne vocale et une instrumentale |
| `K:D#m` | la tonalité, ré dièse mineur. `K:` vient toujours en dernier dans l’en-tête |

Puis la musique elle-même :

```
% intro
V: Vocal
z24z4"D#m"z4|"D#m"z32|
V: Ins
Z|d16a16-|a16g8a8|
```

- **Les notes sont des lettres.** `d16` est un ré qui dure 16 unités. Les minuscules sont une octave au-dessus des majuscules,
  et `'` ou `,` les décalent encore.
- **`-` lie** une note à la suivante, pour qu’elles sonnent comme une seule.
- **`z` est un silence**, avec une durée comme une note. Un `Z` majuscule est un silence d’une mesure entière.
- **Les accords sont entre guillemets doubles**, comme `"D#m"`, et se placent devant la note sur laquelle ils commencent. C’est
  ce que modifie **rechercher et remplacer**.
- **`|` est une barre de mesure**, et **`%` ouvre un commentaire** — c’est ainsi que les sections sont marquées :
  `% intro`, `% verse`, `% chorus`.

Ce fragment dit donc : ré dièse mineur, quatre temps, 120 battements par minute, et pendant l’intro la
voix se tait en portant l’accord, tandis que l’instrument joue un ré et un la liés, puis sol et la.

Deux conséquences pratiques. **Modifier les accords est sans risque**, même si les notes paraissent opaques — ce ne sont que
les parties entre guillemets, et tout le reste peut rester tel quel. Et **si vous modifiez le plan, le rendu
utilise ce que vous avez modifié**, donc corriger un plan est souvent plus rapide que d’en retirer jusqu’à en avoir un bon.

### L’écouter {#hearing-it}

L’onglet **Notation** a un lecteur au-dessus des portées. Appuyez sur **Lire** pour entendre le plan tel que la zone
le contient, modifications comprises, pour juger à l’oreille une mélodie dont vous doutez avant de lui consacrer un rendu.
Les notes jouées sont mises en évidence au fur et à mesure, et son réglage de tempo ne change que l’aperçu,
pas la partition. Le lancer arrête ce que jouait la barre du lecteur, car deux choses à la fois ne servent
à personne, et fermer la fenêtre — ou passer à Grille ou Paroles — l’arrête aussi, pour que rien ne
continue de jouer sans commande à portée de main.

**Instruments** joue chaque voix avec un instrument que nomme le style, plutôt qu’un piano
partout : un style qui dit *electric guitar, drums* s’entend avec une guitare, ses accords joués par
une autre, et une basse en dessous ; une ligne chantée est remplacée par une voix, mais pas la mélodie
d’un instrumental. Un style qui nomme une batterie reçoit aussi une partie de batterie, écrite dans la mesure de la
partition — un backbeat pour le rock, le four-on-the-floor pour la dance, une ride pour le jazz, quelque chose de plus dépouillé pour une
ballade — et elle joue du début à la fin, puisque la partition n’a pas de sections où elle se tairait. La
ligne à côté du lecteur dit ce qu’il a choisi, et décocher revient au piano que vous entendriez
sinon. C’est une lecture du style, pas du rendu : YuE2 décide de la
vraie interprétation et ajoute des parties que la partition n’a jamais eues, prenez-le donc comme le plan joué dans les bonnes
couleurs plutôt que comme le son de la prise.

**Télécharger le MIDI** enregistre la partition pour une STAN. Chaque partie est une piste à part, sur son propre canal,
avec l’instrument utilisé par l’aperçu réglé sur ce canal : la ligne vocale, la ligne instrumentale et,
sauf si vous décochez **Accords**, les symboles d’accords comme partie d’accords avec leur basse à côté (le seul
endroit où l’harmonie est écrite en notes), et la batterie sur le canal 10 quand le style en demande. Les
instruments sont des numéros de programme General MIDI, votre STAN les joue donc avec ses propres sons, et le
tempo et la mesure sont dans le fichier. Un plan qui change de mesure en cours de route est écrit dans la mesure par laquelle il
commence — seule celle-ci est enregistrée — tandis que les notes gardent leurs propres durées. Cliquer sur une note dans
les portées place le curseur sur l’ABC qui l’a écrite.

Une partition avec une note au-dessus de ce que ces instruments peuvent jouer, ou en dessous, est jouée décalée d’octaves
entières jusqu’à ce qu’elle tienne, et la ligne à côté du lecteur dit de combien ; les portées, le fichier MIDI et
la partition elle-même sont inchangés. Les instruments n’ont pas tous la même tessiture — une basse s’arrête bien en dessous
d’un piano — c’est pourquoi la ligne est là quand une partition est décalée. Une partition encore sans notes
n’a rien à jouer et le dit.

Le lecteur a besoin de ses échantillons de notes, qui ne font pas partie de l’application : chaque instrument pèse environ 7 Mo,
récupéré à sa source la première fois qu’un aperçu l’utilise et gardé dans la bibliothèque, si bien
qu’il fonctionne ensuite hors ligne. **Lire** récupère ce dont la partition actuelle a besoin puis démarre, et
**Récupérer les sons** récupère la même chose sans jouer, pour qui préfère que tout soit prêt
d’abord.

### Le piano roll {#the-piano-roll}

Cliquez sur **Piano roll** dans la fenêtre de partition pour ouvrir l’éditeur MIDI visuel. Plutôt que de modifier des lettres ABC brutes, vous voyez et façonnez la mélodie directement sur une grille interactive de hauteur et de temps.

L’éditeur affiche les deux voix de la partition à la fois — **Vocal** (la mélodie chantée principale en bleu ciel) et **Ins** (l’accompagnement instrumental en ambre chaud). Les deux voix sont toujours pleinement actives, visibles, sélectionnables et modifiables. Les boutons **Dessiner** en haut à gauche choisissent à quelle voix sont attribuées les nouvelles notes quand vous cliquez pour en ajouter.

#### Modifier les notes {#editing-notes}

- **Ajouter une note :** cliquez sur une case vide de la grille pour créer une note à cette hauteur et ce moment. La note sonne aussitôt pour que vous entendiez son ton.
- **Sélectionner des notes :** cliquez sur une note pour la sélectionner. Maintenez <kbd>Shift</kbd> ou <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> en cliquant pour sélectionner plusieurs notes dans les parties vocale et instrumentale. Cliquez et faites glisser un **cadre de sélection** sur une zone vide de la grille pour sélectionner une phrase ou un passage dans toutes les voix. Appuyez sur <kbd>Ctrl</kbd>+<kbd>A</kbd> (<kbd>Cmd</kbd>+<kbd>A</kbd> sur macOS) ou cliquez sur **Tout sélectionner** pour sélectionner toutes les notes de la partition. Pour sélectionner toutes les notes depuis le curseur de lecture jusqu’à la fin de la chanson, appuyez sur <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> ou <kbd>Alt</kbd>+<kbd>A</kbd> (ou cliquez sur **Depuis le curseur ▶** dans la barre d’outils).
- **Déplacer des notes :** faites glisser une note sélectionnée pour l’avancer ou la retarder, ou verticalement pour transposer sa hauteur. Quand plusieurs notes sont sélectionnées — vocales, instrumentales ou les deux — elles bougent toutes ensemble, en gardant leur timing relatif, leurs mélodies et leurs paroles.
- **Durée :** faites glisser le bord droit d’une note pour l’allonger ou la raccourcir. Le sélecteur **Grille** (1/16, 1/8 ou 1/4 de note) contraint les déplacements et redimensionnements à des divisions musicales nettes.
- **Supprimer des notes :** double-cliquez sur une note pour la supprimer, ou sélectionnez une ou plusieurs notes et appuyez sur <kbd>Delete</kbd> ou <kbd>Backspace</kbd>.
- **Annuler et rétablir :** chaque modification, déplacement, redimensionnement, ajout et suppression de note est enregistré dans l’historique. Appuyez sur <kbd>Ctrl</kbd>+<kbd>Z</kbd> (<kbd>Cmd</kbd>+<kbd>Z</kbd>) pour annuler, et <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> ou <kbd>Ctrl</kbd>+<kbd>Y</kbd> pour rétablir.
- **Écouter les touches :** cliquez sur une touche du clavier de piano à gauche pour entendre sa hauteur.
- **Agrandir :** cliquez sur **Agrandir** dans la barre d’outils du haut pour étendre le piano roll à toute la largeur de votre fenêtre de navigateur.

#### Chronologie, sections et accords {#timeline-sections-and-chords}

Le long de la règle du haut, la chronologie affiche les numéros de mesure et les limites de section :
- **Renommer des sections :** cliquez sur un repère de section (`intro`, `verse`, `chorus`, etc.) pour modifier son nom ou le réattribuer.
- **Modifier les accords :** juste sous la règle des mesures, la piste d’accords montre la progression harmonique de la chanson. Cliquez sur un accord existant pour le renommer (par exemple changer `C` en `Am7` ou `G/B`), ou sur une mesure vide pour placer un nouvel accord.
- **Harmoniser les mesures vides (Combler les vides) :** cliquez sur **Combler les vides** dans la barre d’outils pour remplir les mesures vides de l’accompagnement instrumental avec des notes générées à partir de la progression d’accords.
- **Supprimer les mesures vides (Compacter les vides) :** cliquez sur **Compacter les vides** pour supprimer les mesures vides et silencieuses dans les deux voix, en décalant vers la gauche les notes et accords suivants pour éliminer les trous indésirables de l’arrangement.

#### Paroles et suivi karaoké {#lyrics-and-karaoke-tracking}

En bas du piano roll, une piste de paroles dédiée aligne chaque syllabe sur la mélodie vocale :
- **Correspondance par phrases :** cliquez sur **Associer les paroles** pour répartir les paroles sur la mélodie vocale. L’alignement détecte les respirations naturelles et les silences entre les phrases mélodiques, et attribue chaque ligne de paroles à sa phrase sans déborder par-dessus les silences sur les mesures suivantes. Les mots de plusieurs syllabes se répartissent proprement sur les notes.
- **Modifier les syllabes :** cliquez sur une étiquette de paroles (ou sélectionnez une note vocale et appuyez sur <kbd>L</kbd>) pour modifier son texte. Si vous saisissez des syllabes séparées par des espaces ou des traits d’union (par exemple `Hel- lo world`), elles se répartissent automatiquement sur les notes vocales consécutives.
- **Surlignage au survol :** survoler une étiquette de paroles met en évidence la note correspondante sur la grille, et survoler une note vocale met en évidence son étiquette en dessous.
- **Balle karaoké :** pendant la lecture, une balle animée rebondit sur chaque note au moment où elle est chantée, et la syllabe active et la note de la grille s’illuminent en temps réel.

#### Lecture et accompagnement harmonique {#playback-and-harmony-accompaniment}

Appuyez sur <kbd>Space</kbd> ou cliquez sur **▶ Lire** pour lancer la lecture depuis le curseur. La ligne de lecture balaie la grille et met à jour la mesure, le temps et le compteur de temps écoulé.

- **Clic audible (métronome) :** la lecture comprend par défaut un clic audible, avec un clic de woodblock accentué sur le premier temps de chaque mesure et des clics plus doux sur les autres temps. Appuyez sur <kbd>C</kbd> ou <kbd>M</kbd> (ou cliquez sur **Clic** dans la barre de transport) pour activer ou couper le métronome à tout moment.
- **Accompagnement harmonique :** la lecture synthétise de chaudes nappes d’accords polyphoniques directement à partir de la progression d’accords de la partition. Même quand les pistes vocale ou instrumentale se taisent, l’espace harmonique reste musical et chaleureux au lieu de tomber dans un silence mort. Appuyez sur <kbd>H</kbd> (ou cliquez sur **Accords** dans la barre de transport) pour activer ou couper l’accompagnement d’accords.
- **Avancer par mesures :** appuyez sur <kbd>Flèche gauche</kbd> et <kbd>Flèche droite</kbd> pour reculer et avancer mesure par mesure, ou sur <kbd>Home</kbd> pour revenir directement au début.

#### Raccourcis clavier {#keyboard-shortcuts}

| Touche | Action |
|---|---|
| <kbd>Space</kbd> | Lecture / pause |
| <kbd>Flèche gauche</kbd> | Reculer d’une mesure |
| <kbd>Flèche droite</kbd> | Avancer d’une mesure |
| <kbd>Home</kbd> | Ramener la lecture au début (mesure 1) |
| <kbd>C</kbd> ou <kbd>M</kbd> | Activer / couper le clic audible (métronome) |
| <kbd>H</kbd> | Activer / couper l’accompagnement d’accords |
| <kbd>Delete</kbd> / <kbd>Backspace</kbd> | Supprimer la ou les notes sélectionnées |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Cmd</kbd>+<kbd>Z</kbd> | Annuler la dernière modification |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> | Rétablir |
| <kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>Cmd</kbd>+<kbd>A</kbd> | Sélectionner toutes les notes des deux voix |
| <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> / <kbd>Alt</kbd>+<kbd>A</kbd> | Sélectionner toutes les notes du curseur à la fin, dans les deux voix |
| <kbd>+</kbd> ou <kbd>=</kbd> | Agrandir l’échelle horizontale |
| <kbd>-</kbd> ou <kbd>_</kbd> | Réduire l’échelle horizontale |
| <kbd>0</kbd> | Défiler jusqu’aux notes (ajuster la vue) |
| <kbd>L</kbd> | Modifier les paroles de la note vocale sélectionnée |
| <kbd>Escape</kbd> | Effacer la sélection, ou fermer la fenêtre de partition |

### Harmonie {#harmony}

Livré à lui-même, YuE2 tend à écrire une boucle de quatre accords et à s’y tenir. Le curseur **Harmonie** l’éloigne
des accords qu’il vient d’utiliser, sans casser la structure de la chanson.

| Cran | Ce que vous obtenez |
|---|---|
| Familière | Les accords de YuE2. Souvent une seule boucle pour toute la chanson |
| Variée | Évite de répéter les mêmes accords. Reste dans la tonalité |
| Colorée | Couplet et refrain ont des progressions différentes, avec des accords plus riches. Une section ne peut pas commencer comme la précédente |
| Aventureuse | Garde l’harmonie en mouvement et emprunte des accords hors de la tonalité |
| Hors cadre | Audacieux, et va plus loin hors de la tonalité |

**Écrire un nouveau plan** utilise la position actuelle du curseur, vous pouvez donc retirer les mêmes paroles avec des
accords plus audacieux et comparer.

Cela a été mesuré, pas deviné — une seule série de paroles, deux styles, trois seeds chacun :

| | Familière | Variée | Colorée | Aventureuse | Hors cadre |
|---|---|---|---|---|---|
| Accords différents dans une chanson | 4.7 | 6.3 | 8.7 | 9.0 | 10.3 |
| Mesures avec un accord hors tonalité | 0% | 0% | 0% | 13% | 24% |
| Motifs de quatre mesures non répétés | 29% | 38% | 50% | 63% | 64% |

Chaque plan, à chaque cran, a gardé ses sections et des accords valides. Demander une harmonie audacieuse dans le
texte du style à la place — « jazz harmony », « borrowed chords » — n’a eu aucun effet mesurable.

### Variété du plan {#plan-variety}

Dans *Avancé*, **Variété du plan** règle la liberté avec laquelle le planificateur écrit. Là où l’Harmonie agit sur les
accords, ceci agit sur tout : mélodie, structure et durée.

- **Calme :** le plus stable. Peu d’accords, et une mélodie qui reste près de son point de départ.
- **Normal :** la valeur par défaut.
- **Vif :** quelques accords et tournures de plus.
- **Audacieux :** une harmonie plus riche, environ trois fois le vocabulaire d’accords du mode normal, tandis que la mélodie reste
  reconnaissablement du même genre.
- **Excentrique :** agité. Les accords changent sans cesse, et la mélodie saute entre les registres d’une
  section à l’autre. Pour des chansons étranges et décalées.
- **Sauvage :** le plus agité de tous, et il peut changer de tonalité en cours de route.

### Une chanson sans partition {#a-song-with-no-score}

**Sans partition**, le troisième choix sous **Mode**, chante les paroles sans aucun plan : YuE2 écrit la mélodie et
les accords en chantant, comme le faisait le YuE d’origine, et la chanson est rendue aussitôt avec **Chanter sans partition**.
Elle sonne souvent très différemment d’une chanson planifiée.

Ce qui oriente un plan n’a ici rien sur quoi agir, donc **Harmonie**, **Variété du plan**, **Garder cet air** et **Suivre exactement cette structure**
sont grisés tant qu’il est choisi, et il n’y a pas de partition à lire ou à modifier. YuE2 décide
de la durée, jusqu’à la limite. Le verrouillage de tonalité et de tempo ne l’atteignent que comme mots dans le style. Chanter à nouveau,
Variations, Essayer encore et nouvelles paroles fonctionnent tous, chacun chanté à nouveau sans partition. **Écrire un nouveau plan** donne à la prise une
partition, et Mode revient à *complet*. C’est réservé aux chansons à partir d’un prompt : une reprise est la partition de son enregistrement, et un
instrumental en a besoin pour tenir sa voix à l’écart. Les deux moteurs savent le faire.

---

## Le rendu {#rendering}

### Interprétation {#interpretation}

La partition fixe les notes. L’**interprétation** règle la manière de les jouer.

| Interprétation | Ce que vous entendez |
|---|---|
| Standard | La lecture habituelle de YuE2 |
| Serrée | plus maîtrisé et poli |
| Lâche | plus brut et spontané |
| Posée | libre de répéter un motif et de rester dans un groove |
| Agitée | garde les parties en mouvement, évite de se répéter |
| Large | va chercher des sons moins évidents |

### Variations {#variations}

Le bouton étincelle d’une carte rend **la même partition et la même seed** dans les autres
interprétations. Comme seule l’interprétation change, ce que vous entendez de l’une à l’autre est
l’interprétation — pas un autre coup de dés. Chacune est une prise à part entière, intitulée
*Night drive · Loose* et gardée dans la prise d’où elle vient (voir **Des prises dans une prise**,
dans La bibliothèque). La fenêtre a sa propre limite de durée, qui part de celle de l’éditeur et ne s’applique
qu’à ces prises.

### Essayer encore {#try-more}

Le bouton dé d’une carte rend **la même partition et les mêmes paroles en plusieurs nouvelles prises**, à
écouter ensemble. Variations ne change que l’interprétation et garde la seed ; ceci change le
tirage :

- **Nouvelles seeds :** une seed neuve pour chacune, tout le reste gardé.
- **Intensités du Planificateur :** pour une prise avec une LoRA de style qui a une moitié planificateur, la même seed à
  d’autres forces de Planificateur (la sienne est exclue). Le planificateur change l’interprétation elle-même, pas seulement
  la voix, il agit donc comme une autre seed.

Les nouvelles prises s’intitulent *Night drive · try 1* ou *Night drive · planner 0.60* et sont gardées dans
la prise d’où elles viennent, dont le panneau s’ouvre pour les montrer à mesure qu’elles se terminent. Pour les comparer
entre elles, appuyez sur **Tout sélectionner** pendant que le panneau est ouvert, puis sur **Comparer**. La fenêtre a sa
propre limite de durée, qui part de celle de la prise.

### La seed, et reproduire une prise {#seed-and-reproducing-a-take}

Chaque prise enregistre sa seed et chaque réglage qui l’a façonnée. La carte les nomme, cliquer sur une carte
les montre dans le panneau de prise, et l’ouvrir dans l’éditeur recharge le tout. **Encore** ouvre
l’éditeur avec exactement cela, seed comprise, pour reproduire une prise qui vous a plu, et ajuster un réglage à la fois une prise
qui vous a presque plu.

Dans les menus de l’éditeur, survoler une interprétation montre ce qu’elle fait.

Cochez **garder cette seed** pour garder la même seed d’un rendu à l’autre ; sinon chaque rendu en tire une
nouvelle.

Un rendu utilise ce que montre l’éditeur : son style, la LoRA de style et ses forces, la limite de durée, le mode,
l’interprétation et la seed, même quand on refait le rendu de la partition d’une prise.

### Même mélodie, nouvelles paroles {#same-tune-new-words}

Le planificateur lit toutes les paroles avant d’écrire une note, donc la même seed ne donne le même plan que
pour les mêmes paroles. Changez une ligne et le plan suivant est un nouvel air : une autre mélodie, souvent une autre
tonalité et un autre tempo, et la voix change avec eux.

Pour garder un air qui vous plaît, ouvrez la prise et changez ses paroles. **Garder cet air** apparaît sous les
paroles, coché, et le bouton principal devient **Chanter avec les nouvelles paroles**. Changez d’abord tout ce que vous
voulez : le style, la LoRA et ses forces, la limite de durée, l’interprétation. La partition de la prise est
alors chantée avec les nouvelles paroles, en une nouvelle prise à côté de l’originale, qui reste telle quelle. Gardez la seed
cochée pour garder la voix aussi proche que possible. Décochez **Garder cet air** pour écrire à la place un nouveau plan, et un
nouvel air, pour les paroles. De nouvelles paroles qui gardent le nombre de syllabes des anciennes lignes collent le mieux
à la mélodie. Sinon, parce qu’il y a plus de sections ou bien plus de syllabes que l’air n’a de notes (de longues lignes sur un air
fait pour des courtes : les lignes sont répétées ou abandonnées), ou bien moins (de courtes lignes sur un air fait pour des longues :
le chanteur remplit les notes en trop avec ses propres mots), **Garder cet air** se décoche avec une ligne qui dit pourquoi, et
un nouveau plan est écrit pour les paroles. Recochez-le pour chanter l’air quand même.

### Finition de production {#production-polish}

**Finition de production** applique la LoRA de décodeur Realaudio de Mothersuperior. YuE2 tel quel sonne souvent étouffé
dans les médiums ; ceci sépare plus nettement instruments et voix. Activé par défaut.

### Durée {#length}

La limite de durée est un plafond ferme, pas une cible. YuE2 décide quand une chanson se termine, et finit généralement
d’elle-même ; la limite arrête celle qui ne s’arrête pas. Elle part de 360 secondes, ou de ce qu’indique **Durée maximale d'une nouvelle prise**
dans les Paramètres. Puis elle fait de la place à la musique, pour qu’une chanson longue ne soit pas coupée :

- Pour une **chanson ou un instrumental à partir d’un prompt**, la limite est relevée quand son plan est écrit, si le plan
  est plus long : à la durée du plan avec une dizaine de secondes de marge. Elle n’est jamais abaissée.
- Avec un **enregistrement** choisi, pour une reprise ou un instrumental, la limite suit la partition de l’enregistrement,
  arrondie de la même façon.

Une limite que vous saisissez vous-même reste telle quelle, et la page Partition signale alors quand un plan est plus long
qu’elle. Un plan bien plus long que sa limite (plus d’un tiers au-dessus, et plus de huit minutes) n’est pas pris
pour une chanson du tout, et il est réécrit. De temps en temps,
un rendu ne s’arrête pas à la fin de sa partition et continue jusqu’à la limite ; une telle prise est fondue
sur ses dernières secondes plutôt que coupée, et sa carte dit qu’elle a atteint la limite. Plus rarement encore, un
rendu se termine avant que commence la dernière section de sa partition. L’application refait alors un rendu avec une nouvelle
seed avant de le déclarer terminé, et si celui-ci s’arrête trop tôt lui aussi, la carte dit qu’il s’est arrêté avant la
dernière section : refaites un **Rendu** pour un autre essai.

---

## Reprendre un enregistrement {#covering-a-recording}

1. Déposez un fichier audio, jusqu’à 2 Go. Il est stocké une fois et haché, si bien que le même fichier n’est jamais
   gardé deux fois. Un fichier vidéo (MP4, MOV, MKV, WebM et autres) fonctionne aussi : seul son son est gardé, en FLAC.
2. Appuyez sur **Transcrire**. SheetSage2 écrit la mélodie et les accords dans la zone de partition. C’est
   mis en cache par enregistrement, donc reprendre à nouveau la même chanson saute cette étape.
3. Corrigez ce qu’il a mal entendu.
4. Ajoutez des paroles, choisissez un style, appuyez sur **Créer la reprise**.

Une reprise suit la mélodie et les accords de l’original tandis que le style décide de tout le reste, et c’est
ce qui en fait une reprise plutôt qu’une copie.

### Enregistrer votre propre air {#recording-a-tune-of-your-own}

> [!NOTE]
> La qualité de la détection d’un air dépend de l’enregistrement, et un plan construit autour peut tout de même échouer ou
> divaguer : écrivez un nouveau plan, ou réenregistrez l’air.

En mode **Reprise**, **Enregistrer une mélodie** ouvre l’enregistreur. Choisissez ce que vous enregistrez sous **Entrée** :

- **Voix :** chantez ou fredonnez dans un micro. **Autotune** peut caler la prise sur une tonalité et une gamme ; le
  bouton d’une prise bascule entre la version accordée et la version brute pour que vous entendiez ce qu’il a fait.
- **Instrument :** jouez l’air sur un instrument, par exemple une guitare branchée sur une interface audio.
  Jouez-le **une note à la fois** : la ligne que vous jouez devient l’air chanté, et des accords
  grattés ne donnent pas d’air à chanter. Choisissez l’interface sous **Appareil**, et sous **Canal** le côté
  où est branché votre instrument (l’entrée 1 d’une interface est en général **Gauche**). Montez **Gain d'entrée**
  pour un instrument faible, en gardant le vumètre hors du CLIP. L’autotune n’est pas proposé : un instrument est
  déjà accordé. Yeufonic retient ces choix dans ce navigateur.

Le métronome, le décompte et le retour casque fonctionnent de la même façon pour les deux. **Utiliser pour la reprise** garde la
prise comme enregistrement, marqué **MIC** ou **INST** dans la liste. Transcrivez-le comme n’importe quel enregistrement ; un
air enregistré est transcrit en mélodie seule, car des accords devinés à partir d’un air isolé seraient tenus dans
chaque refrain d’une chanson faite à partir de lui (un enregistrement transcrit avant ceci garde ses accords jusqu’à ce qu’il soit
transcrit à nouveau). Dix à trente secondes d’air suffisent largement.
**Extraire les paroles** n’est pas proposé pour une prise d’instrument, puisqu’elle n’a pas de paroles à entendre : utilisez
**Écrire les paroles**.

**Vous vous entendez en retard ?** Le navigateur ajoute un court délai entre ce que vous chantez ou jouez et ce que
vous entendez au casque. Si votre interface audio a un retour direct (sans latence), utilisez-le
et coupez le **Retour** de l’enregistreur, pour vous entendre directement depuis l’interface, et une seule
fois. Utilisez un casque filaire : le Bluetooth ajoute son propre délai.

#### Développer en chanson complète {#expand-to-full-song}

Un air enregistré ne fait souvent que quelques mesures. **Développer en chanson complète** fait planifier par YuE2 une chanson entière
qui contient votre air : le plan est dans la tonalité, la mesure et le tempo de votre air, chaque refrain (ou chaque couplet,
si vous le choisissez) contient votre air, et le reste de la chanson est écrit autour. Puis elle est rendue
comme une reprise de votre enregistrement.

- **Chanté par :** un homme ou une femme. Votre air est déplacé par octaves entières là où chante cette voix,
  puisque l’octave dans laquelle la mélodie est écrite décide de qui la chante. Si le style ne nomme aucun chanteur,
  la voix y est ajoutée.
- **Accords :** un air seul revient souvent du transcripteur sans accords. Yeufonic lui donne alors
  des accords tirés de ses propres notes, pour que le planificateur ait une harmonie à suivre. Les accords que vous écrivez dans
  la partition de l’enregistrement sont conservés.
- **Votre air** est toujours la partition de l’enregistrement, même quand l’éditeur montre une prise faite à partir
  de lui.
- **Structure de la chanson :** utilisée quand la zone des paroles est vide. S’il y a des mots dans la zone, leurs sections sont
  la structure, et il leur faut un **[Chorus]** (ou un **[Verse]**) pour accueillir votre air.
- **Paroles :** un fredonnement peut être planifié sans paroles. Un air joué sur un instrument a besoin de paroles pour être
  chanté, alors écrivez-les d’abord : **Écrire les paroles** les rédige pour vous.

### Fichiers MIDI et reprises {#midi-files-and-covers}

> [!NOTE]
> L’utilisation de fichiers MIDI est conçue pour générer des prises différentes, souvent décalées, d’airs originaux.

En plus des fichiers audio enregistrés, vous pouvez déposer ou téléverser des fichiers MIDI standard (`.mid`, `.midi`) directement en mode **Reprise**.

Quand un fichier MIDI est téléversé :
- **Transcription automatique de la partition :** Yeufonic analyse les pistes et les canaux pour identifier la mélodie vocale principale, l’accompagnement et la progression d’accords, les transcrit en notation ABC et les charge directement dans le piano roll. Les leads de synthé ou les mélodies vocales programmées dans des registres plus graves sont automatiquement transposés vers une octave naturelle de chant.
- **Paroles intégrées :** les événements de paroles ou de texte présents dans la séquence MIDI sont extraits et alignés sur les syllabes de la mélodie.
- **Où tombent les mesures :** un fichier MIDI n’a pas de barres de mesure propres, et certains commencent avec le premier mot sur le temps *avant* le premier temps fort. Yeufonic lit la batterie et la basse pour trouver la vraie barre de mesure et, quand le fichier commence par une telle levée, place les premiers mots dans une courte mesure à part pour que les accords et les repères de mesure tombent là où sont ceux de la chanson. Un fichier sans motif clair de batterie et de basse est laissé tel quel.
- **Paroles collées :** les mots que vous collez sont ajustés à toute la mélodie d’un coup, une syllabe par note, les notes restantes étant tenues sur la syllabe précédente. Les lignes se terminent là où la mélodie fait silence et commencent là où commence une phrase, si bien qu’une section plus longue ou plus courte que les titres des paroles ne décale plus le reste. Si les mots sont plus longs que ce que la mélodie peut porter, les dernières lignes sont laissées de côté.
- **Écoute audio complète avec SoundFonts :** le lecteur synthétise l’arrangement MIDI en audio haute fidélité avec **FluidSynth** et des SoundFonts General MIDI (`.sf2`). La sortie est normalisée en crête pour que des enregistrements MIDI multipistes discrets s’écoutent avec présence et clarté, sans distorsion.
- **Choisir les SoundFonts :** dans les **Paramètres**, vous pouvez choisir votre banque SoundFont `.sf2` active préférée (comme *Arachno SoundFont 1.0* ou *JNS-GM 2.0*). Les fichiers `.sf2` supplémentaires placés dans `data/models/soundfonts/sf2/` sont détectés automatiquement.
- **Retouches dans le piano roll :** ouvrez le **Piano roll** pour inspecter ou modifier les notes, choisir quelle piste sert de mélodie vocale principale, harmoniser les trous de l’accompagnement avec **Combler les vides**, ou aligner des paroles fraîchement collées avec **Associer les paroles**.

### Reprendre une chanson d’un corpus {#covering-a-song-from-a-corpus}

L’analyse d’un corpus a déjà fait ce dont une reprise a besoin : la partition, les paroles entendues dans la chanson, et
sa voix séparée. Sous vos enregistrements, la liste propose donc **De vos corpus**, repliée par
corpus, avec la tonalité et le tempo de chaque chanson, et un filtre pour un grand corpus. Choisissez une chanson et elle devient aussitôt l’un
de vos enregistrements, avec sa partition et ses paroles, et rien n’est relancé. Les paroles sont placées
sous les sections de la partition, comme les place **Extraire les paroles**, sauf si vous les avez vérifiées dans le corpus,
auquel cas elles arrivent telles que vous les avez laissées. Elles vont dans la zone des paroles, en remplaçant des mots venus
d’un autre enregistrement ; des mots que vous y avez saisis ou modifiés ne sont remplacés que si vous le dites. La zone Style prend le
style avec lequel la chanson a été apprise dans le corpus, le même que sa puce sous une LoRA entraînée à partir de lui.

Le fichier est lié plutôt que copié quand le disque le permet, il ne prend donc pas plus de place, et il reste
si le corpus est supprimé. Quelques chansons sont marquées *score: melody only* ou *score: first 4 min* : leur
transcription complète a échoué pendant l’analyse, ce qui suffit pour l’entraînement. Appuyez sur **Transcrire** pour la
partition complète avec ses accords.

**Avec une LoRA.** C’est là que les chansons de corpus sont le plus utiles : une chanson et une LoRA tirées de la même
œuvre, ou d’œuvres différentes.
1. En mode **Reprise**, ouvrez la liste des enregistrements et choisissez la chanson sous **De vos corpus**. Sa
   partition fixe la mélodie et les accords, et ses paroles sont dans la zone.
2. Choisissez une **LoRA de style**. La LoRA du corpus lui-même fait reprendre au chanteur sa propre chanson, au plus près de
   l’original. La LoRA d’un autre corpus la reprend dans cet autre style et cette autre voix.
3. Réglez les forces comme pour toute reprise : l’enregistrement fixe déjà la mélodie, gardez donc **Son**
   vers **0.50**, et montez-le pour plus de la voix et du son de la LoRA.
4. La zone Style contient déjà le style propre de la chanson, et choisir une LoRA met son mot déclencheur
   devant. Cela garde le genre et l’ambiance de la chanson ; une autre puce, ou les tags du filtre, l’emmènent
   ailleurs. Le tempo et la tonalité viennent de la partition, quoi que dise le style.
5. Appuyez sur **Créer la reprise**. **Variations** en fait ensuite le rendu dans les autres interprétations, et
   **Rechanter** donne une autre voix sur la même partition, comme pour toute prise.

### Extraire les paroles {#extracting-the-lyrics}

**Extraire les paroles**, à côté de *Transcrire*, écrit ce que chante l’enregistrement : il sépare la
voix, l’écoute, et place les lignes sous les sections de la partition. On le demande plutôt
qu’il ne se fait à chaque transcription, car il prend quelques minutes là où transcrire une partition
prend quelques secondes. La voix est séparée, et ses mots entendus, sur le GPU quand le moteur dispose de Demucs et de Whisper, et sur le CPU
sinon (Paramètres, **Utiliser le GPU pour les stems et les paroles**), et la barre indique laquelle des deux étapes est en cours. Whisper sur le GPU
et sur le CPU n’écrivent pas toujours les mêmes mots pour la même voix, aucun n’étant exact : une voix difficile, comme des chœurs
par-dessus une voix principale, peut différer d’un cinquième de ses mots dans un sens ou dans l’autre. La voix séparée est gardée, donc extraire à nouveau le même enregistrement passe
directement à l’écoute, ce qui économise l’essentiel de l’attente.

Les mots sont gardés avec l’enregistrement. Appuyez à nouveau sur **Extraire les paroles** et ils reviennent aussitôt dans
la zone, et on vous demande s’il faut les extraire à nouveau, ce qui vaut la peine après avoir changé la
méthode dans les Paramètres. Choisir un autre enregistrement prend ses mots de la même façon, et un enregistrement
sans mots efface ceux du précédent. Les mots que vous avez saisis ou modifiés restent, sauf si vous acceptez de les remplacer.

Attendez-vous à un bon brouillon plutôt qu’à une transcription. Mesuré sur les vraies paroles de deux chansons, Whisper
s’est trompé sur **1,5 % des mots** pour l’une et **25 %** pour l’autre, où voix principale et chœurs chantent l’un par-dessus
l’autre dans le dernier refrain. Il écoute toute la voix : il sautait autrefois ce que son détecteur de voix
prenait pour du silence, c’est-à-dire l’essentiel de la chanson pour des voix chantées. Lisez le brouillon et corrigez ce qu’il a
mal entendu, surtout là où les voix se chevauchent.

**Faire écouter un LLM externe.** Si un [LLM externe](#external-llm) est votre fournisseur, les Paramètres proposent un choix sous
*Paroles à partir d'un enregistrement*. Réglez-le sur **LLM externe** et la voix séparée est envoyée au modèle pour
entendre les mots, tandis que Whisper détermine toujours quand chaque ligne est chantée. Sur les deux mêmes chansons, Gemini
a fait **1,5 % et 23 %**, les deux sont donc proches ; essayez les deux sur une chanson qui pose problème à Whisper. Il faut un
modèle qui accepte l’audio, comme Gemini. Quand la réponse du modèle ressemble à des paroles, ses mots sont
utilisés, même là où ils diffèrent beaucoup de ceux de Whisper : une voix noyée dans un mix est là où Whisper
peine le plus, et le modèle non. Si le modèle refuse l’audio, se retient (en raccourcissant des lignes,
ou en vous renvoyant vers un site de paroles, comme un modèle peut le faire avec une chanson qu’il reconnaît) ou ne renvoie
presque rien, vous obtenez la version de Whisper à la place. Le message de fin indique lequel
a entendu les mots. La voix quitte votre machine pour cela ; Whisper la garde ici.

Pour une chanson de corpus, **les deux versions sont gardées**. Quand les deux existent, le panneau de relecture de la chanson montre
**Paroles de** avec chaque version et son nombre de mots, celle du modèle externe étant utilisée par défaut. Choisissez
l’autre et ses mots vont dans la zone. La première fois qu’une version est choisie, ses mots sont rédigés, ce qui
marque leurs sections avec le modèle externe ; ensuite chaque version garde ses propres mots, modifications et
case **vérifiées**, si bien que passer de l’une à l’autre est instantané et ne fait aucun appel au modèle. Dans les lignes de Whisper, tout mot
qu’il a répété plus de huit fois d’affilée, comme un « la » tenu qu’il a écrit des centaines de fois, est ramené
à huit.

---

## Instrumentaux {#instrumentals}

Le troisième mode écrit un morceau sans voix. Au lieu de paroles, il prend une **structure** :

| Structure | Ce que reçoit YuE2 | Qui décide |
|---|---|---|
| Laisser YuE2 décider | `[instrumental]` | YuE2 choisit les sections et leurs durées |
| Sections | `[intro] [verse] [chorus] …` | vous choisissez les sections, YuE2 leur durée |
| Sections minutées | `[intro 0:00-0:15] …` | vous choisissez les deux |

Ajoutez des sections avec les puces **+**, réordonnez-les avec les flèches, et donnez une durée à chacune en mode minuté.
**Envoyé à YuE2 :** montre exactement ce que reçoit le modèle. La structure est une indication : YuE2 peut renommer une
section, ajouter un interlude, ou dépasser les durées données, la limite de durée reste donc le plafond ferme.

### Un instrumental à partir d’un enregistrement {#an-instrumental-from-a-recording}

**À partir d'un enregistrement (facultatif)** en haut de l’éditeur prend l’un de vos enregistrements, comme une reprise. Sa
transcription est la partition, il n’y a donc pas de plan à écrire, et le rendu joue sa mélodie et ses
accords avec la LoRA instrumentale.

Les sections viennent aussi de la partition : une par section de la partition, sous les noms que connaît la LoRA. Un
*interlude* devient un pont. Un rendu associe chaque section de la structure à une section de la partition,
c’est pourquoi le constructeur leur cède la place. Pour réorganiser la chanson, faites glisser une section à un autre endroit ou déplacez-la avec les flèches, ajoutez
une **copie** après elle, ou retirez-la avec le **✕** : chaque changement réécrit la partition (la fenêtre Partition
le montre), et **Restaurer les sections d'origine** la rétablit jusqu’au chargement d’une autre partition.
Pendant que la prise joue dans l’éditeur, la section en cours est allumée, et un double-clic sur une section y saute. Les durées viennent des mesures et du tempo de la partition, que le rendu suit de près au début d’une prise et pour une prise rendue en entier. Un rendu qui finit bien avant sa partition a joué moins de musique que n’en contient la partition, la liste peut donc se décaler par rapport à l’audio au fil de la chanson ; une ligne sous la liste le signale et dit de combien. Une reprise montre la même liste sous ses paroles, et ses paroles sont associées aux sections dans l’ordre, alors
adaptez-les : la liste dit ce qu’il leur faut après que vous avez ajouté, supprimé ou réorganisé des sections. Elle montre aussi le total face à la
limite de durée, et propose de relever la limite quand une chanson plus longue serait coupée. Appuyez sur **Créer l'instrumental** pour faire le rendu.

Un instrumental écrit à partir d’une structure a aussi une partition, et une fois planifié ses sections sont listées de la même façon. Le
constructeur de structure est la consigne pour un plan pas encore écrit, il cède donc la place à la liste. Réorganisez les sections et appuyez sur
**Rendre cette partition** : les tags de section du rendu suivent la partition modifiée. Une prise qui a déjà de l’audio est rendue en une
nouvelle prise à côté, quoi que vous ayez changé, si bien que l’originale garde la sienne. **Écrire un nouveau plan** (sous la partition) demande toujours
une autre mélodie à partir de la structure avec laquelle la prise a été écrite.

**Une chanson chantée fonctionne aussi.** Sa partition a la mélodie chantée dans la partie vocale, qui sortirait
chantée, l’air est donc confié à un instrument : partout où aucun instrument ne joue, les notes chantées
passent à un instrument, et la partie vocale ne garde que ses accords. L’éditeur le signale sous l’enregistrement. C’est
en général le meilleur choix pour une chanson : sans sa voix, le transcripteur tend à manquer la
différence entre couplet et refrain, et entend toute la chanson comme une seule boucle d’accords. La LoRA
l’arrange en instrumental, attendez-vous donc à des parties à elle, comme de la guitare en plus.

Choisissez **Pas d'enregistrement : écrire un plan de partition** dans la liste pour revenir à l’écriture d’un plan.

### Quand un instrumental chante {#when-an-instrumental-sings}

Il arrive que le modèle mette une voix dans un instrumental. C’est un échec du modèle, pas un réglage
que vous avez mal fait. Avant le rendu, si le plan met des notes dans la voix vocale, une boîte de dialogue propose un nouveau
plan, une nouvelle seed, ou de faire le rendu quand même. Une prise terminée n’est pas vérifiée : écoutez-la.

### Un instrumental à partir de la partition d’une chanson {#an-instrumental-from-a-song-s-score}

**Faire un instrumental**, sous la partition d’une chanson ou d’une reprise dans la page Partition de l’éditeur (à côté de **Rendre cette partition**
pour une chanson), fait de la
même partition un instrumental, dans une nouvelle prise : l’originale reste telle quelle. La mélodie chantée passe
à un instrument, seuls les tags de section de la partition sont envoyés au modèle à la place des paroles, la
LoRA instrumentale est utilisée, et le style perd les tags qui décrivent une voix (« soft male vocal »).
C’est la façon d’obtenir « cet air, sans voix ». Vider à la main la partie Vocal de la partition d’une chanson ne
suffit pas : le rendu d’une chanson chante quand même les mots qu’on lui donne.

---

## Voix {#voices}

Les puces **Chant** fixent le sexe et le caractère du chanteur en écrivant dans le style, pour toute la chanson.

Pour un duo, ou un chanteur pour les couplets et un autre pour le refrain, mettez des indications de voix dans les paroles et cochez
**Les voix suivent les repères** : voir [Les paroles](#the-words) dans « Écrire une chanson à partir d’un prompt ». Cela fonctionne aussi pour les
paroles d’une reprise.

## Corpus et entraînement d’une LoRA {#corpora-and-training-a-lora}

Un **corpus** est un dossier de chansons, préparé comme jeu d’entraînement pour une LoRA de style : en général un
artiste, un genre, ou quelques artistes proches.
Ouvrez **Corpus** depuis le menu. C’est activé par défaut ; `TRAINING_ENABLED=0` pour l’application, ou un
moteur construit avec `WITH_TRAINER=0`, le retire.

L’entraînement est ce que l’application fait de plus exigeant : avec le modèle pleine qualité (BF16) recommandé,
une carte graphique de 16 Go et 32 Go de RAM système (sous WSL2, `memory=32GB` dans `.wslconfig`) sont le minimum pratique.
Une carte de 8 Go peut servir à l’entraînement avec le modèle à faible mémoire (INT8).

1. **Nouveau corpus.** Donnez-lui un nom et un **mot déclencheur**, dites si la voix est masculine ou féminine
   (**aucune** pour des chansons sans voix : voir plus bas), décrivez le son commun à toutes les chansons, et ouvrez le dossier qui contient les chansons. Confirmez que vous
   avez le droit de vous entraîner dessus, puis appuyez sur **Analyser le dossier**. Le dossier est seulement lu.
   **Un corpus sans voix.** Choisissez **aucune** pour **Voix** quand les chansons sont instrumentales, comme
   la dance et la musique électronique. L’application ne sépare alors pas de voix et n’écoute pas de mots, si bien que rien
   n’invente de paroles sur des synthés. Les paroles de chaque chanson sont les tags de section trouvés dans sa partition (ou
   `[instrumental]` quand elle n’en a pas), la légende omet la partie vocale, et il n’y a pas de relecture des
   paroles : la zone **Sections** peut être modifiée, et une modification est gardée. Le son de chaque chanson est décrit
   par le modèle local quand il est installé, puisque le modèle externe n’aurait qu’un titre pour s’orienter.
   Une LoRA entraînée ainsi peut écrire des notes dans la partie Vocal d’un plan, ce qui fait chanter ou fredonner un rendu ;
   l’avertissement « peut chanter » d’un plan le montre. Changer la Voix d’un corpus déjà analysé change ses
   paroles en conséquence.
2. **Choisissez les chansons.** Décochez celles que vous voulez laisser de côté. Quand une chanson est préparée, l’application garde sa propre copie de l’enregistrement complet dans le stockage interne des corpus, si bien qu’un corpus reste intact même si son dossier source est vidé ou déplacé par la suite. Un enregistrement de plus de 25 minutes est laissé de côté, car c’est très probablement un album entier ou un concert en un seul fichier. Si une feuille `.cue` se trouve à côté, **Découper en pistes** le découpe en ses chansons, qui prennent sa place dans le corpus. Les pistes vont dans le dossier propre de l’application ; le vôtre n’est pas modifié. (Les chansons plus longues que la limite GPU de l’entraîneur, comme des morceaux de 15 minutes, sont coupées proprement et fondues à une limite de section musicale lors de l’export.)
3. **Analyser.** La voix de chaque chanson est séparée, sa tonalité, son tempo et ses sections sont trouvés, et ses paroles sont rédigées, marquées par section. Avec un LLM externe réglé dans les Paramètres, les sections sont marquées à partir des mots entendus : les refrains parce que leurs mots reviennent, les nouvelles sections par les pauses. Seules les lignes et leurs temps sont envoyés, et les mots et leur ordre ne sont jamais changés. Sans LLM externe, ou si sa réponse ne contient pas toutes les lignes, les tags viennent de l’analyse musicale. **Réesquisser**, à côté d’Enregistrer dans la relecture d’une chanson, marque à nouveau les sections de la même façon sans réécouter la chanson, pour une chanson rédigée auparavant, et remplace le contenu de la zone. Une ligne sous les boutons dit ce qui tourne, et l’analyse en cours apparaît dans la carte des tâches et la file d’attente de l’écran principal. **Arrêter** l’arrête. Les étapes terminées sont gardées, donc **Analyser** reprend là où il s’est arrêté.

   **Réanalyser.** Une fois chaque chanson analysée, le bouton affiche **Analysé ✓**. Un clic demande si vous voulez réanalyser les suggestions de style de toutes les chansons avec les derniers prompts et réglages de LLM (pratique après avoir renommé un corpus ou changé de fournisseur). Un Maj-clic sur **Analysé ✓** propose une réanalyse complète depuis zéro (séparation, tonalité, tempo, transcription et styles relancés). Chaque chanson peut aussi être restylée avec **Réanalyser** dans sa relecture.
4. **Revoir** Ouvrez une chanson pour vérifier ses paroles et cocher **vérifiées**, et pour décrire son son
   là où il diffère du reste. La légende de style montre ce que lira l’entraîneur.
5. **Exporter le jeu d'entraînement.** Écrit l’audio, les paroles et la légende de chaque chanson. Une ligne sous les
   boutons montre l’avancement. L’entraîneur ne prend qu’une partie de chaque chanson, que l’application calcule
   d’après la mémoire libre de votre carte graphique (environ 5½ minutes sur une carte de 16 Go ; la fenêtre Journaux
   indique ce qu’elle a choisi). Une chanson plus longue est coupée à la fin de sa dernière section dans cette limite, fondue,
   et ne garde que les mots encore chantés. Sa ligne indique « first 3:12 trained ». Si l’entraînement
   manque de mémoire, réglez la variable d’environnement `TRAIN_MAX_MINUTES` sur un nombre plus petit, comme
   3.5 : voir le README.
6. **Entraîner un LoRA.** Cela prend longtemps, et le GPU n’est pas disponible pour l’application avant la
   fin. La progression s’affiche sous les boutons et sur l’écran principal, où vous pouvez l’arrêter,
   et le badge du corpus en haut de la page pulse pendant l’entraînement. Un nouvel entraînement garde
   la LoRA de l’exécution précédente sous un nom daté, dans **Exécutions précédentes**, ou la supprime, comme vous
   le choisissez.
   L’entraînement sur le modèle pleine qualité (BF16) recommandé demande au moins environ 12,5 Go de mémoire GPU
   (avec une coupe de 3½ minutes ; une coupe plus longue en demande plus), surtout pendant la préparation des chansons, donc une carte de 16 Go
   est le minimum pratique, avec 32 Go de RAM système (ComfyUI place les poids complets de YuE2
   et les caches du jeu de données en mémoire hôte ; sous WSL2, réglez `memory=32GB` dans `.wslconfig`). Une carte de 8 Go peut
   s’entraîner avec le modèle à faible mémoire (INT8). Les cartes qui ne peuvent pas s’entraîner peuvent quand même utiliser des LoRA entraînées
   ailleurs (**Installer un LoRA**). La fenêtre Entraîner prévient quand moins de mémoire GPU ou système est disponible,
   fermez donc d’abord tout ce qui utilise le GPU.

### Une exécution qui s’arrête tôt {#a-run-that-ends-early}

Une exécution peut s’arrêter avant sa dernière étape : **Arrêter**, un plantage, ou le GPU à court de mémoire. La ligne
sous les boutons dit alors quand et pourquoi, et après quelle étape. En chemin, l’entraîneur enregistre un
checkpoint toutes les 50 étapes, et garde une copie du meilleur jusqu’ici selon sa perte de planificateur, si bien que l’essentiel
du travail est en général encore là. **Terminer avec ce qu'il a enregistré** fait ce que fait une exécution terminée, à partir de
ces fichiers : la meilleure copie, ou à défaut le dernier checkpoint, devient la LoRA sous le
nom du corpus, avec son mot déclencheur, et les checkpoints se replient en dessous dans la liste des LoRA de style. Cela
prend quelques secondes et aucun temps GPU. Les dernières étapes d’une exécution changent le moins la LoRA, donc une LoRA terminée de cette
façon est en général proche d’une exécution complète ; **Checkpoints** fait le rendu d’une chanson une fois à chaque étape si vous voulez
comparer à l’oreille. Pour tout réentraîner à la place, appuyez sur **Entraîner un LoRA**.

### Tout lancer {#run-all}

**Tout lancer**, à côté des trois, enchaîne Analyser, Exporter et Entraîner, pour un corpus que vous
préférez ne pas surveiller : un grand corpus prend des heures à analyser. Il demande d’abord quoi faire d’une
LoRA précédente, puis continue page fermée. Il n’analyse que ce qui en a encore besoin, et une
chanson dont l’analyse échoue est laissée hors du jeu d’entraînement et nommée sous les boutons. Les paroles
que personne n’a vérifiées sont utilisées telles que rédigées. **Arrêter** l’arrête où il en est, en gardant ce qui est terminé ;
arrêté pendant l’export, il termine d’abord le jeu d’entraînement. Il attend tout ce qui utilise déjà
le moteur avant d’entraîner. Un redémarrage de l’application l’arrête, et **Tout lancer** à nouveau reprend.

### À court de mémoire GPU {#running-out-of-gpu-memory}

Une tâche à court de mémoire GPU le dit, avec quoi essayer : fermer d’autres programmes qui utilisent le GPU,
baisser la limite de durée, ou, pour l’entraînement, laisser de côté les chansons les plus longues. Si le moteur plante et
redémarre, la tâche qu’il exécutait est perdue, et elle le dit aussi.

### La LoRA entraînée {#the-trained-lora}

Quand l’entraînement se termine, la LoRA apparaît dans la liste **LoRA de style** avec son mot déclencheur. La choisir
montre une puce pour chaque chanson dont elle a appris, sous la zone Style, et cliquer dessus met le style de cette chanson dans
la zone.
Au-delà d’une douzaine de chansons, une zone de filtre et une rangée des tags qui reviennent dans le corpus (ses genres,
ambiances et instruments) les restreignent ; cliquez sur deux tags pour trouver les chansons qui ont les deux. La liste montre sa
première douzaine jusqu’à **Tout afficher**. Voir **Équilibrer Planificateur et Son** plus bas pour les forces de départ. Pour la partager, appuyez sur **Télécharger le LoRA** sur la page du corpus, ou **Télécharger** sous
le sélecteur ; voir **Partager une LoRA** plus bas.

Pour ajouter une LoRA que quelqu’un a partagée, appuyez sur **Importer un LoRA** à côté de **Nouveau corpus** et choisissez son zip. Pour utiliser une
LoRA entraînée ailleurs à partir du jeu exporté, appuyez sur **Installer un LoRA** et choisissez le
fichier. Elle est ajoutée à la liste des LoRA de style avec le mot déclencheur de ce corpus.

**Supprimer un corpus** retire les copies de ses chansons faites par l’application, les voix séparées, les paroles et
les partitions. Le dossier que vous lui avez indiqué, et toute LoRA faite à partir de lui, ne sont pas touchés.

---

## Droit d’auteur et consentement {#copyright-and-consent}

Ce sur quoi vous entraînez, et ce que vous faites du résultat, relève de votre responsabilité selon la loi de votre
pays. L’application vous demande de le déclarer et ne le vérifie pas : créer un corpus exige de confirmer
que vous avez le droit de vous entraîner sur ces enregistrements.

Deux faits sont bons à savoir :

- Les poids de YuE2 sont sous **CC BY-NC 4.0** — usage non commercial, quoi que vous entraîniez à partir d’eux.
- S’entraîner en privé sur un corpus et publier la LoRA ou ce qu’elle produit sont deux actes différents. Le second
  est celui qui demande généralement une autorisation : de qui détient les droits sur les enregistrements, et pour
  une voix reconnaissable, du chanteur.

Les LoRA que vous n’avez pas entraînées vous-même ont leurs propres licences : lisez-les sur la page d’où vient chacune
(voir **Où trouver des LoRA de style** dans LoRA de style).

## LoRA de style {#style-loras}

Une LoRA est un petit fichier qui oriente le modèle vers un son. Placez-en une dans `models/loras/` et appuyez sur
**Réanalyser** sous le sélecteur, ou utilisez **Installer**, et elle apparaît dans la liste **LoRA de style**.

Une LoRA de style peut contenir deux moitiés, et le sélecteur montre lesquelles contient un fichier :

- **Planificateur** façonne ce qui est joué — le plan de partition (forme, harmonie, phrasé), puis la musique
  que le rendu écrit à partir de cette partition. Il agit aux deux étapes.
- **Son** façonne l’audio — timbre et production.

Une force que le fichier ne peut pas utiliser est grisée, et un fichier que ce moteur ne peut pas charger du tout est signalé
comme tel au lieu d’échouer en silence pendant un rendu.

### Où trouver des LoRA de style {#where-to-find-style-loras}

Le plus rapide est à l’installation : cochez **LoRA de style** sur la page des composants de l’installateur (ou, avec Docker, lancez
`sh scripts/fetch-models.sh --loras`). Cela récupère 39 LoRA de style auprès de leurs auteurs, 3,8 Go en tout, chacune avec une
description donnant son mot déclencheur et des forces conseillées : les ensembles ci-dessous, deux d’atomtanstudio (dream pop
et hip-hop old school), et seize curseurs de concept de ntc-ai, qui ne façonnent que la partition (Son ne fait rien,
et ils n’ont pas besoin de mot déclencheur). Elles sont rassemblées, inchangées, dans
[pshields/yue2-style-loras](https://huggingface.co/pshields/yue2-style-loras), dont le README crédite chaque auteur
et renvoie à la page d’origine. Une LoRA déjà présente dans votre dossier sous le même nom est laissée telle quelle.

Il y en a d’autres sur Hugging Face. Voici les ensembles qui y sont rassemblés, chacun sur la page de son auteur :

- [Militant reggae](https://huggingface.co/becausereasons/yue2-mltnt-militant-reggae)
- [Chanson française](https://huggingface.co/becausereasons/yue2-chnsn-chanson-francaise)
- [Canzone italiana](https://huggingface.co/becausereasons/yue2-cnzn-canzone-italiana)
- [Bulgarian voices](https://huggingface.co/becausereasons/yue2-blgr-bulgarian-voices)
- [Qawwali, sufi and tabla](https://huggingface.co/becausereasons/yue2-qwwl-qawwali-sufi-tabla)
- [J-pop](https://huggingface.co/storagejuju/yue2-jpop-t4-lora), une seule LoRA avec uniquement une moitié Son

Pour en ajouter une, téléchargez son fichier `.safetensors` depuis l’onglet **Files** du dépôt, placez-le dans `models/loras/`
et appuyez sur **Réanalyser**, ou appuyez sur **Installer** et choisissez le fichier. La page du dépôt donne le
mot déclencheur et les forces conseillées de chaque LoRA : écrivez-les dans un `.txt` à côté du fichier (voir **Descriptions** plus bas) et
le sélecteur les affiche, et met le mot déclencheur en tête du Style pour vous. Une LoRA venue d’ailleurs
peut être enregistrée dans un format que ce moteur ne sait pas charger : le sélecteur la signale comme telle, et elle ne fait aucun mal.

Chaque LoRA porte la licence de son auteur, que ces ensembles donnent comme CC BY-NC 4.0 : usage personnel et non
commercial, comme les poids de YuE2 eux-mêmes. Lisez la licence sur la page d’une LoRA avant de l’utiliser, ou de partager ce
qu’elle produit.

### Équilibrer Planificateur et Son {#balancing-planner-and-sound}

- **Corpus homogènes :** une LoRA entraînée sur un seul album ou un son acoustique unifié (par ex. le folk rock des années 1960) supporte des forces plus élevées, en général autour de **Planificateur ~0.85 / Son ~0.80**.
- **Corpus variés :** si le corpus d’entraînement couvre plusieurs genres, styles de production ou époques (par ex. folk acoustique, rock et synth-pop), des poids de Son élevés peuvent créer des conflits acoustiques. Jusqu’à environ **Planificateur 0.70 / Son 0.70**, l’audio reste propre tout en gardant le phrasé mélodique et le caractère vocal de l’artiste.
- **Reprises :** votre enregistrement fixe la mélodie, la LoRA a donc moins à façonner et la moitié Son est davantage sollicitée. Gardez Son vers **0.50**.
- **Variété du plan :** avec une LoRA entraînée sur un corpus, **Calme** ou **Normal** donne le résultat le plus reconnaissable. **Calme** peut boucler avec une LoRA de style et un style court, et le plan dure alors
  des minutes avec de longues intros répétées, ou sans rien de chanté. Décrivez le style plus en détail (genre, instruments et sensation), ou utilisez **Normal**. Un tel plan, ou un plan bien plus long qu’une chanson, est réécrit une fois
  avec une nouvelle seed, et la prise échoue avec un conseil si le second ressort pareil.
- **Trouver une bonne prise :** le caractère de la LoRA dépend du tirage autant que des forces.
  Entre environ 0.3 et 0.6, **Son** change peu la voix, inutile donc de le pousser.
  **Planificateur** change l’interprétation elle-même, pas seulement la voix, donc une valeur qui convient à une chanson
  peut être la plus faible pour une autre. Traitez-la comme la seed : essayez-en quelques-unes (disons 0.6, 0.8 et 1.0) et
  quelques seeds avec **Rechanter**, et gardez la prise qui vous plaît.
- **Enregistrer les intensités :** quand vous trouvez la bonne paire pour une LoRA, appuyez sur **Enregistrer les intensités** sous le
  sélecteur. Choisir cette LoRA partira alors de ces valeurs, et elles voyagent avec elle quand vous la partagez.

### Mots déclencheurs {#trigger-words}

La plupart des LoRA de style sont entraînées sur des légendes qui **commencent** par un mot déclencheur, et font très peu
sans lui. L’application s’en charge : choisir une LoRA met son déclencheur en tête du Style,
passer à une autre l’échange, choisir Aucune le retire, et un rendu le remet s’il a été
supprimé. Vous verrez le mot apparaître dans la zone Style — libre à vous de le modifier ou de le déplacer.

### Descriptions {#descriptions}

La liste est groupée par ensemble. Cliquez sur un titre pour l’ouvrir ou le replier ; le sélecteur se souvient de ceux que vous
avez laissés ouverts, et le groupe qui contient votre choix actuel s’ouvre toujours avec lui.

Survolez une entrée pour lire ce qu’elle est, dans les mots de son auteur, avec ses forces conseillées. Ces
descriptions viennent d’un fichier texte à côté de la LoRA :

```
CHNSN Rive Gauche
Trigger: chnsn
Step 200, the decoder-loss minimum. The more supple of the two: acoustic
narrative, yé-yé, female leads, waltz meters.
```

La première ligne la nomme, une ligne `Trigger:` devient le mot déclencheur, et le reste est la
description. Une LoRA à vous en obtient une si vous écrivez un `.txt` à côté. `families.txt` dans le même
dossier donne leurs titres aux groupes, un `prefix = label` par ligne.

### LoRA entraînées sur un corpus {#loras-trained-from-a-corpus}

Une LoRA entraînée sur l’un de vos corpus est une LoRA de style ordinaire : elle apparaît dans cette liste avec les
autres, son mot déclencheur à côté, et les mêmes deux forces s’appliquent.

### Essayer les checkpoints {#trying-the-checkpoints}

Une exécution d’entraînement enregistre un checkpoint toutes les 50 étapes, et les garde sous sa LoRA dans le sélecteur :
**▸ 9 étapes** à côté du nom de la LoRA les ouvre (les Paramètres peuvent les supprimer à la place, pour gagner de
la place). Un checkpoint dont la LoRA a été supprimée reste sous **Checkpoints d'entraînement**. Pour en
retirer, appuyez sur **Modifier** sur le corpus : **Checkpoints d'entraînement** y liste ceux de chaque exécution, celle-ci
et les précédentes, avec leurs tailles. Cochez ceux qui doivent partir et appuyez sur **Supprimer**. La LoRA
finie n’est pas listée ; elle a son propre **Supprimer le LoRA**. Chacun est la LoRA telle qu’elle était à
ce moment de l’entraînement. Ils sonnent à peu près aussi bien les uns que les autres, mais chacun pondère à sa façon
ce qu’il a appris, et a donc son propre goût tout en gardant le style et le son caractéristique sur lesquels la LoRA
a été entraînée.

Pour les entendre côte à côte, choisissez la LoRA, préparez l’éditeur comme pour une seule prise, et appuyez sur
**Checkpoints** à côté de **Supprimer le LoRA**. Il est grisé pour une LoRA sans checkpoints. Cochez les
étapes voulues, réglez une limite de durée pour ces prises si vous voulez, et appuyez sur **Rendu**. L’action
propre de l’éditeur s’exécute une fois sur chaque checkpoint, toutes avec une même seed, et chaque prise porte le nom de son étape :
*Night drive · step 250*, *Night drive · full*. Elles sont gardées dans la prise ouverte dans l’éditeur,
ou, pour une nouvelle chanson, dans la dernière d’entre elles (voir **Des prises dans une prise**, dans La bibliothèque). L’éditeur se ferme, et vous revenez à la bibliothèque
où les prises se font. Une chanson ou un instrumental écrit son plan et passe directement au
rendu.

Dans une chanson ou un instrumental, la LoRA écrit l’air en plus de façonner le son, donc la même
seed ne donne pas la même chanson : chaque checkpoint écrit sa propre mélodie et sa propre structure. La seed
choisit parmi ce que le modèle juge probable, et chaque checkpoint pense un peu différemment dès la
première note, si bien que les plans divergent en quelques mesures. Ce qui reste, c’est le son. Pour ne comparer que le
son, chargez un plan avec **Partition** et appuyez sur **Rendre cette partition** avec chaque checkpoint tour à tour.

Les nouveaux fichiers apparaissent une fois que le moteur a réexaminé `models/loras/`, ce qu’il fait quand les
options sont rechargées.

### Partager une LoRA {#sharing-a-lora}

Choisissez une LoRA et appuyez sur **Télécharger** sous le sélecteur : vous obtenez un seul zip avec la LoRA et sa note.
Pour une LoRA entraînée sur un corpus, la note contient ses styles appris, donc les puces viennent avec.

Pour en ajouter une qu’on vous a envoyée, appuyez sur **Installer** et choisissez son zip, ou un simple fichier `.safetensors`.
Elle va dans `models/loras` sous le titre **Installées**, avec son nom, son mot déclencheur et ses
puces. **Supprimer le LoRA** retire la LoRA choisie, sa note et sa ligne de groupe ; **Réanalyser** relit le dossier
après que vous avez ajouté un fichier à la main.

---

## Stems {#stems}

Appuyez sur **Stems** sur n’importe quelle prise. Choisissez un modèle, cochez les parties voulues — voix, batterie, basse, autres,
et guitare et piano sur certains modèles — et lancez.

La séparation tourne sur le **GPU** quand le moteur dispose de Demucs, comme une tâche dans la file du moteur : elle attend un
rendu en cours, puis va vite, et un rendu en file derrière elle attend à son tour. Un moteur construit avant
cela, une LoRA en cours d’entraînement (qui occupe le GPU), **Utiliser le GPU pour les stems et les paroles** réglé sur Non dans les Paramètres, ou `STEMS_ON_GPU=0` la laisse sur le **CPU**, ce qui est plus lent
et ne retarde jamais un rendu. *Affiné* fait tourner quatre modèles à la suite pour une meilleure séparation et prend environ quatre fois
plus de temps.

Pour une piste d’accompagnement, choisissez **Voix et instruments**. Elle coupe la chanson en deux : la voix, et
les **instruments**, tout le reste en un seul stem. Décochez **voix** pour ne garder que les instruments. C’est
la même séparation que pour les quatre stems, réassemblée, elle prend donc autant de temps et sonne aussi propre.
La version *affinée* laisse le moins de voix derrière elle.

Les stems arrivent dans `data/stems/<title>-<id>/`, se lisent depuis les puces de la carte, et se téléchargent un par un ou en
zip. Ils restent jusqu’à ce que vous les supprimiez.

---

## Arrêter, supprimer et recommencer {#stopping-deleting-and-starting-again}

Ce sur quoi travaille le moteur s’affiche dans la barre du haut, à côté du nom : une pastille avec la tâche, son temps, une ligne
en bas pour l’avancement, et le nombre de tâches qui attendent après elle. Elle ne change rien d’autre à la page quand une
tâche commence ou finit. Cliquez dessus pour la carte de tâche : l’étape, **arrêter**, et **À suivre**, les tâches en attente, chacune avec
**annuler**.

Une prise en file ou en cours affiche **Annuler** sur sa carte, et **arrêter** sur la carte de tâche arrête ce sur quoi
travaille le moteur. Le titre d’une prise sur la carte de tâche, dans sa liste **À suivre**, ou dans le lecteur en
bas de la page vous mène à la prise : dans son espace, en effaçant toute recherche ou tout filtre qui la cache. Supprimer une prise arrête sa tâche et retire ses stems. **Supprimer** à côté d’un
enregistrement retire le fichier et ses stems ; les reprises faites à partir de lui gardent leur audio et leur partition, mais ne peuvent plus
être rendues à nouveau.

**+ Chanson**, **+ Reprise** et **+ Instrumental** dans le panneau de prise, ou **Nouvelle chanson** à côté du
titre de l’éditeur, recommencent à partir de la prise affichée. Ils effacent le titre, les paroles et la partition,
et repartent des valeurs par défaut : un style vide (avec le mot déclencheur d’une LoRA choisie), la limite de durée
habituelle, Harmonie Varié, variété du plan normale, interprétation Large, finition de production activée,
normalisation désactivée, et une nouvelle seed non retenue. Une LoRA choisie et un enregistrement choisi restent choisis.
La prise affichée se détache de l’éditeur, pour que Rendu ne puisse pas agir sur elle par erreur.

Les mots que vous aviez saisis sans les utiliser ne sont pas jetés : une barre propose de les restaurer.

## La bibliothèque {#the-library}

### Espaces {#spaces}

Les prises vivent dans des **espaces** : un espace par chanson, par album, ou pour des esquisses. Le nom de l’espace au-dessus des prises
est celui affiché, et tout ce que vous créez y arrive. Cliquez dessus pour la liste des espaces : tapez pour en trouver un par
nom, ou choisissez-le avec les flèches et Entrée. Les cinq derniers utilisés viennent en premier, puis tous les espaces, chacun avec
son nombre de prises. **Nouvel espace**, **Renommer cet espace**, **Importer une prise…** et **Supprimer cet espace** sont au
pied de la liste. Supprimer un espace ne supprime jamais de prises —
elles passent dans Default. Les enregistrements sont partagés par tous les espaces, donc un même enregistrement peut être repris dans
plusieurs.

Le bouton dossier d’une carte déplace cette prise vers un autre espace, avec les prises qu’elle contient.

### Des prises dans une prise {#takes-inside-a-take}

**Variations**, **Essayer encore** et **Checkpoints** créent chacun plusieurs prises d’une chanson. Elles sont gardées
**dans** la prise d’où elles viennent, pour que l’espace liste vos chansons et non chaque rendu de chacune.
Checkpoints se lance dans l’éditeur : avec une prise ouverte, ses prises vont dans cette prise ; pour
une nouvelle chanson, qui n’a pas encore de prise, la prise du dernier checkpoint coché (la LoRA finie, quand
elle en fait partie) contient les autres.

- **Le bouton Contenu** apparaît parmi les petits boutons en haut d’une carte dès que sa prise contient
  des prises, terminées ou en cours, et il est **allumé en orange**. Survolez-le pour lire combien sont
  faites et combien restent à venir. La carte elle-même est nettement plus claire que les autres (dans le
  thème clair, une teinte chaude), pour qu’une prise contenant des prises se remarque dans une liste. (Le bouton du rack de mastering à côté s’allume en vert de
  la même façon quand la prise est masterisée.)
- **Cliquez dessus** et un panneau s’ouvre sous la carte avec les prises qu’elle contient, chacune sur sa propre carte. Une
  prise s’y affiche quand elle est terminée ; pendant sa création, seule la prise à laquelle elle appartient s’affiche.
  Cliquez à nouveau sur le bouton, ou sur **Fermer**, pour le fermer.
- **Une prise dans une autre est une prise comme les autres.** Lisez-la, mettez-lui une étoile, enregistrez-la, séparez-la en
  stems, renommez-la, et double-cliquez pour ouvrir sa chanson et sa partition.
- **Un seul niveau.** Une prise dans une autre n’en contient aucune, sa carte n’a donc ni Variations ni Essayer
  encore, et **Checkpoints** dans l’éditeur est grisé tant qu’elle y est ouverte. **Sortir** (la flèche qui sort d’une boîte) en fait une prise à part entière dans la liste de l’espace, et alors elle le peut.
- **Les outils de la liste suivent le panneau.** Tant qu’un panneau est ouvert, **Tout sélectionner**, **Favoris**, les boutons
  de type, **Comparer**, **Supprimer** et précédent et suivant du lecteur agissent sur les prises du
  panneau. La prise dont le panneau est ouvert reste sur la page quels que soient les filtres.
- **Ce qui joue dedans se voit dehors.** Si vous fermez le panneau pendant qu’une de ses prises
  joue, le bouton Lecture de la prise qui la contient brille en doré, pour que vous voyiez d’où vient le son.
  Le vert signifie toujours que cette prise elle-même joue.
- **La recherche les trouve** comme toute autre prise, où qu’elles soient. Pendant une recherche, ce qu’elle
  trouve s’affiche en cartes simples, et une prise contenue dans une autre dit laquelle.
- **Supprimer une prise supprime les prises qu’elle contient.** L’avertissement dit combien. Sortez d’abord celles que vous voulez
  garder.

Les prises faites avant cette fonction restent où elles sont, côte à côte dans la liste.

### Cartes {#cards}

Chaque carte nomme les réglages qui ont façonné sa prise — Harmonie, Interprétation, Variété du plan, la LoRA et
ses forces, la seed, le moteur qui a fait le rendu et son âge — pour qu’une carte se lise comme la recette qui l’a faite.

**Enregistrer** demande dans quel format télécharger la prise, FLAC, WAV ou MP3. Il part de ce que vous avez enregistré la dernière
fois, et sans choix la première fois. Une prise avec une image peut aussi être enregistrée en **Vidéo** : un MP4 de
la chanson qui montre l’image de sa carte (vidéo H.264, audio AAC à 192 kbps). Les messageries comme
WhatsApp l’envoient et le lisent comme une vidéo, là où un fichier audio part comme document. Avec le rack de mastering actif, la
vidéo a le son masterisé, comme les autres formats. **Prise**, à côté, enregistre en plus la recette de la prise : un petit fichier
(`<title>.yeufonic.json`) qui contient ses paroles, son style et sa partition, ses seeds et réglages, ses LoRA par nom et
les réglages du rack de mastering, mais pas son audio. Avec un format choisi aussi, les deux arrivent dans un zip ; appuyez à nouveau sur le
format choisi pour n’enregistrer que la recette. Le fichier ne contient rien de votre installation (ni chemins, ni identifiants, ni clés),
il peut donc être gardé, ou partagé avec un autre utilisateur de Yeufonic.

**Importer une prise…**, dans la liste des espaces, crée à partir d’un tel fichier une nouvelle prise dans l’espace affiché ; déposer le fichier
sur la bibliothèque fait de même. La prise contient le plan, prêt pour le rendu, pour qu’on puisse d’abord le vérifier ou le modifier.
Les deux moteurs peuvent en faire le rendu : la même partition et la même seed sur le même moteur donnent une prise très proche, sur l’autre
moteur une prise différente. Une LoRA qu’il nomme et qui n’est pas installée ici est signalée à l’import, pour que vous puissiez
l’installer ou en choisir une autre avant le rendu. L’enregistrement d’une reprise n’est pas dans le fichier, donc une reprise partagée arrive
comme une chanson avec la partition et les paroles de la reprise, en laissant derrière elle les réglages propres à son enregistrement (le
verrouillage du tempo, l’Harmonie, les indications de voix et la limite de durée) : un nouveau plan à partir d’elle commence comme une chanson à partir d’un prompt.

**Rechercher des prises** trouve les prises dont tous les mots saisis figurent quelque part dans le titre, le style, les paroles ou le
nom de LoRA, sans tenir compte de la casse. Elle cherche dans l’espace affiché ; **Tous les espaces**, à côté dès que vous tapez,
cherche dans tous les espaces, et une carte venant d’un autre espace dit lequel. × ou Échap l’efface. La
zone est vide à chaque ouverture de la page, et propose vos dernières recherches qui ont trouvé quelque chose :
cliquez sur l’une, ou choisissez-la avec les flèches et Entrée.

**Chanson**, **Reprise** et **Instrumental** montrent les prises de ces types : allumez-en un ou plusieurs, ou aucun pour tous les types.
**Favoris** ne montre que les prises étoilées ; cliquez à nouveau pour toutes les montrer. Les icônes à côté règlent la disposition
des prises, celles utilisées allumées en vert : des cartes **confortables** plus larges avec plus du prompt ou des **compactes** plus étroites,
**toute la largeur** de la fenêtre ou une colonne centrée, et chaque prise **repliée** sur sa ligne de titre. Survolez
une icône pour lire ce que fait un clic.

Cochez des prises et la rangée propose ce qu’on peut en faire, à la place des types et de la disposition : combien sont
choisies, **Comparer**, **Supprimer** et **Terminé**, qui les décoche. **Tout sélectionner**, au bout de la rangée, coche
chaque prise affichée. Un titre reste toujours sur une ligne, terminé par … s’il est long. Survolez le titre, les réglages ou le style d’une carte pour tout lire.

### Une image pour chaque prise {#a-picture-for-each-take}

Chaque nouvelle prise reçoit une image de la chanson, affichée en transparence derrière sa carte, en haut du panneau de prise quand vous la choisissez, et derrière l’éditeur quand la prise y est
ouverte. Dessinée sur ce PC, elle attend qu’aucune chanson ne soit en cours de création, donc elle ne retarde jamais un plan ou un rendu, et
apparaît peu après que la chanson est terminée ; dessinée par un LLM externe, elle se fait pendant le rendu de la prise.
Elle se fait en deux étapes : le titre, le style et les premiers mots de la prise deviennent une **description** d’une
image, puis un modèle d’image la **dessine** sur fond blanc, et le blanc est retiré, laissant l’image
sur un fond transparent. Une prise faite dans une autre (Essayer encore, Variations, Checkpoints) montre
l’image de la prise qui la contient au lieu d’en avoir une à elle.

Un modèle d’image ne dessine pas un vrai groupe ou une vraie personne, donc la description omet les noms ; et le
lettrage propre à l’image reste discret, pour ne pas concurrencer celui de la carte.

#### Deux façons de dessiner : FLUX.2 klein sur ce PC, ou un LLM externe {#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm}

Les images ont besoin de quelque chose qui sache dessiner. Il y en a deux, et vous pouvez avoir l’un, les deux ou aucun.

| | FLUX.2 klein, sur ce PC | Le modèle d’image de votre LLM externe |
|---|---|---|
| Ce que c’est | un petit modèle d’image qui tourne sur le moteur, à côté de YuE2 | le modèle d’image du fournisseur, comme celui de Gemini |
| Ce que ça coûte | rien ; environ 8 Go de disque | chaque image est une requête au fournisseur, qui peut être facturée |
| Ce qui quitte le PC | rien : la description est écrite par Gemma sur ce PC, ou faite à partir de la prise elle-même | le titre, le style et les premiers mots de la prise, et la description |
| Quand il tourne | sur le GPU dès qu’aucune chanson n’est en cours : après votre chanson, jamais dans ses pattes | à côté des rendus, pendant qu’ils tournent |
| Ce que vous configurez | une option d’installation | le LLM externe dans les Paramètres, avec un fournisseur qui propose un modèle d’image |

**Pour dessiner sur ce PC, installez FLUX.2 klein.**

- **Windows :** cochez **FLUX.2 [klein]** sur la page des composants de l’installateur. Il n’est pas coché
  à moins que vous ne le choisissiez. Une application installée retrouve la même page lors d’une mise à jour, ou relancez l’installateur
  depuis la page de version : la case est ensuite mémorisée, et une mise à jour ne le télécharge jamais deux fois. Ce
  sont trois fichiers, environ 8 Go en tout.
- **Docker :** lancez `sh scripts/fetch-models.sh --pictures`, qui place les trois fichiers dans `models/`
  (`diffusion_models`, `text_encoders` et `vae`) et vérifie chacun, puis redémarrez l’application avec
  `docker compose restart app` pour qu’elle les trouve.

**FLUX.2 klein 9B, si vous avez la carte graphique pour.** klein existe en plus grande taille, un modèle de meilleure qualité
qui dessine plus de détails et de meilleures mains et visages, destiné seulement aux cartes graphiques avec plus de mémoire
vidéo. Yeufonic ne le télécharge jamais, car ses fichiers sont à accès restreint sur Hugging Face et sous la **licence non commerciale**
de Black Forest Labs, mais mettez-les en place et ils sont utilisés.

- **Disque :** environ 18 Go pour la paire habituelle, le modèle FP8 et son encodeur de texte FP8 (16 Go avec l’encodeur
  FP4), à côté des fichiers du 4B. Il a besoin du VAE du 4B (`flux2-vae.safetensors`), installez donc d’abord le 4B.
- **Mémoire vidéo :** il fonctionne sur une carte de 16 Go, mais en prend presque tout pendant qu’il dessine, la mémoire libre
  tombant presque à zéro. Les images attendent qu’aucune chanson ne soit en cours, cela ne ralentit donc pas vos chansons, mais d’autres
  programmes qui utilisent la carte graphique en même temps peuvent peiner. Avec moins de mémoire il tourne quand même, plus
  lentement, le moteur chargeant et déchargeant le modèle ; le 4B est alors le meilleur choix.

1. **Le modèle.** Connectez-vous à Hugging Face, acceptez la licence sur
   [black-forest-labs/FLUX.2-klein-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8)
   et téléchargez `flux-2-klein-9b-fp8.safetensors` (9,4 Go). Ou prenez la version pleine précision
   `flux-2-klein-9b.safetensors` de [black-forest-labs/FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B),
   celle pour un Mac, environ deux fois plus grande et qui demande deux fois plus de mémoire.
   Il va dans le dossier `diffusion_models`.
2. **Son encodeur de texte.** Depuis [Comfy-Org/Flux-2-Klein-9B](https://huggingface.co/Comfy-Org/Flux-2-Klein-9B/tree/main/split_files/text_encoders),
   sans connexion requise, téléchargez l’un de ceux-ci et placez-le dans le dossier `text_encoders` :
   `qwen_3_8b_fp8mixed.safetensors` (8,7 Go, le choix habituel sur une carte NVIDIA), `qwen_3_8b_fp4mixed.safetensors`
   (6,8 Go, le plus petit) ou `qwen_3_8b.safetensors` (16,4 Go, pleine précision, pour un Mac).
   **Avec le moteur yue2.cpp**, le serveur d’images ne peut pas lire ces encodeurs : prenez plutôt `Qwen3-8B-Q4_K_M.gguf`
   (5,0 Go) sur [unsloth/Qwen3-8B-GGUF](https://huggingface.co/unsloth/Qwen3-8B-GGUF)
   (`-Q8_0.gguf`, 8,7 Go, fonctionne aussi), et placez-le dans le même dossier.
3. **Où sont les dossiers :** sous `models/` dans le dossier Yeufonic pour **Docker** ; sous
   `engine\ComfyUI\models` dans le dossier d’installation sous **Windows** ; sous `engine/ComfyUI/models/` dans le
   dossier d’installation sur un **Mac**.
4. **Laissez l’application les voir, et choisissez-le.** Redémarrez Yeufonic (avec Docker, `docker compose restart app`),
   puis réglez **Images des prises : modèle klein** dans les Paramètres sur *FLUX.2 klein 9B*. Le 4B dessine jusque-là, et
   les Paramètres le signalent quand le 9B est choisi mais ne peut pas dessiner ici. Choisissez
   *4B* pour revenir en arrière sans rien supprimer. La note de l’image dans l’éditeur dit lequel l’a dessinée
   (*drawn by FLUX.2 klein 9B on this PC*).

Le modèle et son encodeur ne sont trouvés que sous ces noms, gardez donc les noms de fichiers tels que téléchargés.

**FLUX 3 klein, pour le lettrage et une carte de 12 Go ou plus.** FLUX 3 Image Klein de Black Forest Labs dessine à partir d’une
description complète de la scène, ce que sont justement les prompts d’image écrits par Gemma ou le LLM externe, et il
écrit bien les lettres, ce qui convient à **Images des prises : titre de la chanson sur l'image**. Comme pour le 9B, Yeufonic ne le télécharge jamais : ses fichiers sont
à accès restreint sur Hugging Face et sous la **FLUX Kommunity License** (usage non commercial, et usage commercial de ce qu’il
dessine pour quiconque se trouve sous le plafond de revenus de la licence ; lisez-la avant de l’accepter). Mettez ses fichiers en place et il
peut être choisi.

- **Disque :** environ 11 Go pour la paire int8, à côté des fichiers du 4B. Il utilise le VAE du 4B (`flux2-vae.safetensors`),
  installez donc d’abord le 4B.
- **Mémoire vidéo :** environ 11 Go pendant qu’il dessine. Il fait plusieurs fois plus d’étapes que les FLUX.2 klein, chaque
  image prend donc plus de temps.
- **Moteur :** seulement le moteur ComfyUI pour l’instant ; avec le moteur yue2.cpp il n’est pas proposé.

1. **Connectez-vous à Hugging Face** et acceptez la licence sur
   [black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
2. **Le modèle,** dans le dossier `diffusion_models` : `flux3-image-klein-int8-convrot.safetensors` (5,8 Go, le choix
   habituel sur une carte NVIDIA), `flux3-image-klein-nvfp4.safetensors` (5,3 Go, pour une carte RTX 50) ou
   `flux3-image-klein-bf16.safetensors` (11,1 Go, pleine précision, pour un Mac).
3. **Son encodeur de texte,** dans le dossier `text_encoders` : `qwen3vl_4b_int8_convrot.safetensors` (4,9 Go) ou
   `qwen3vl_4b_bf16.safetensors` (8,9 Go, pour un Mac).
4. **Laissez l’application les voir, et choisissez-le :** redémarrez Yeufonic (avec Docker, `docker compose restart app`), puis réglez
   **Images des prises : modèle klein** dans les Paramètres sur *FLUX 3 klein*. La note de l’image dans l’éditeur dit *drawn by
   FLUX 3 klein on this PC*.

Les dossiers sont les mêmes que pour le 9B, et les fichiers ne sont trouvés que sous ces noms.

**Pour dessiner avec un LLM externe,** ouvrez les Paramètres et réglez **LLM pour écrire les paroles et les tags de style** sur le
[LLM externe](#external-llm), avec son **URL d’API**, sa **clé d’API** et son **modèle**, comme pour les paroles. Le fournisseur doit avoir un modèle
d’image : Gemini en a un (`gemini-3.1-flash-image` est utilisé sauf si vous en nommez un autre), et à un fournisseur compatible OpenAI
on demande `gpt-image-1`. L’application demande au fournisseur sa liste de modèles, en arrière-plan,
au démarrage, quand ces réglages changent et toutes les quelques heures, et n’y dessine qu’une fois que la liste
contient le modèle d’image.

Sans l’un ni l’autre, **Images des prises** dans les Paramètres indique **Pas d'images : l'arrière-plan par défaut**, avec une ligne expliquant comment en
avoir, et le choix d’en créer ne peut pas être sélectionné.
Configurez l’un ou l’autre et elles s’activent : des images sont alors créées pour les prises que vous faites à partir de ce moment.

#### Gérer les images dans les Paramètres {#managing-pictures-in-settings}

| Réglage | Effet |
|---|---|
| **Images des prises** | *En créer une pour chaque nouvelle prise* (par défaut quand quelque chose peut dessiner), ou *Seulement sur demande*, où une prise garde le fond par défaut jusqu’à ce que vous en créiez une depuis son carré ou le bouton Image de l’éditeur. Les réglages ci-dessous façonnent une image créée dans les deux cas. C’est *Pas d’images* tant que rien ici ne peut dessiner. |
| **Images des prises : dessinées par** | *Ce PC si klein est installé, sinon le LLM externe* (par défaut), *Ce PC (le modèle klein ci-dessous)* ou *Le modèle d’image du LLM externe*. Le klein qui dessine sur ce PC (FLUX.2 klein 4B ou 9B, ou FLUX 3 klein) se choisit sous **modèle klein**. |
| **Images des prises : modèle klein** | *FLUX.2 klein 4B* (par défaut), *FLUX.2 klein 9B*, *FLUX 3 klein*, ou *9B là où ses fichiers sont installés, sinon 4B*. Seulement pour les images dessinées sur ce PC. Le 9B et FLUX 3 ne sont jamais installés pour vous : voir [FLUX.2 klein 9B et FLUX 3 klein](#two-ways-to-draw-flux-2-klein-on-this-pc-or-an-external-llm) plus haut. Si celui demandé n’est pas là, un autre dessine, et les Paramètres disent lequel. |
| **Images des prises : décrites par** | qui écrit le prompt d’image, à partir du titre de la prise, du style artistique ci-dessous, de son style et de ses paroles (jusqu’à 50 lignes). *Gemma local s’il est installé, sinon la prise elle-même* (par défaut), quel que soit celui qui dessine. *Gemma local* : écrit sur ce PC ; nécessite l’option Brouillons de paroles. *À partir de la prise elle-même* : pas de LLM ; une description faite à partir du titre, du style et des premiers mots de la prise, la plus rapide, et rien n’est envoyé. Ou le *LLM externe*, une requête par image ; quand il est injoignable, ou si vous passez aux LLM locaux pour la session, Gemma les écrit à la place s’il est installé. |
| **Images des prises : style artistique** | à quoi l’image doit ressembler, donné au LLM qui écrit le prompt d’image (grisé quand la prise se décrit elle-même). Par défaut un design abstrait et surréaliste à la manière des pochettes d’album des années 1970 et 1980, sans texte ni personnes. Vidé, il revient à cela. |
| **Images des prises : votre propre prompt** | des mots par lesquels commence le prompt d’image de chaque image, comme *big sky, doom-laden*, jusqu’à 512 caractères ; le prompt écrit par le LLM les suit. Vide (par défaut) : aucun. Seulement quand un LLM écrit le prompt d’image (grisé quand la prise se décrit elle-même). |
| **Images des prises : titre de la chanson sur l'image** | *Non* (par défaut) ou *Oui* : le titre de la chanson est écrit en gras sur la pochette, en capitales ou en minuscules, tel que vous l’avez écrit, même quand c’est le nom d’un artiste (l’image elle-même est toujours décrite sans lui). La plupart du temps, l’image est encadrée par un mince filet sombre dans une bordure blanc cassé, comme sur beaucoup de pochettes des années 1970, avec le titre centré dans une bande plus large en haut ou en bas. Environ une sur cinq n’a pas de bordure : le titre se place sur l’image, dans un coin ou centré en haut ou en bas, dans une couleur sourde tirée de l’image, et on demande au LLM de garder cette partie de l’image dégagée pour lui. Tout cela est tiré au hasard pour chaque image. FLUX.2 klein peut l’écrire imparfaitement. Seulement quand un LLM écrit le prompt d’image. |
| **Images des prises : modèle d'image** | lequel des modèles du fournisseur dessine. Seulement pour les images dessinées par le LLM externe (choisissez-le sous **Dessinée par** ; grisé sinon), et vide pour le modèle habituel du fournisseur, ce qui est presque toujours ce que vous voulez. |

Donc avec FLUX.2 klein installé et les réglages tels qu’ils arrivent, les images sont faites entièrement sur ce PC, même
quand le LLM externe écrit vos paroles : Gemma écrit chaque prompt d’image là où les Brouillons de paroles sont installés, et
sans lui la description est faite à partir de la prise elle-même, sans LLM, ce qui ne prend pas de temps. Choisissez *Le modèle d’image du
LLM externe* pour que le fournisseur les dessine à la place, ou réglez **décrite par** sur *À partir de la prise elle-même* pour les
images les plus rapides, ou sur *LLM externe* (une requête par image).

#### L’image d’une prise dans l’éditeur {#a-take-s-picture-in-the-editor}

L’icône **Image** dans la rangée du haut de la fenêtre de l’éditeur, à côté des autres boutons de la prise, montre l’image
avec deux choix : **Faire une nouvelle image**, qui la refait en arrière-plan, et **Utiliser l'arrière-plan par défaut**, qui la retire pour de bon : aucune image n’est plus créée pour cette prise à moins que vous n’en demandiez une.
Cliquez sur l’image pour la voir en entier, aussi grande que la fenêtre le permet ; un clic n’importe où ou Échap
la range et laisse l’éditeur tel quel. L’image entière a les deux mêmes choix en dessous. Choisissez
**Faire une nouvelle image** à cet endroit et l’image reste affichée pendant que la nouvelle se fait, avec ce qui se passe affiché
entre les boutons, puis elle passe à la nouvelle quand elle est prête.

Sur la carte d’une prise, le carré en haut à gauche montre l’image quand vous le survolez. Une prise sans
image propose **Faire une nouvelle image** à cet endroit à la place, là où ce PC peut créer des images.

### Comparer des prises {#comparing-takes}

Cochez deux à six prises et appuyez sur **Comparer** (il apparaît à côté de Tout sélectionner dès que deux sont cochées, et
attend les prises encore en rendu). Les prises s’empilent dans une fenêtre sur une position commune : appuyez sur **1** à
**6** ou cliquez sur l’une pour basculer, et elle reprend au même moment de la chanson, en lecture ou
en pause. **Espace** lit et met en pause, les flèches avancent de 5 secondes, et l’étoile marque celle que vous
préférez. **Égaliser le volume** baisse les prises les plus fortes au niveau de la plus douce, car une prise plus forte tend
à sembler meilleure ; **Masquer les noms** mélange les prises et les appelle Prise A, B, C pour une écoute à l’aveugle.

### Le lecteur {#the-player}

Cliquez ou faites glisser sur la forme d’onde pour vous déplacer. Précédent et suivant parcourent les cartes dans l’ordre affiché.

| Touche | Effet |
|---|---|
| Espace | lecture ou pause |
| Gauche, Droite | reculer ou avancer de cinq secondes |
| Maj+Gauche, Maj+Droite | la prise précédente ou suivante ; dans la vue Playlists, la chanson précédente ou suivante de la playlist |
| Haut, Bas | volume |

Les touches multimédia du système fonctionnent aussi. Les touches propres à la prise sont dans [Raccourcis clavier](#hot-keys).

### Le visualiseur audio et les paroles synchronisées {#the-audio-visualizer-and-synced-lyrics}

Appuyez sur **Visualiseur** dans la barre de transport (ou sur **V** pendant la lecture) pour lancer la scène plein écran du visualiseur.

La scène affiche des visualisations audio en temps réel synchronisées avec la lecture :

- **Modes du visualiseur :** choisissez parmi dix visualiseurs dans la barre du haut :
  - *Yeufonic :* le logo lui-même, qui respire — la tuile brille avec les basses et s’étend sur le temps, chaque branche de la fourche est un vumètre avec sa moitié du spectre, et le point vert s’embrase sur le temps.
  - *Ruban d’onde :* deux rubans harmoniques flottants qui réagissent au son.
  - *Aurore boréale :* des rideaux ondulants d’aurore boréale éthérée qui réagissent aux médiums et aux aigus.
  - *Nébuleuse cosmique :* un champ d’étoiles et une nébuleuse de particules interstellaires tourbillonnante qui pulse au rythme.
  - *Kaléidoscope :* des symétries géométriques radiales qui pulsent avec le tempo.
  - *Grille néon :* un plan filaire synthwave rétrofuturiste en perspective qui ondule avec les lignes de basse.
  - *Distorsion liquide :* une surface fluide déformée par des ondes harmoniques.
  - *Essaim de particules :* des amas de particules gravitationnels qui se dispersent sur les frappes de percussion.
  - *Barres de spectre hi-fi :* un analyseur de spectre multibande avec des crêtes flottantes qui retombent.
  - *Pochette :* l’image de la prise, en grand, avec son titre en dessous, sur une copie floue d’elle-même qui bouge avec la musique. Une prise sans image montre la scène Yeufonic jusqu’à ce qu’une soit créée.
- **Derrière les scènes :** les scènes Pochette, Yeufonic, Mandala, Grille, Liquide et Barres se jouent sur l’image de la prise, qui bouge doucement avec la musique, quand la prise en a une. Quelque chose peut aussi bouger par-dessus, dans les couleurs de l’image : *Souffle* (l’image seule), des *Rayons de lumière* qui tournent depuis le centre, des *Ondulations* lancées sur le temps, une *Couleur dérivante*, de la *Profondeur* (d’autres copies de l’image qui tournent l’une contre l’autre) ou un *Halo spectral*. Chaque scène commence avec le sien (couleur dérivante derrière Pochette, le halo derrière Mandala, les rayons derrière Grille, les ondulations derrière Liquide, l’image seule derrière Yeufonic et Barres) ; appuyez sur **B** pour les parcourir, et la scène retient votre choix.
- **La forme d’onde :** sous les scènes Yeufonic et Pochette, la forme d’onde de la prise montre où en est la chanson ; cliquez dessus pour y sauter.
- **Pochette d’album et dynamique du vinyle :** affiche la pochette de la prise façon Hipgnosis dans une pochette 3D interactive qui s’incline et tourne avec le pointeur. Un disque vinyle réaliste tourne à 33⅓ tours et sort de la pochette sur les coups de basse, avec un reflet holographique et des anneaux d’onde de choc qui réagissent au rythme. Changez de mode avec le bouton **Pochette** : *Pochette*, *Aura* (fond flouté) ou *Désactivé*.
- **Une nouvelle image :** le bouton image en haut à droite, dans chaque scène, crée une nouvelle image pour la prise en lecture, là où ce PC peut créer des images. Il pulse pendant la création, et la nouvelle prend le relais quand elle est prête.
- **Affichage des paroles :** appuyez sur **L** ou cliquez sur **Paroles** pour afficher ou masquer le panneau de paroles indépendant et défilant. Faites-le glisser par la barre du haut pour le déplacer ; il reste où vous le posez, et un double-clic sur la barre le remet en place.
- **Ruban du mini-lecteur :** tant que le visualiseur plein écran est fermé, un mini-visualiseur à double onde réactif joue dans la barre de transport du bas. Il s’active ou se désactive dans **Paramètres → Apparence**.

### Playlists et favoris {#playlists-liked-songs}

Cliquez sur **Playlists** dans la barre du haut pour passer à la vue Playlists.

- **Disposition en deux colonnes :** la colonne de gauche liste vos playlists à côté de la playlist système épinglée **Coups de cœur**, avec le nombre total de chansons. La colonne principale montre l’en-tête de la playlist active (pochette haute résolution, titre, description, nombre total de chansons et durée) et la liste des pistes.
- **Synchronisation automatique des favoris :** toute prise étoilée dans la bibliothèque, dans n’importe quel espace, apparaît automatiquement dans la playlist des favoris. Retirer l’étoile la retire de cette playlist.
- **Ajouter à une playlist :** appuyez sur **P** ou cliquez sur l’icône **Playlist** d’une carte pour ouvrir le sélecteur de playlists, cocher ou décocher l’appartenance aux playlists, ou en créer une nouvelle. **Échap** ferme le sélecteur.
- **Tri et recherche interactifs :** cliquez sur un en-tête de colonne (**Titre**, **Durée** ou **Ajout**) pour trier avec indicateur de sens et inverser l’ordre d’un clic, et filtrez les pistes avec la zone de recherche.
- **Aller à l’espace dans la bibliothèque :** cliquez sur le titre d’une chanson dans la liste des pistes pour passer aussitôt à la vue Bibliothèque, ouvrir l’espace où vit cette prise et mettre sa carte en évidence.
- **Raccourcis dans les playlists :** les raccourcis propres aux prises sont ignorés dans la vue Playlists pour éviter des modifications involontaires, sauf **M** (rack de mastering), qui agit sur la piste en lecture ou chargée, en plus des commandes de transport habituelles (**Espace**, flèches, **?** et **L**).
- **Lecture continue et aléatoire :** cliquez sur **Lire** dans l’en-tête de la playlist pour écouter depuis la piste 1, ou sur **Aléatoire** pour un ordre aléatoire. La lecture passe automatiquement à la piste suivante de la playlist à la fin de chaque chanson.

### Raccourcis clavier {#hot-keys}

Sur la page principale, des touches seules agissent sur la **prise choisie** : celle du panneau de gauche. Cliquez sur sa carte pour
la choisir. Chaque touche fait ce que fait son bouton, donc une touche qui supprimerait demande d’abord, et une prise
qui ne peut pas faire ce que demande une touche (Variations sur une prise sans partition, par exemple) laisse une ligne dans la barre
d’état qui dit pourquoi.

| Touche | Effet |
|---|---|
| Espace | lecture ou pause |
| Gauche, Droite | reculer ou avancer de cinq secondes |
| Maj+Gauche, Maj+Droite | la prise précédente ou suivante ; dans la vue Playlists, la chanson précédente ou suivante de la playlist |
| Haut, Bas | volume |
| M | ouvrir le rack de mastering de la prise ; à nouveau pour le fermer |
| E | ouvrir la prise dans l’éditeur |
| I | les détails de la prise : tout ce avec quoi elle a été faite, en mots, avec **Copier** |
| N | normaliser la prise, ou annuler si elle est normalisée |
| V | ouvrir ou fermer le visualiseur pendant la lecture, ou Variations à l’arrêt |
| T | Essayer encore |
| S | mettre ou retirer l’étoile de la prise |
| P | ajouter la prise à une playlist |
| D | supprimer la prise, après confirmation, comme sa corbeille |
| L | les journaux ; ou afficher les paroles quand le visualiseur est ouvert |
| B | dans le visualiseur, ce qui bouge derrière une scène sur l’image de la prise |
| F | basculer en plein écran |
| ? | afficher ou masquer les raccourcis ; à nouveau pour fermer |
| Échap | fermer la fenêtre au premier plan : le visualiseur, les journaux, le rack de mastering par-dessus l’éditeur, puis l’éditeur ou toute autre fenêtre |

Les touches de lettres ne font rien pendant que vous tapez dans une zone, quand une fenêtre est ouverte au premier plan, ou avec Ctrl,
Alt ou la touche Windows ou Commande enfoncée, pour que les raccourcis du navigateur (Ctrl+L, Ctrl+S et les autres)
fonctionnent toujours. L’infobulle d’un bouton nomme sa touche, comme dans **Variations (V)**. Appuyez sur **?** à tout moment pour afficher la liste des raccourcis.

Dans la fenêtre de l’éditeur, Espace et les flèches pilotent le lecteur de la fenêtre, pour la prise qui y est ouverte, chaque fois que son lecteur
s’affiche : à chaque étape, et avec le rack de mastering ouvert par-dessus. Elles n’agissent jamais pendant que vous tapez dans une zone,
et les touches de lettres ne valent que pour la page principale. Le piano roll a ses propres touches : voir [Le piano roll](#the-piano-roll).

---

## Paramètres {#settings}

Appuyez sur **Yeufonic** en haut à gauche. Les paramètres sont stockés sur le serveur, ils vous suivent donc dans n’importe quel
navigateur et survivent à une reconstruction : le format audio de sortie des stems et de l’enregistrement d’une prise, le
modèle de séparation, l’endroit où les stems sont écrits, si les checkpoints d’entraînement sont gardés, et la manière dont
on vérifie qu’un instrumental ne chante pas.

### Stockage {#storage}

**Paramètres → Stockage** montre où part l’espace disque de Yeufonic et vous permet d’en récupérer. Entraîner un
corpus laisse beaucoup de fichiers dont on n’a plus besoin : des copies faites pour le moteur pendant l’analyse des chansons,
le jeu d’entraînement (chaque chanson réécrite en FLAC sans perte, plus grand que l’original), et les checkpoints
enregistrés en chemin. La fenêtre liste chacun avec sa taille, **ce que c’est** et **ce que coûte sa
suppression**, et ne retire que ce que vous cochez, après une dernière confirmation. **Cocher ceux qui ne coûtent rien** coche
les copies qui sont simplement refaites au besoin.

Les chansons analysées désormais gardent leur voix séparée en FLAC, le même audio dans environ la moitié de la place. La
fenêtre peut **convertir les voix WAV que vous avez déjà** : chacune est convertie, vérifiée pour se décoder exactement en le même
audio, et seulement ensuite le WAV est retiré. Cela tourne en arrière-plan et peut être arrêté.

Les checkpoints d’entraînement méritent un second regard avant de partir : chacun est une entrée de la liste des LoRA de style que vous
pouvez choisir pour de nouvelles prises, donc retirer les checkpoints d’un corpus retire ces entrées de la liste pour de bon. Sa
LoRA finie reste et continue de fonctionner. Le jeu d’entraînement d’un corpus est différent : le retirer laisse la LoRA et ses
checkpoints dans la liste, et seul un nouvel entraînement de ce corpus en a besoin.

Vos prises, chansons, LoRA finies et modèles ne sont jamais proposés à la suppression. Tout ce qui appartient à un corpus en cours
d’entraînement, d’export ou d’analyse est grisé et ne peut pas être touché avant la fin.

En dessous, **Ranger automatiquement** choisit ce que Yeufonic retire pour vous : les copies de travail de chaque chanson
une fois son analyse terminée (activé par défaut), le jeu d’entraînement une fois qu’une LoRA est entraînée (désactivé par défaut ; le corpus
a alors besoin d’un nouvel **Export** avant de pouvoir s’entraîner à nouveau), et les checkpoints d’entraînement (gardés par défaut).

Les images et le cache de construction de Docker sont hors de Yeufonic et ne sont pas couverts ici ; `docker system df` les montre.

### Le modèle YuE2 {#the-yue2-model}

YuE2 existe en deux tailles, et une installation en a une : **pleine qualité**, que nous recommandons, ou **faible
mémoire**, une copie plus petite pour les cartes graphiques avec peu de mémoire vidéo. **À propos**, dans le même menu,
dit laquelle vous avez. Elle se choisit à l’installation de Yeufonic, pas ici :

- **Sous Windows**, relancez l’installateur. Sa page de composants propose les deux tailles et marque celles
  déjà téléchargées. Changer télécharge l’autre la première fois et garde les deux, donc revenir en arrière
  ne télécharge rien.
- **Avec Docker**, `sh scripts/fetch-models.sh` récupère la pleine qualité et
  `sh scripts/fetch-models.sh --int8` celle à faible mémoire. Avec les deux fichiers dans `models/checkpoints`,
  l’application utilise la pleine qualité sauf si `YUE2_CHECKPOINT=int8` est défini dans `.env`.

Essayez la faible mémoire si les rendus sont très lents ou si le moteur manque de mémoire GPU. Entraîner une LoRA fonctionne
avec les deux tailles. Le réglage **Entraînement avec le modèle à faible mémoire (int8)** choisit laquelle : désactivé, l’entraînement utilise
le modèle pleine qualité ; activé, il utilise le modèle avec lequel l’application fait ses rendus. Il est activé au départ quand seul le modèle à faible mémoire
est installé. Le README sur GitHub a une section, *Choosing a model size*, sur ce qu’on peut attendre de chacun.

Yeufonic peut aussi faire tourner le moteur **yue2.cpp** au lieu de ComfyUI, pour les cartes graphiques avec moins de mémoire,
choisi à la mise en place : sur la page des composants de l’installateur Windows, ou avec Docker par
`sh scripts/fetch-models.sh --cpp`. **À propos** dit quel moteur tourne, et la carte d’une prise quel moteur en a fait le rendu. Il crée chansons, reprises et
instrumentaux et transcrit les enregistrements, avec vos LoRA de style ; Gemma peut rédiger des paroles et décrire des images
à côté (avec Docker, `--gemma`), et FLUX.2 klein les dessiner (`--pictures`). L’entraînement a besoin du moteur
ComfyUI : avec yue2.cpp, Corpus et entraînement ne sont pas proposés. La page
[Choosing an engine](https://github.com/yeufonic/yeufonic/blob/main/docs/ENGINES.md) sur GitHub a la
liste complète, et comment changer.

**Rechercher une nouvelle version** est la seule chose ici qui utilise Internet de sa propre initiative : toutes
les quatre heures, l’application demande à yeufonic.com si une version plus récente est sortie, et le signale par une pastille à côté de la
version en haut à droite. Cette pastille vous donne l’installateur, ou, pour une copie Docker, les deux commandes
qui la mettent à jour. C’est une seule requête et rien d’autre ne quitte l’ordinateur ; **Ne pas vérifier** la
désactive. **Rechercher des mises à jour** dans le menu demande sur-le-champ, que ce soit activé ou non, et répond dans
le menu : quelle version vous avez, et si c’est la dernière.

Quand il y en a une plus récente, le menu propose **Obtenir x.y.z**, qui télécharge l’installateur sur une installation Windows ou place les deux commandes dans le presse-papiers pour une copie Docker.

**Thème** règle l’apparence de l’application : **Sombre**, **Clair**, **Comme l'ordinateur (sombre ou clair)**, qui suit le clair ou le sombre de votre
système et change avec lui, **Studio**, un sombre chaud avec de l’ambre, ou **Contraste élevé**, noir et blanc
avec des contours marqués. Le changement est immédiat, et chaque navigateur le retient
pour que la page s’ouvre ainsi. La fenêtre des journaux reste sombre dans tous les thèmes, comme un terminal. Le rack de mastering suit aussi le thème : dans le thème clair ses panneaux sont en argent brossé, tandis que ses boutons,
fenêtres de vumètres et afficheurs gardent l’aspect sombre du matériel.

**Couleur d'arrière-plan**, sous Thème, teinte la page derrière les prises d’une couleur de votre choix : cochez **Teinte**, puis
faites tourner **Couleur** sur la roue chromatique et réglez **Intensité** d’un léger voile à une couleur riche. La page change pendant que vous
faites glisser, et le choix est gardé quand vous relâchez. Les cartes de prise, les panneaux et les fenêtres gardent leurs propres
couleurs, et le thème à contraste élevé reste noir.

### LLM externe {#external-llm}

Yeufonic peut rédiger des brouillons de paroles, transcrire des enregistrements, marquer les sections des chansons et analyser les styles des corpus avec un LLM externe plutôt qu’avec le modèle Gemma local.

Utiliser un LLM externe a deux avantages nets :
- **Économise la mémoire GPU :** cela évite de charger le modèle Gemma 4 dans la VRAM du GPU (environ 8 Go de mémoire vidéo économisés), laissant votre carte graphique entièrement libre pour la planification et le rendu audio de YuE2.
- **Brouillons et analyses plus riches :** les grands modèles dans le cloud rédigent souvent des paroles plus nuancées et produisent des tags de style détaillés pour vos corpus.

**Fournisseur recommandé :** nous recommandons de choisir un fournisseur de LLM externe dont l’API n’est pas facturée si c’est possible pour vous — **Google Gemini** est un bon exemple. L’API de Gemini (via Google AI Studio) offre un palier gratuit généreux sans facturation, prend en charge les points de terminaison standard compatibles OpenAI (`https://generativelanguage.googleapis.com/v1beta/openai/`), et accepte directement l’audio pour transcrire des enregistrements.

Si vous utilisez une API mesurée ou payée au token (comme les paliers payants d’OpenAI ou d’Anthropic), analyser tout un corpus de dizaines de chansons ou générer des descriptions pour de nombreuses prises peut vite consommer des crédits d’API ou déclencher des plafonds de dépenses. Si une API externe renvoie une erreur de quota ou de limite de débit (HTTP 429), Yeufonic affiche une alerte et vous permet de passer aux modèles locaux pour le reste de la session, pour que les autres tâches continuent sans interruption. Un fournisseur sans facturation évite les frais inattendus.

**Configuration :**
1. Ouvrez **Yeufonic → Paramètres → LLM externe et paroles**.
2. Réglez **LLM pour écrire les paroles et les tags de style** sur **LLM externe (API compatible OpenAI)**.
3. Saisissez l’**URL d’API**, la **clé d’API** et le **modèle** de votre fournisseur (par exemple le modèle `gemini-2.5-flash` ou `gemini-1.5-flash` avec l’URL de base compatible OpenAI de Google Gemini `https://generativelanguage.googleapis.com/v1beta/openai/`).
4. Cliquez sur **Tester la connexion au LLM** pour vérifier vos identifiants.
5. Si le modèle choisi accepte l’audio en entrée (comme Gemini), vous pouvez aussi régler **Paroles à partir d'un enregistrement** sur **LLM externe** pour qu’il écoute les voix séparées.

---

## Utiliser Yeufonic depuis un agent IA (MCP) {#using-yeufonic-from-an-ai-agent-mcp}

Yeufonic peut servir de **serveur MCP**. Cela permet à un agent IA sur le même ordinateur, comme Claude Code ou Cursor, de l’utiliser pour vous :
demander une chanson, une reprise ou un instrumental, l’attendre, la lire, l’essayer autrement, lui donner une image, la mettre dans une playlist et
ranger la bibliothèque, le tout avec vos propres mots (« fais un instrumental EDM d’une minute dans l’espace EDM et lance-le »). L’agent fait ce que fait la page, par les mêmes routes, donc une prise qu’il lance est une
prise ordinaire de votre bibliothèque.

### Configuration {#setting-it-up}

1. **Activez-le.** Ouvrez les Paramètres et réglez **Serveur MCP** sur **Activé**. Il est désactivé par défaut, car une requête peut lancer un travail sur le GPU.
2. **Connectez votre agent** à l’adresse de l’application avec `/mcp` à la fin : l’adresse à laquelle vous ouvrez Yeufonic, par exemple
   `http://localhost:8090/mcp`. Dans Claude Code :

   ```
   claude mcp add --transport http yeufonic http://localhost:8090/mcp
   ```

   Les autres clients prennent la même adresse comme serveur HTTP. Ceux qui lisent un fichier de configuration veulent en général quelque chose comme
   `{"mcpServers": {"yeufonic": {"url": "http://localhost:8090/mcp"}}}`. Aucune connexion ni clé n’est nécessaire.
3. **Demandez.** Lancez votre agent depuis n’importe quel dossier et décrivez ce que vous voulez.

**Quelle adresse ?** C’est l’adresse à laquelle vous ouvrez Yeufonic, avec `/mcp` à la fin.
- **Docker :** `http://localhost:8090/mcp`.
- **L’installation Windows :** le port de l’application est dans `settings.ini` (`app_port`, 8090 sauf si vous l’avez changé, par exemple pour tourner à côté
  d’une copie Docker). Avec `app_port = 8091`, c’est `http://localhost:8091/mcp`.
- **Agent dans WSL, application sous Windows :** cela ne se connecte pas. L’application Windows n’écoute que sur l’adresse de bouclage propre à Windows, que WSL ne peut pas
  atteindre (Docker dans WSL fonctionne, puisqu’il est aussi dans WSL). Lancez l’agent depuis Windows (PowerShell ou la version Windows de
  votre agent), ou activez le réseau en miroir de WSL (`networkingMode=mirrored` sous `[wsl2]` dans `.wslconfig`, puis `wsl --shutdown`),
  qui rend `localhost` identique des deux côtés.

Si votre agent dit que le serveur **demande une authentification**, c’est presque toujours parce que le réglage est encore désactivé : activez-le, puis
reconnectez l’agent (dans Claude Code, `/mcp`). Reconnectez-le aussi après un redémarrage de Yeufonic, car un redémarrage coupe la connexion.

### Ce que vous pouvez demander {#what-you-can-ask-for}

| Demandez | Ce qui se passe |
|---|---|
| « Liste mes dernières prises », « montre les prises de l’espace EDM » | Liste les prises, les plus récentes d’abord, avec un id court, quand chacune a été faite, sa durée et son style |
| « Fais un instrumental d’une minute dans un style synthwave » | Planifie et fait le rendu d’un instrumental. On peut nommer une durée, un espace et une [LoRA de style](#style-loras) |
| « Fais une chanson dans un style folk avec ces paroles » | Pareil pour une chanson, à partir des paroles que vous donnez |
| « …avec une harmonie audacieuse, une interprétation serrée, en fa dièse, à 100 BPM » | N’importe quel réglage d’une nouvelle prise sous les noms qu’utilise la page : [Harmonie](#harmony), [Variété du plan](#plan-variety), l’[interprétation](#interpretation), les verrouillages de tonalité et de tempo, et pour une chanson **Suivre exactement cette structure** et **Les voix suivent les repères**. Sans précision, une nouvelle prise part de là où part celle de la page : Varié et Large |
| « Écris des paroles sur un train de nuit, façon parlée » | Le **Écrire les paroles** de l’application, avec ses formes de chanson, ses lignes par section et ses façons. L’agent peut aussi écrire les paroles lui-même |
| « Fais une reprise de *l’enregistrement* dans un style jazz » | Fait une reprise à partir d’un enregistrement déjà dans votre bibliothèque. Il faut une partition (transcrivez-le d’abord dans l’application). Sans paroles de votre part, il utilise les mots entendus dans l’enregistrement |
| « Lance-la » | Ouvre la prise dans votre navigateur, où elle se lit |
| « Mets une étoile à celle-là », « appelle-la Sunrise », « déplace-la dans l’espace Folk » | Met une étoile, renomme ou déplace une prise |
| « Refais le rendu avec une nouvelle seed », « arrête ça » | Refait le rendu d’une prise, ou en annule une en cours |
| « Donne-m’en quelques autres comme celle-là » | Refait le rendu de la prise avec de nouvelles seeds, en plusieurs nouvelles prises à écouter ensemble |
| « Chante-la encore », « essaie-la dans chaque interprétation » | **Rechanter** (une nouvelle voix pour la même partition) ou **Variations** (la même partition et la même seed, jouées de chaque façon). Les variations sont gardées dans la prise, comme Essayer encore |
| « Chante cet air avec ces paroles à la place » | **Nouvelles paroles** : la même mélodie, la même tonalité et le même tempo avec d’autres paroles, en une nouvelle prise |
| « Fais-en un instrumental » | La même partition avec l’air sur un instrument et sans chant, en une nouvelle prise |
| « Écris-lui un nouveau plan, plus vif » | Un nouveau plan pour une prise qui n’a pas encore d’audio (planifiée sans rendu, ou dont le plan a échoué). Une prise qui a de l’audio n’est pas touchée : demandez plutôt une nouvelle prise |
| « Garde la version libre à part » | **Sortir** : une prise gardée dans une autre devient une prise à part entière |
| « Donne-lui une image » | Crée une nouvelle image pour la prise, comme le bouton **Image** de l’éditeur, et donne un lien qui l’ouvre. Une image dessinée sur cet ordinateur attend qu’aucune chanson ne soit en cours |
| « Mets les trois meilleures dans une playlist appelée Road trip » | Crée des playlists, liste leur contenu, et ajoute ou retire des prises. Mettre une prise dans **Coups de cœur** lui met une étoile |
| « Trouve-moi un style synthwave », « enregistre ce style sous Night drive » | Parcourt vos styles enregistrés et ceux intégrés, et enregistre un style sous un nom pour le menu des styles |
| « Crée un espace appelé Drafts » | Crée un nouvel espace pour y garder des prises |
| « Transcris *l’enregistrement* » | Transcrit un enregistrement en partition, pour qu’on puisse en faire une reprise. Il laisse tranquille un enregistrement qui a déjà une partition, sauf demande |
| « Sépare ça en voix et instruments » | Sépare une prise terminée en ses parties (quatre, six, ou juste voix et instruments) et vous donne un lien vers chaque fichier et un vers l’ensemble en zip |
| « Yeufonic est-il occupé ? » | Dit si le moteur est prêt, ce qui tourne et avec quel avancement, ce qui attend, et si une LoRA s’entraîne |
| « Supprime cette prise » | Montre ce qui partirait et vous demande d’abord ; voir plus bas |

Créer une prise prend des minutes. L’agent la lance et attend, en rendant compte de l’avancement, et vous pouvez demander la suite entre-temps.

### Comment ça peut se passer : un exemple {#how-it-can-work-an-example}

Une conversation, d’une idée à une playlist. Vous parlez ; l’agent choisit les outils (la colonne du milieu n’est là que pour montrer ce qui
se passe) et vous dit ce qui est revenu.

| Vous dites | L’agent | Ce que vous obtenez |
|---|---|---|
| « Écris des paroles sur la dernière nuit d’un gardien de phare, style folk, forme récit. Puis fais-en une chanson dans un nouvel espace appelé Coast. » | `write_lyrics`, `create_space`, `make_song`, puis `wait_for_take` jusqu’à la fin | Les paroles, intitulées *The Last Light*, qui vous sont montrées ; un espace appelé Coast ; une chanson planifiée et rendue là, avec l’avancement en cours de route |
| « Lance-la. » | `get_take`, puis ouvre son `listen_url` | Elle se lit dans votre navigateur |
| « Bel air. Essaie-la plus libre et plus agitée, et donne-m’en une sans chant. » | `make_variations` avec loose et restless, `instrumental_from_take` | Deux prises dans la chanson, et un instrumental à côté |
| « Montre-moi ce qu’on a. » | `list_takes` dans Coast, et avec `inside` pour la chanson | Une liste avec un id court pour chacune, pour que vous puissiez dire « 3f9a » plutôt qu’un titre |
| « Garde 3f9a à part, mets-lui une étoile et donne-lui une image. » | `take_out`, `star_take`, `make_picture` | La version libre en prise à part entière, étoilée (donc aussi dans les favoris), avec un lien vers son image |
| « Mets-la avec l’instrumental dans une playlist appelée Coast demos. » | `create_playlist`, `add_to_playlist` | Une playlist qui contient les deux |
| « Enregistre le style sous Coastal folk. » | `save_style` | **Coastal folk** dans le menu des styles de l’application, prêt pour la prochaine fois |
| « Maintenant un duo : ces paroles, avec des indications [male voice] et [female voice], chaque section telle qu’écrite. » | `make_song` avec `follow_structure` (un nouveau plan, car les sections changent) | Une nouvelle chanson qui planifie exactement vos sections, dans l’ordre, chaque ligne indiquée étant déplacée là où chante cette voix |

Tout ce qu’il a créé est dans la bibliothèque comme si vous l’aviez fait dans la page : ouvrez n’importe quelle prise dans l’éditeur, masterisez-la, ou continuez là.
Quand une étape ne peut pas se faire, l’agent reçoit la raison de l’application (« this take is an instrumental already », « nothing here can draw a
picture ») et la transmet, pour que vous entendiez la même réponse que donnerait la page.

### Tout ce qu’il sait faire {#everything-it-can-do}

Vous n’avez pas besoin de ces noms : vous demandez avec vos propres mots et l’agent choisit. Ils sont là pour que vous voyiez ce qui existe, et pour que vous puissiez
dire à votre agent lequel vous voulez.

| Outil | Ce qu’il fait |
|---|---|
| `list_takes` | Liste les prises, les plus récentes d’abord, éventuellement seulement celles qui correspondent à des mots, dans un espace nommé, ou étoilées. Montre un id court |
| `get_take` | Une prise en entier : comment elle a été faite, son état, une éventuelle erreur et, dès qu’elle a de l’audio, un lien qui la lit. Peut inclure la partition |
| `wait_for_take` | Attend (jusqu’à environ une minute à la fois) une prise en cours de création, et dit si elle est terminée |
| `make_instrumental` | Planifie et fait le rendu d’un instrumental à partir d’un style, avec une durée, un espace et une LoRA de style si vous les nommez, et des sections si vous en donnez |
| `make_song` | Pareil pour une chanson, à partir de paroles |
| `make_cover` | Une reprise à partir d’un enregistrement de la bibliothèque, avec sa partition et, sauf si vous en donnez d’autres, ses paroles |
| `try_more` | Plusieurs autres prises à partir d’une existante, avec de nouvelles seeds |
| `sing_again` | La même partition chantée à nouveau avec une nouvelle seed : une nouvelle voix, en une nouvelle prise |
| `make_variations` | La même partition et la même seed dans chaque interprétation nommée (ou toutes), gardées dans la prise |
| `new_words` | La même partition chantée avec d’autres paroles, en une nouvelle prise |
| `instrumental_from_take` | La même partition en instrumental, en une nouvelle prise |
| `replan_take` | Un nouveau plan pour une prise encore sans audio, éventuellement avec une autre Harmonie, Variété du plan, tonalité ou tempo |
| `take_out` | Fait d’une prise gardée dans une autre une prise à part entière |
| `write_lyrics` | Des paroles à partir d’une consigne, dans une forme et une façon de chanson, écrites comme le fait Écrire les paroles de la page |
| `render_take` | Fait le rendu d’une prise planifiée, ou refait celui d’une prise terminée (avec une nouvelle seed si demandé) |
| `cancel_take` | Arrête une prise en file ou en cours |
| `make_stems`, `get_stems` | Sépare une prise en parties, puis liste les parties avec un lien vers chacune et vers l’ensemble en zip |
| `list_recordings`, `transcribe_recording` | Montre les enregistrements de la bibliothèque et si chacun a une partition ; transcrit celui qui n’en a pas |
| `list_style_loras` | Les LoRA de style installées, avec leurs mots déclencheurs et les forces enregistrées avec elles |
| `list_spaces`, `move_take`, `create_space` | Les espaces et ce que chacun contient ; déplace une prise vers un autre ; crée un nouvel espace |
| `list_playlists`, `create_playlist`, `add_to_playlist`, `remove_from_playlist` | Les playlists et les prises d’une playlist ; en crée une ; y ajoute ou en retire des prises |
| `make_picture` | Une nouvelle image pour une prise, avec un lien qui l’ouvre. `get_take` donne aussi le lien vers l’image d’une prise |
| `list_styles`, `save_style` | Vos styles enregistrés et ceux intégrés, cherchés par mots ; garde un style sous un nom |
| `star_take`, `rename_take` | Met ou retire l’étoile d’une prise ; change son titre |
| `delete_take` | Supprime une prise pour de bon, après vous l’avoir montrée et avoir reçu votre accord |
| `status` | Si le moteur est prêt, ce qui tourne et attend, et si une LoRA s’entraîne |

### Idées d’utilisation {#ideas-for-using-it}

- **Un lot d’idées, puis choisir.** « Fais cinq instrumentaux EDM d’une minute dans des styles différents, dans l’espace EDM. » Il les lance l’un après
  l’autre et vous prévient à mesure que chacun se termine. Vous écoutez, puis dites « mets une étoile au deuxième et au quatrième et supprime le reste. »
- **Faire évoluer une idée.** « Fais un instrumental dans un style synthé rêveur et lance-le », puis « maintenant la même avec plus de batterie », et
  « donne-m’en quatre autres comme la deuxième. » L’agent garde la trace de quelle prise est laquelle, pour que vous puissiez en parler par position ou
  par ce que vous en avez dit.
- **Des reprises sans cliquer partout.** « Transcris *la démo*, puis fais-en trois reprises : folk, synthwave et jazz. » Il transcrit
  d’abord l’enregistrement s’il n’a pas de partition, puis fait les reprises dans l’espace que vous nommez.
- **Travailler avec une LoRA.** « Liste mes LoRA de style, puis fais un instrumental avec celle de jazz. » Le mot déclencheur et les forces enregistrées sont
  gérés pour vous, ce qu’il est facile de rater à la main.
- **Des paroles de l’agent, ou de l’application.** L’agent peut écrire les paroles lui-même : « Écris des paroles sur un train de nuit et fais-en une chanson
  dans un style folk. » Yeufonic ne voit que les paroles finies. Ou demandez celles de l’application : « utilise l’auteur de paroles de Yeufonic, forme hip-hop,
  façon parlée », qui les écrit comme le fait **Écrire les paroles** dans la page et les rend pour une chanson.
- **Même air, autres paroles.** « Chante celle-là à nouveau avec ces paroles pour le deuxième couplet » : `new_words` garde la mélodie, la tonalité et le tempo,
  là où une nouvelle chanson à partir des paroles écrirait un nouvel air.
- **Comparer des réglages.** « Fais la même chanson deux fois, une fois en harmonie Familière et une fois en Audacieuse, avec la même seed », puis
  « maintenant donne à la meilleure chaque interprétation. » Les réglages se demandent par leur nom, vous pouvez donc concevoir un petit test en une phrase.
- **Des playlists à l’écoute.** « Mets toutes les prises étoilées de cette semaine dans une playlist appelée Week 43 », ou « retire les instrumentaux de
  Road trip. » Les favoris sont les prises étoilées, donc l’étoile et les favoris restent la même liste.
- **Des stems pour tout un lot.** « Sépare mes cinq prises les plus récentes en voix et instruments et donne-moi les liens. » Elles se mettent en file l’une
  derrière l’autre, et derrière tout rendu que le GPU exécute.
- **Ranger la bibliothèque.** « Trouve les prises qui ont le même titre, montre-moi laquelle est la plus récente, et supprime les plus anciennes », ou « déplace tout
  ce que j’ai fait aujourd’hui dans un espace appelé Drafts. » Il travaille avec des ids et demande avant de supprimer.
- **Vérifier avant une longue tâche.** « Yeufonic est-il occupé ? » avant de mettre en file un long rendu ou un lot, pour ne pas attendre derrière un entraînement.
- **Une partie d’une tâche plus large.** Comme c’est un outil que l’agent peut appeler, il peut s’intégrer à quelque chose de plus grand : créer une piste pour une vidéo et
  écrire la note qui l’accompagne, ou constituer un lot de la taille d’une playlist et nommer les prises d’après une liste.

L’agent ne peut pas entendre une prise, il ne peut donc pas juger de son son : vous écoutez, et il fait le travail de fond. Ce n’est pas non plus un
raccourci autour du moteur : le GPU fait toujours une tâche à la fois, donc un gros lot est une longue file.

### À savoir {#things-to-know}

- **Des prises peuvent partager un titre,** donc l’agent travaille avec l’**id** d’une prise et en montre un court (la colonne `short_id`) quand il liste les prises.
  Vous pouvez désigner une prise par le début de son id, quatre caractères ou plus, tant qu’une seule prise commence ainsi. Si deux le font, il vous le dit
  et en demande davantage.
- **La suppression demande deux fois.** L’agent vous montre d’abord ce qu’il supprimerait, y compris toute autre prise du même titre, et ne supprime
  qu’après votre accord. Une prise étoilée exige que vous le disiez explicitement. Une prise supprimée, avec son audio, ne peut pas être récupérée.
- **Les espaces et les LoRA de style sont désignés par leur nom,** pas par un numéro : « dans l’espace EDM », « avec la LoRA jazz ». Un nom qui ne correspond à rien reçoit la liste de
  ce qui existe, et rien n’est créé. Le mot déclencheur d’une LoRA est ajouté au style pour vous, car une LoRA fait très peu sans lui.
- **Une nouvelle prise part de là où part celle de la page :** Harmonie sur Varié et l’interprétation Large, sauf si vous en nommez d’autres. Sur un moteur
  sans le nœud d’harmonie, elle part de Familier, car l’Harmonie ne peut pas monter plus haut là.
- **Images et paroles attendent leur tour.** Une image dessinée ou décrite sur cet ordinateur attend qu’aucune chanson ne soit en cours, et des paroles
  écrites sur cet ordinateur font la queue avec le reste du travail GPU, donc l’agent peut répondre « encore en cours » et revérifier plus tard.
- **Un instrumental est toujours planifié avec une structure minutée,** calculée à partir de la durée demandée (environ deux minutes et demie
  si vous ne dites rien). Sans durées, le planificateur écrit des plans trop longs pour être utilisés. Nommez vos propres sections et elles sont utilisées telles quelles.
- **Seulement sur cet ordinateur.** Les mêmes contrôles de nom d’hôte et d’origine que pour la page s’appliquent, et il n’y a pas de connexion, alors désactivez le réglage
  quand vous ne l’utilisez pas, et n’exposez pas le port à un réseau auquel vous ne faites pas confiance.

## Journaux système {#system-logs}

L’application écrit un journal consolidé et en temps réel de chaque action importante — planification de partition, rendu, transcription audio, séparation des stems et entraînement de LoRA — avec les préfixes `INFO`, `WARN` et `ERROR`.

- **Console dans le navigateur :** cliquez sur le bouton **Journaux** dans la barre du haut (ou appuyez sur **L**) pour ouvrir une console flottante, déplaçable et redimensionnable. Elle reste ouverte sans bloquer la page, ce qui vous permet de mettre des prises en file et de suivre la génération en temps réel.
- **Fenêtre séparée :** cliquez sur **↗ Détacher** dans l’en-tête de la console (ou allez directement sur `/logs`) pour ouvrir une fenêtre dédiée aux journaux.
- **Dans un terminal :** les journaux tournent automatiquement dans `data/logs/yeufonic.log` sur l’hôte, où vous pouvez les suivre en direct :
  ```bash
  tail -f data/logs/yeufonic.log
  ```

## La page propre au moteur {#the-engine-s-own-page}

Le moteur est ComfyUI (sauf si cette installation fait tourner yue2.cpp, dont la page est un simple banc d’essai), et sa propre interface est accessible : <http://localhost:8189> avec Docker, ou
<http://localhost:8188> avec l’installation Windows (le `engine_port` dans `settings.ini`). Il ne répond
que sur cette machine, sans connexion.

- **C’est le même moteur et le même GPU que l’application.** Une tâche lancée là apparaît dans la file de l’application comme venant
  de l’extérieur, et les tâches de l’application l’attendent.
- **Son historique montre chaque graphe envoyé par l’application** : le plan, le rendu et les transcriptions, avec
  chaque réglage tel que le moteur l’a reçu. C’est un endroit utile pour voir exactement à partir de quoi une prise a été
  faite.

---

## Quand quelque chose ne va pas {#when-something-is-wrong}

**L’en-tête dit que le moteur manque.** L’application tourne sans lui et le dit. Les rendus attendent.
Vérifiez que le conteneur du moteur tourne.

**Une chanson ne se termine pas.** En général trop de force de planificateur. Baissez le Planificateur de la LoRA à 0.5. La
limite de durée l’arrêtera de toute façon.

**Une LoRA semble ne rien faire.** Vérifiez que le mot déclencheur est dans le Style, et que la force que vous avez
montée est bien une que le fichier contient — le sélecteur grise l’autre.

**Une prise indique *Rendu faible*.** Elle est sortie bien plus faible que d’habitude du début à la fin. Certaines prises
comme ça sont seulement faibles ; d’autres sonnent maigres ou distordues. Cliquez sur l’avertissement pour la normaliser, ce qui
la ramène au volume habituel et la marque *Normalisée*. Si elle sonne toujours mal, essayez une autre
seed, et gardez le Son de cette LoRA à 0.5 ou moins. Cela arrive surtout dans les reprises passant par une LoRA de style
entraînée ici.

**Normaliser le volume.** Cochez-le dans l’éditeur et chaque prise faite pendant qu’il est coché est ramenée au
volume habituel quand elle se termine, et marquée *Normalisée*. Une prise faite sans lui peut être normalisée
plus tard avec le bouton haut-parleur en haut de sa carte. Le fichier tel que rendu est gardé à côté, et
cliquer sur *Normalisée* y revient. Le niveau visé se règle dans les Paramètres, sous *Normaliser à*.
Décoché, une prise garde le niveau de son rendu.

**Un instrumental a chanté.** Voir *Quand un instrumental chante* plus haut. C’est un échec du modèle ; une nouvelle seed
le corrige en général.

**Une prise ne veut plus faire de rendu.** Son enregistrement a peut-être été supprimé. Les reprises gardent leur audio et leur
partition, mais ne peuvent pas être rendues à nouveau à partir d’un enregistrement qui n’existe plus.

**Rien ne joue, mais la forme d’onde bouge.** Vérifiez le curseur de volume et qu’un stem n’est pas sélectionné —
le lecteur suit ce qui a été cliqué en dernier.
