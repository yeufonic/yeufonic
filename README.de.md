<p align="center">
  <img src="https://img.shields.io/badge/Yeufonic-ganze%20Songs%20auf%20deiner%20GPU-7b5cff?style=for-the-badge&labelColor=3a3a46" alt="Yeufonic: ganze Songs auf deiner GPU">
  <img src="https://img.shields.io/badge/Covers-deiner%20eigenen%20Aufnahmen-ff4d94?style=for-the-badge&labelColor=3a3a46" alt="Covers: deiner eigenen Aufnahmen">
  <img src="https://img.shields.io/badge/Style--LoRAs-selbst%20trainieren-7b5cff?style=for-the-badge&labelColor=3a3a46" alt="Style-LoRAs: selbst trainieren">
</p>

<p align="center">
  <img src="app/static/icon.svg" alt="Yeufonic" width="160">
</p>

<h1 align="center">Yeufonic</h1>

<p align="center">
  <b>Ganze Songs mit bearbeitbarer Partitur, erzeugt mit YuE2 auf deiner eigenen GPU. Aus einem Prompt schreiben,
  deine eigene Aufnahme covern, einen Stil aus einem Ordner voller Songs trainieren.</b>
</p>

<p align="center">
  <a href="https://yeufonic.com"><img src="https://img.shields.io/badge/Website-yeufonic.com-7b5cff?style=for-the-badge&labelColor=3a3a46" alt="Website: yeufonic.com"></a>
  <a href="https://github.com/yeufonic/yeufonic/releases/latest"><img src="https://img.shields.io/badge/Download-Windows%20x64-ff4d94?style=for-the-badge&labelColor=3a3a46" alt="Download: Windows x64"></a>
  <a href="https://yeufonic.com/macos/"><img src="https://img.shields.io/badge/macOS-Apple%20Silicon-7b5cff?style=for-the-badge&labelColor=3a3a46" alt="macOS: Apple Silicon"></a>
  <a href="#schnellstart-mit-docker"><img src="https://img.shields.io/badge/Docker-Linux%20·%20WSL-ff4d94?style=for-the-badge&labelColor=3a3a46" alt="Docker: Linux · WSL"></a>
</p>

<p align="center">
  <a href="https://github.com/yeufonic/yeufonic/releases/latest"><img src="https://img.shields.io/github/v/release/yeufonic/yeufonic?style=flat-square&label=Version&color=7b5cff" alt="Neueste Version"></a>
  <a href="https://github.com/yeufonic/yeufonic/releases"><img src="https://img.shields.io/github/downloads/yeufonic/yeufonic/total?style=flat-square&label=Downloads&color=ff4d94" alt="Downloads"></a>
  <a href="https://github.com/yeufonic/yeufonic/stargazers"><img src="https://img.shields.io/github/stars/yeufonic/yeufonic?style=flat-square&label=Sterne&color=7b5cff" alt="Sterne"></a>
  <a href="https://github.com/yeufonic/yeufonic/commits/main"><img src="https://img.shields.io/github/last-commit/yeufonic/yeufonic?style=flat-square&label=letzter%20Commit&color=ff4d94" alt="Letzter Commit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Lizenz-privat%2C%20nicht%20kommerziell-555?style=flat-square" alt="Lizenz: privat, nicht kommerziell"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>Deutsch</b>
</p>

---

> Diese Seite ist maschinell übersetzt und kürzer als das [englische README](README.md), das jedes Detail enthält.
> Die vollständige Anleitung gibt es auf Deutsch in der App (Hilfe) und hier: **[Anleitung auf Deutsch](app/static/guides/de-DE.md)**.

Eine Weboberfläche für [YuE2](https://github.com/multimodal-art-projection/YuE), das offene Musikmodell. Schreibe einen
Song aus einem Prompt oder cover deine eigene Aufnahme. Trainiere eine lokale LoRA auf einer Sammlung von Musik.
Bearbeite in beiden Fällen die Partitur und zieh danach die Stems aus dem Ergebnis.

## Was es kann

- **Song aus einem Prompt:** einen Partiturplan aus Stil und Songtext schreiben, bearbeiten und rendern.
- **Wähle deine Engine:** ComfyUI mit den YuE2-Nodes oder yue2.cpp (GGUF) für kleinere GPUs.
- **Eine Aufnahme covern:** deinen Song transkribieren, Melodie und Akkorde ändern und eine neue Version rendern.
- **Instrumentals:** die Struktur Abschnitt für Abschnitt aufbauen oder die Partitur einer Aufnahme spielen.
- **Eine Melodie aufnehmen:** singen, summen oder auf einem Instrument spielen und ein paar Takte zu einem ganzen Song
  erweitern.
- **MIDI-Import** für Covers und Instrumentals, mit Pianoroll und SF2-Klängen.
- **Style-LoRAs:** veröffentlichte nutzen oder mit der ComfyUI-Engine eigene aus einem Ordner voller Songs trainieren.
- **Aufgenommene Stimmen:** eine Stimme aus deinem eigenen Gesang trainieren und jeden Take darin singen lassen
  (Docker und Windows).
- **Songtexte:** aus einem Satz entwerfen oder aus einer Aufnahme heraushören.
- **Duette:** für beliebige Zeilen einen Mann, eine Frau oder beide vorgeben.
- **Sprachen:** die App und ihre Anleitung in fünfzehn Sprachen, maschinell übersetzt.
- **Vintage-Mastering-Rack:** EQ im 1073-Stil, parametrischer Equalizer, Kompressor, Stereo-Imager und Limiter, in
  Echtzeit. Dazu **3D Space**, das einen Take auf Kopfhörern um dich herum platziert und als 5.1 speichert.
- **Stems:** jeden Take in Gesang, Schlagzeug, Bass und mehr aufteilen, oder in Gesang und Begleitung.
- **Für eine DAW:** einen Take als ein ZIP mit Audio, Stems, MIDI, Partitur und Akkordtabelle speichern.
- **Eine Bibliothek:** Spaces, Sterne, Notizen und die Einstellungen jedes Takes, damit er sich wiederholen lässt.
- **Take-Dateien:** einen Take samt Rezept, Audio und Aufnahme speichern, teilen und wieder importieren.
- **Bilder zu Songs:** Cover mit lokalen Modellen (FLUX, Gemma) oder einem eigenen externen LLM.
- **Ein MCP-Server (standardmäßig aus):** ein KI-Agent wie Claude Code kann Songs, Covers und Instrumentals machen.

Alles läuft auf einem Rechner, in zwei Teilen: der App und der Engine. Keine Cloud und keine Konten; ein externes LLM für
Songtexte ist optional.

## Voraussetzungen

- Eine NVIDIA-GPU mit 12 GB VRAM oder mehr wird empfohlen, dazu 16 GB Arbeitsspeicher. Eine 8-GB-Karte ist einen
  Versuch wert. Für kleinere Karten gibt es das sparsame INT8-Modell oder die Engine yue2.cpp.
- Eine LoRA lokal zu trainieren braucht mehr: praktisch 16 GB VRAM und 32 GB Arbeitsspeicher (mit dem INT8-Modell
  geht es mit 8 GB VRAM).
- Etwa 30 GB freier Speicherplatz, mehr mit wachsender Bibliothek.
- Ein Macintosh mit Apple Silicon läuft experimentell, deutlich langsamer als eine NVIDIA-Karte:
  siehe **[yeufonic.com/macos](https://yeufonic.com/macos/)**.

## Unter Windows, ohne Docker

Ein kleines Installationsprogramm richtet Yeufonic nativ unter Windows ein, ohne Docker, ohne WSL und ohne
Administratorrechte. Lade es aus der **[neuesten Version](https://github.com/yeufonic/yeufonic/releases/latest)** herunter
und starte es. Es prüft deinen Rechner, bevor es etwas herunterlädt (etwa 27 GB, größtenteils die Modelle). Ein neueres
Installationsprogramm aktualisiert eine bestehende Installation.

Windows 10 22H2 oder Windows 11 (64 Bit) und eine NVIDIA-Karte ab der RTX-30-Serie mit aktuellem Treiber.

## Schnellstart mit Docker

Unter Linux oder Windows mit WSL2, mit Docker und dem NVIDIA Container Toolkit:

```sh
git clone https://github.com/yeufonic/yeufonic.git
cd yeufonic
sh scripts/fetch-models.sh          # etwa 19 GB, legt auch die Ordner an
docker compose up -d --build
```

Dann <http://localhost:8090> öffnen. Optionen (das kleinere Modell, die Engine yue2.cpp, Bildmodelle, Style-LoRAs) und
alles Weitere stehen im [englischen README](README.md#quick-start).

## Mehr

- **[Die vollständige Anleitung auf Deutsch](app/static/guides/de-DE.md)**, auch in der App unter Hilfe.
- **[Beispiel-Songs und LoRAs](https://yeufonic.com/examples/)**, mit Yeufonic gemacht.
- Fehler und Wünsche: [GitHub Issues](https://github.com/yeufonic/yeufonic/issues) (gern auf Englisch).

## Lizenz

Yeufonic steht unter einer Lizenz für den privaten, nicht kommerziellen Gebrauch: siehe [LICENSE](LICENSE). Die
Modelle, LoRAs und anderen Komponenten haben ihre eigenen Lizenzen; das [englische README](README.md#credits) nennt sie.
