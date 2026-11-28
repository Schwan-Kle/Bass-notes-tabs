#!/usr/bin/env python3
"""Erzeugt die Bibliothek der App: lib/*.musicxml und lib/index.json.

Alle Stücke sind eigene Notensetzungen für die App (CC0).
Volkslieder und frühe Klassik-Stücke: nur gemeinfreie Melodien, aus dem Gedächtnis neu gesetzt.
Cello-Auszüge: gemeinfreie Werke, Tonhöhen/Rhythmus aus dem music21-Korpus (tools/cello_auszuege.json).
Funk, Rock, Übungen: eigene Muster im Stil, keine Basslinien bekannter Songs.

Schreibweise je Takt: "Ton:Länge" mit Länge in Sechzehnteln, getrennt durch Leerzeichen.
Ton = klingende Tonhöhe am Bass (E1 = leere E-Saite), z. B. C2, F#1, Bb1; r = Pause.
Akkordsymbole je Takt: "Sym" oder "Sym@Position" (Position in Sechzehnteln), mehrere mit Komma.
Aufruf:  python3 tools/bibliothek.py   (im Repo-Hauptordner)
"""
import json, os
from xml.sax.saxutils import escape

STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11, "H": 11}
TYPES = {16: ("whole", 0), 12: ("half", 1), 8: ("half", 0), 6: ("quarter", 1), 4: ("quarter", 0),
         3: ("eighth", 1), 2: ("eighth", 0), 1: ("16th", 0)}
KINDS = [("maj7", "major-seventh"), ("m7", "minor-seventh"), ("7", "dominant"), ("m", "minor"), ("", "major")]


def split_len(d):
    """Zerlegt eine Länge in darstellbare Notenwerte (werden übergebunden)."""
    out = []
    for v in (16, 12, 8, 6, 4, 3, 2, 1):
        while d >= v:
            out.append(v)
            d -= v
    return out


def note_xml(p, d, tie_in, tie_out, mark, slur_start):
    """p = Ton oder r; mark: x = Dead Note, a = Akzent, s = staccato, h = gebunden (Hammer-on/Legato) vom Vorton."""
    typ, dot = TYPES[d]
    x = "<note>"
    if p == "r":
        x += "<rest/>"
    else:
        step, rest = p[0], p[1:]
        alter = 0
        while rest and rest[0] in "#b":
            alter += 1 if rest[0] == "#" else -1
            rest = rest[1:]
        octave = int(rest) + 1  # Bass wird eine Oktave höher notiert, als er klingt
        x += "<pitch><step>%s</step>%s<octave>%d</octave></pitch>" % (
            step, "<alter>%d</alter>" % alter if alter else "", octave)
    x += "<duration>%d</duration>" % d
    if tie_in:
        x += '<tie type="stop"/>'
    if tie_out:
        x += '<tie type="start"/>'
    x += "<voice>1</voice><type>%s</type>%s" % (typ, "<dot/>" if dot else "")
    if "x" in mark:
        x += "<notehead>x</notehead>"
    nots = ""
    if tie_in:
        nots += '<tied type="stop"/>'
    if tie_out:
        nots += '<tied type="start"/>'
    if "h" in mark:
        nots += '<slur type="stop"/>'
    if slur_start:
        nots += '<slur type="start"/>'
    art = ("<accent/>" if "a" in mark else "") + ("<staccato/>" if "s" in mark else "")
    if art:
        nots += "<articulations>%s</articulations>" % art
    if nots:
        x += "<notations>%s</notations>" % nots
    return x + "</note>"


def bar_xml(bar, tie_in=False):
    """Takt in Kurzschrift -> (MusicXML der Noten, Länge in Sechzehnteln).
    Kurzschrift: Ton:Länge[Zeichen]; Zeichen ~ = Haltebogen zum nächsten Ton, x = Dead Note,
    a = Akzent, s = staccato, h = gebunden vom vorigen Ton (Hammer-on/Legato)."""
    evs = []
    for tok in bar.split():
        p, rest = tok.split(":")
        num = "".join(c for c in rest if c.isdigit())
        mark = rest[len(num):]
        evs.append([p, int(num), mark])
    out, tot = [], 0
    for i, (p, d, mark) in enumerate(evs):
        nxt = evs[i + 1] if i + 1 < len(evs) else None
        slur_start = bool(nxt and "h" in nxt[2])
        parts = split_len(d)
        for j, v in enumerate(parts):
            last = j == len(parts) - 1
            t_out = p != "r" and (not last or "~" in mark)
            t_in = p != "r" and (j > 0 or tie_in)
            out.append(note_xml(p, v, t_in, t_out, mark if j == 0 else mark.replace("h", "").replace("a", ""),
                                slur_start and last))
        tie_in = "~" in mark and p != "r"
        tot += d
    return "".join(out), tot, tie_in


def harmony_xml(sym, pos):
    root = sym[0]
    rest = sym[1:]
    alter = 0
    if rest[:1] in ("#", "b"):
        alter = 1 if rest[0] == "#" else -1
        rest = rest[1:]
    kind = "major"
    for suf, k in KINDS:
        if rest == suf:
            kind = k
            break
    off = "<offset>%d</offset>" % pos if pos else ""
    return "<harmony><root><root-step>%s</root-step>%s</root><kind>%s</kind>%s</harmony>" % (
        root, "<root-alter>%d</root-alter>" % alter if alter else "", kind, off)


def score(p):
    beats, btype = map(int, p["sig"].split("/"))
    steps = beats * 16 // btype
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<score-partwise version="3.1">',
           "<work><work-title>%s</work-title></work>" % escape(p["title"]),
           '<identification><creator type="composer">%s</creator><rights>%s</rights></identification>' % (
               escape(p["composer"]), escape(p["license"])),
           '<part-list><score-part id="P1"><part-name>Bass</part-name>'
           '<midi-instrument id="P1-I1"><midi-program>34</midi-program></midi-instrument></score-part></part-list>',
           '<part id="P1">']
    chords = p.get("chords", [])
    tie = False
    for i, bar in enumerate(p["bars"]):
        m = '<measure number="%d">' % (i + 1)
        if i == 0:
            m += ("<attributes><divisions>4</divisions><key><fifths>%d</fifths></key>"
                  "<time><beats>%d</beats><beat-type>%d</beat-type></time>"
                  "<clef><sign>F</sign><line>4</line></clef></attributes>") % (p["key"], beats, btype)
            m += '<direction placement="above"><direction-type><metronome><beat-unit>quarter</beat-unit>' \
                 '<per-minute>%d</per-minute></metronome></direction-type><sound tempo="%d"/></direction>' % (p["bpm"], p["bpm"])
        if i < len(chords) and chords[i]:
            for c in chords[i].split(","):
                sym, _, pos = c.strip().partition("@")
                m += harmony_xml(sym, int(pos or 0))
        x, tot, tie = bar_xml(bar, tie)
        m += x
        if tot != steps:
            raise SystemExit("%s: Takt %d hat %d statt %d Sechzehntel" % (p["id"], i + 1, tot, steps))
        if i == len(p["bars"]) - 1:
            m += '<barline location="right"><bar-style>light-heavy</bar-style></barline>'
        out.append(m + "</measure>")
    out.append("</part></score-partwise>")
    return "\n".join(out)


PD = "Melodie gemeinfrei; Notensatz für diese App: CC0 (frei nutzbar)"
OWN = "Eigene Übung für diese App: CC0 (frei nutzbar)"


def rep(seq, n):
    return seq * n


def blues(pattern, chords_per_bar):
    return [pattern[c] for c in chords_per_bar]


BL = ["E", "E", "E", "E", "A", "A", "E", "E", "B", "A", "E", "B"]

PIECES = [
    # ---------- Kinderlieder und Traditionals ----------
    dict(id="alle-meine-entchen", title="Alle meine Entchen", composer="Volkslied", cat="Lieder", level=1,
         source="traditionelles Kinderlied", license=PD, sig="4/4", key=0, bpm=90,
         bars=["C2:4 D2:4 E2:4 F2:4", "G2:8 G2:8", "A2:4 A2:4 A2:4 A2:4", "G2:16", "A2:4 A2:4 A2:4 A2:4", "G2:16",
               "F2:4 F2:4 F2:4 F2:4", "E2:8 E2:8", "D2:4 D2:4 D2:4 D2:4", "C2:16"],
         chords=["C", "C", "F", "C", "F", "C", "F", "C", "G", "C"]),
    dict(id="haenschen-klein", title="Hänschen klein", composer="Volkslied", cat="Lieder", level=1,
         source="traditionelles Kinderlied (Melodie)", license=PD, sig="4/4", key=0, bpm=96,
         bars=["G2:4 E2:4 E2:8", "F2:4 D2:4 D2:8", "C2:4 D2:4 E2:4 F2:4", "G2:4 G2:4 G2:8",
               "G2:4 E2:4 E2:8", "F2:4 D2:4 D2:8", "C2:4 E2:4 G2:4 G2:4", "C2:16",
               "D2:4 D2:4 D2:4 D2:4", "D2:4 E2:4 F2:8", "E2:4 E2:4 E2:4 E2:4", "E2:4 F2:4 G2:8",
               "G2:4 E2:4 E2:8", "F2:4 D2:4 D2:8", "C2:4 E2:4 G2:4 G2:4", "C2:16"],
         chords=["C", "G", "C", "C", "C", "G", "C,G@8", "C", "G", "G", "C", "C", "C", "G", "C,G@8", "C"]),
    dict(id="bruder-jakob", title="Bruder Jakob", composer="Volkslied (Frère Jacques)", cat="Lieder", level=2,
         source="traditionelles Lied, auch als Kanon", license=PD, sig="4/4", key=0, bpm=100,
         bars=["C2:4 D2:4 E2:4 C2:4", "C2:4 D2:4 E2:4 C2:4", "E2:4 F2:4 G2:8", "E2:4 F2:4 G2:8",
               "G2:2 A2:2 G2:2 F2:2 E2:4 C2:4", "G2:2 A2:2 G2:2 F2:2 E2:4 C2:4", "C2:4 G1:4 C2:8", "C2:4 G1:4 C2:8"],
         chords=["C", "C", "C", "C", "C", "C", "C", "C"]),
    dict(id="amazing-grace", title="Amazing Grace", composer="Volksweise „New Britain“ (19. Jh.)", cat="Lieder", level=2,
         source="traditionelle Melodie, Erstdruck 1829", license=PD, sig="3/4", key=1, bpm=80,
         bars=["r:4 r:4 D2:4", "G2:8 B2:2 G2:2", "B2:8 A2:4", "G2:8 E2:4", "D2:8 D2:4", "G2:8 B2:2 G2:2", "B2:8 A2:4",
               "D3:12", "D3:8 B2:4", "D3:6 B2:2 G2:4", "D2:8 E2:4", "G2:8 E2:4", "D2:8 D2:4", "G2:8 B2:2 G2:2",
               "B2:8 A2:4", "G2:12"],
         chords=["", "G", "G", "C", "G", "G", "G", "D", "D", "G", "G", "C", "G", "G", "D", "G"]),
    # ---------- Klassik ----------
    dict(id="ode-an-die-freude", title="Ode an die Freude", composer="Ludwig van Beethoven (1770–1827)", cat="Klassik", level=1,
         source="Thema aus der 9. Sinfonie, 4. Satz", license=PD, sig="4/4", key=2, bpm=100,
         bars=["F#2:4 F#2:4 G2:4 A2:4", "A2:4 G2:4 F#2:4 E2:4", "D2:4 D2:4 E2:4 F#2:4", "F#2:6 E2:2 E2:8",
               "F#2:4 F#2:4 G2:4 A2:4", "A2:4 G2:4 F#2:4 E2:4", "D2:4 D2:4 E2:4 F#2:4", "E2:6 D2:2 D2:8"],
         chords=["D", "A", "D", "A", "D", "A", "D", "A,D@8"]),
    dict(id="kanon-pachelbel-bass", title="Kanon in D – Basslinie", composer="Johann Pachelbel (1653–1706)", cat="Klassik", level=1,
         source="Bassmodell des Kanons; zweiter Ton D eine Oktave höher (4-Saiter)", license=PD, sig="4/4", key=2, bpm=60,
         bars=rep(["D2:4 A1:4 B1:4 F#1:4", "G1:4 D2:4 G1:4 A1:4"], 4),
         chords=rep(["D,A@4,Bm@8,F#m@12", "G,D@4,G@8,A@12"], 4)),
    dict(id="cello-suite-1-praeludium", title="Cello-Suite Nr. 1 – Präludium (Anfang)", composer="Johann Sebastian Bach (1685–1750)", cat="Klassik", level=3,
         source="BWV 1007, Takte 1–4, eine Oktave tiefer für Bass", license=PD, sig="4/4", key=1, bpm=60,
         bars=[" ".join(x + ":1" for x in ["G1", "D2", "B2", "A2", "B2", "D2", "B2", "D2"] * 2),
               " ".join(x + ":1" for x in ["G1", "E2", "C3", "B2", "C3", "E2", "C3", "E2"] * 2),
               " ".join(x + ":1" for x in ["G1", "F#2", "C3", "B2", "C3", "F#2", "C3", "F#2"] * 2),
               " ".join(x + ":1" for x in ["G1", "G2", "B2", "A2", "B2", "G2", "B2", "F#2"] * 2)],
         chords=["G", "C", "D7", "G"]),
    # ---------- Übungen ----------
    dict(id="blues-grundton", title="12-Takt-Blues in E – Grundton", composer="Übung", cat="Übungen", level=1,
         source="eigene Übung", license=OWN, sig="4/4", key=4, bpm=90,
         bars=blues({"E": "E1:4 E1:4 E1:4 E1:4", "A": "A1:4 A1:4 A1:4 A1:4", "B": "B1:4 B1:4 B1:4 B1:4"}, BL),
         chords=[c + "7" for c in BL]),
    dict(id="blues-boogie", title="12-Takt-Blues in E – Boogie", composer="Übung", cat="Übungen", level=2,
         source="eigene Übung", license=OWN, sig="4/4", key=4, bpm=100,
         bars=blues({"E": "E1:2 G#1:2 B1:2 C#2:2 D2:2 C#2:2 B1:2 G#1:2",
                     "A": "A1:2 C#2:2 E2:2 F#2:2 G2:2 F#2:2 E2:2 C#2:2",
                     "B": "B1:2 D#2:2 F#2:2 G#2:2 A2:2 G#2:2 F#2:2 D#2:2"}, BL),
         chords=[c + "7" for c in BL]),
    dict(id="blues-walking", title="12-Takt-Blues in E – Walking Bass", composer="Übung", cat="Übungen", level=3,
         source="eigene Übung: Grundton, Terz, Quinte, Annäherung an den nächsten Grundton", license=OWN, sig="4/4", key=4, bpm=110,
         bars=["E1:4 G#1:4 B1:4 C#2:4", "E2:4 D2:4 B1:4 G#1:4", "E1:4 G#1:4 B1:4 C#2:4", "E2:4 D2:4 B1:4 G#1:4",
               "A1:4 C#2:4 E2:4 F#2:4", "A2:4 G2:4 E2:4 F1:4", "E1:4 G#1:4 B1:4 C#2:4", "E2:4 D2:4 B1:4 A#1:4",
               "B1:4 D#2:4 F#2:4 A#1:4", "A1:4 C#2:4 E2:4 F1:4", "E1:4 G#1:4 B1:4 C#2:4", "B1:4 D#2:4 F#2:4 F1:4"],
         chords=[c + "7" for c in BL]),
    dict(id="rock-achtel", title="Rock-Achtel", composer="Übung", cat="Rock", level=1,
         source="eigene Übung", license=OWN, sig="4/4", key=1, bpm=110,
         bars=rep(["E1:2 " * 8, "C2:2 " * 8, "D2:2 " * 8, "E1:2 E1:2 E1:2 E1:2 D2:2 D2:2 B1:2 B1:2"], 2),
         chords=rep(["Em", "C", "D", "Em,D@8"], 2)),
    dict(id="reggae", title="Reggae-Muster", composer="Übung", cat="Übungen", level=2,
         source="eigene Übung: Schlag 1 frei lassen", license=OWN, sig="4/4", key=0, bpm=76,
         bars=rep(["r:4 A1:4 C2:2 E2:2 A1:4", "r:4 D2:4 F#2:2 A2:2 D2:4"], 4),
         chords=rep(["Am", "D"], 4)),
    dict(id="funk-oktaven", title="Funk-Oktaven", composer="Übung", cat="Funk", level=3,
         source="eigene Übung: Sechzehntel, Grundton und Oktave", license=OWN, sig="4/4", key=4, bpm=90,
         bars=rep(["E1:1 r:1 E2:1 r:1 E1:1 E1:1 E2:1 r:1 E1:1 r:1 E2:1 r:1 E1:1 E1:1 E2:1 E2:1"], 2)
              + rep(["A1:1 r:1 A2:1 r:1 A1:1 A1:1 A2:1 r:1 A1:1 r:1 A2:1 r:1 A1:1 A1:1 A2:1 A2:1"], 2),
         chords=["E7", "E7", "A7", "A7"]),
    dict(id="country", title="Country – Grundton und Quinte", composer="Übung", cat="Übungen", level=1,
         source="eigene Übung", license=OWN, sig="4/4", key=0, bpm=100,
         bars=["C2:4 G1:4 C2:4 G1:4", "C2:4 G1:4 C2:4 G1:4", "F1:4 C2:4 F1:4 C2:4", "C2:4 G1:4 C2:4 G1:4",
               "G1:4 D2:4 G1:4 D2:4", "G1:4 D2:4 G1:4 D2:4", "C2:4 G1:4 C2:4 G1:4", "C2:16"],
         chords=["C", "C", "F", "C", "G", "G", "C", "C"]),
    dict(id="tonleitern", title="Tonleitern: C-Dur, G-Dur, e-Moll", composer="Übung", cat="Übungen", level=1,
         source="eigene Übung: je eine Oktave auf und ab", license=OWN, sig="4/4", key=0, bpm=80,
         bars=["C2:4 D2:4 E2:4 F2:4", "G2:4 A2:4 B2:4 C3:4", "C3:4 B2:4 A2:4 G2:4", "F2:4 E2:4 D2:4 C2:4",
               "G1:4 A1:4 B1:4 C2:4", "D2:4 E2:4 F#2:4 G2:4", "G2:4 F#2:4 E2:4 D2:4", "C2:4 B1:4 A1:4 G1:4",
               "E1:4 F#1:4 G1:4 A1:4", "B1:4 C2:4 D2:4 E2:4", "E2:4 D2:4 C2:4 B1:4", "A1:4 G1:4 F#1:4 E1:4"],
         chords=["C", "", "", "", "G", "", "", "", "Em", "", "", ""]),
    dict(id="arpeggien", title="Arpeggien: C, F, G7, Am", composer="Übung", cat="Übungen", level=2,
         source="eigene Übung: Dreiklänge auf und ab", license=OWN, sig="4/4", key=0, bpm=80,
         bars=["C2:4 E2:4 G2:4 C3:4", "C3:4 G2:4 E2:4 C2:4", "F1:4 A1:4 C2:4 F2:4", "F2:4 C2:4 A1:4 F1:4",
               "G1:4 B1:4 D2:4 F2:4", "F2:4 D2:4 B1:4 G1:4", "A1:4 C2:4 E2:4 A2:4", "A2:4 E2:4 C2:4 A1:4"],
         chords=["C", "C", "F", "F", "G7", "G7", "Am", "Am"]),
    # ---------- Funk (eigene Muster im Stil, keine Basslinien bekannter Songs) ----------
    dict(id="funk-achtel-pausen", title="Funk 1 – Achtel und Pausen", composer="Übung", cat="Funk", level=1,
         source="eigene Übung: kurze Töne, Pausen genau zählen", license=OWN, sig="4/4", key=1, bpm=90,
         bars=["E1:2 r:2 E1:2 G1:2 A1:2 r:2 B1:2 D2:2", "E1:2 r:2 E1:2 G1:2 A1:2 B1:2 r:4"] * 2
              + ["A1:2 r:2 A1:2 C#2:2 D2:2 r:2 E2:2 G2:2", "A1:2 r:2 A1:2 C#2:2 D2:2 E2:2 r:4",
                 "E1:2 r:2 E1:2 G1:2 A1:2 r:2 B1:2 D2:2", "E1:2 r:2 E1:2 G1:2 A1:2 B1:2 r:4"],
         chords=["Em7"] * 4 + ["A7", "A7", "Em7", "Em7"]),
    dict(id="funk-deadnotes", title="Funk 2 – Sechzehntel mit Dead Notes", composer="Übung", cat="Funk", level=2,
         source="eigene Übung: ✕ = Dead Note (Saite abdämpfen und anschlagen)", license=OWN, sig="4/4", key=1, bpm=85,
         bars=["E1:2 r:1 E1:1x E2:1 r:1 E1:1 E1:1x r:1 G1:1 A1:1 r:1 B1:1 r:1 D2:1 E2:1",
               "E1:2 r:1 E1:1x E2:1 r:1 E1:1 E1:1x r:2 D2:1 r:1 B1:2 A1:2"] * 2,
         chords=["Em7"] * 4),
    dict(id="funk-oktave-septime", title="Funk 3 – Oktave und Septime", composer="Übung", cat="Funk", level=2,
         source="eigene Übung: Grundton, Oktave, kleine Septime", license=OWN, sig="4/4", key=0, bpm=92,
         bars=["D2:1 r:1 D3:1 r:1 C3:1 r:1 D3:2 r:2 A2:1 C3:1 D2:2 D3:1 r:1",
               "G1:1 r:1 G2:1 r:1 F2:1 r:1 G2:2 r:2 D2:1 F2:1 G1:2 B1:2"] * 2,
         chords=["Dm7", "G7", "Dm7", "G7"]),
    dict(id="funk-synkopen", title="Funk 4 – Synkopen auf „e“ und „+“", composer="Übung", cat="Funk", level=3,
         source="eigene Übung: Töne zwischen den Schlägen, laut „1 e + a“ mitzählen", license=OWN, sig="4/4", key=-2, bpm=88,
         bars=["G1:1 r:2 G1:1 r:1 Bb1:1 r:1 C2:1 r:1 D2:1 r:1 F2:1 r:1 G2:1 F2:1 D2:1",
               "G1:1 r:2 G1:1x G1:1 r:1 G2:1 r:2 F2:1 r:1 D2:1 C2:2 Bb1:2"] * 2
              + ["C2:1 r:2 C2:1 r:1 E2:1 r:1 G2:1 r:1 Bb2:1 r:1 G2:1 E2:2 D2:2"] * 2
              + ["G1:1 r:2 G1:1 r:1 Bb1:1 r:1 C2:1 r:1 D2:1 r:1 F2:1 r:1 G2:1 F2:1 D2:1",
                 "G1:1 r:2 G1:1x G1:1 r:1 G2:1 r:2 F2:1 r:1 D2:1 C2:2 Bb1:2"],
         chords=["Gm7"] * 4 + ["C7", "C7", "Gm7", "Gm7"]),
    dict(id="disco-oktaven", title="Disco-Oktaven", composer="Übung", cat="Funk", level=2,
         source="eigene Übung: Achtel im Oktavsprung, Zeigefinger tief, kleiner Finger hoch", license=OWN, sig="4/4", key=0, bpm=112,
         bars=(["A1:2 A2:2 " * 4, "G1:2 G2:2 " * 4, "F1:2 F2:2 " * 4, "E1:2 E2:2 " * 4]
               + ["A1:2 A2:2 " * 4, "G1:2 G2:2 " * 4, "F1:2 F2:2 " * 4, "E1:2 E2:2 E1:2 E2:2 G#1:2 B1:2 D2:2 E2:2"]),
         chords=["Am", "G", "F", "E7"] * 2),
    dict(id="soul-groove", title="Soul-Groove mit Annäherungston", composer="Übung", cat="Funk", level=2,
         source="eigene Übung: punktierte Achtel, letzter Ton führt zum nächsten Grundton", license=OWN, sig="4/4", key=0, bpm=100,
         bars=["C2:3 C2:1 E2:2 G2:2 A2:4 G2:2 E2:2", "F1:3 F1:1 A1:2 C2:2 D2:4 C2:2 F#1:2",
               "G1:3 G1:1 B1:2 D2:2 E2:4 D2:2 B1:2", "C2:3 C2:1 E2:2 G2:2 A2:2 G2:2 F2:2 E2:1 D2:1",
               "C2:3 C2:1 E2:2 G2:2 A2:4 G2:2 E2:2", "F1:3 F1:1 A1:2 C2:2 D2:4 C2:2 F#1:2",
               "G1:3 G1:1 B1:2 D2:2 E2:4 D2:2 B1:2", "C2:4 G1:4 C2:8"],
         chords=["C", "F", "G", "C"] * 2),
    # ---------- Rock (eigene Muster im Stil) ----------
    dict(id="rock-viertel", title="Rock 1 – Viertel auf dem Grundton", composer="Übung", cat="Rock", level=1,
         source="eigene Übung: gleichmäßig, jeder Ton gleich laut", license=OWN, sig="4/4", key=3, bpm=100,
         bars=["A1:4 A1:4 A1:4 A1:4"] * 2 + ["D2:4 D2:4 D2:4 D2:4"] * 2 + ["E1:4 E1:4 E1:4 E1:4"] * 2
              + ["A1:4 A1:4 A1:4 A1:4", "A1:4 A1:4 A1:8"],
         chords=["A", "A", "D", "D", "E", "E", "A", "A"]),
    dict(id="rock-quinte-oktave", title="Rock 2 – Grundton, Quinte, Oktave", composer="Übung", cat="Rock", level=1,
         source="eigene Übung: ein Griffmuster für alle Akkorde", license=OWN, sig="4/4", key=1, bpm=105,
         bars=["E1:2 E1:2 B1:2 B1:2 E2:2 E2:2 B1:2 B1:2", "G1:2 G1:2 D2:2 D2:2 G2:2 G2:2 D2:2 D2:2",
               "A1:2 A1:2 E2:2 E2:2 A2:2 A2:2 E2:2 E2:2", "E1:2 E1:2 B1:2 B1:2 E2:2 E2:2 B1:2 B1:2",
               "E1:2 E1:2 B1:2 B1:2 E2:2 E2:2 B1:2 B1:2", "G1:2 G1:2 D2:2 D2:2 G2:2 G2:2 D2:2 D2:2",
               "A1:2 A1:2 E2:2 E2:2 A2:2 A2:2 E2:2 E2:2", "E1:2 E1:2 B1:2 B1:2 E2:8"],
         chords=["Em", "G", "A", "Em"] * 2),
    dict(id="rock-shuffle", title="Rock 3 – Shuffle (12-Takt in A)", composer="Übung", cat="Rock", level=2,
         source="eigene Übung: 12/8, lang–kurz; Grundton, Quinte, Sexte", license=OWN, sig="12/8", key=3, bpm=120,
         bars=blues({"A": "A1:4 A1:2 E2:4 E2:2 F#2:4 F#2:2 E2:4 E2:2",
                     "D": "D2:4 D2:2 A2:4 A2:2 B2:4 B2:2 A2:4 A2:2",
                     "E": "E1:4 E1:2 B1:4 B1:2 C#2:4 C#2:2 B1:4 B1:2"},
                    ["A", "A", "A", "A", "D", "D", "A", "A", "E", "D", "A", "E"]),
         chords=[c + "7" for c in ["A", "A", "A", "A", "D", "D", "A", "A", "E", "D", "A", "E"]]),
    dict(id="punk-achtel", title="Rock 4 – Punk-Achtel", composer="Übung", cat="Rock", level=2,
         source="eigene Übung: schnelle Achtel, nur Abschlag, Betonung auf 1 und 3", license=OWN, sig="4/4", key=2, bpm=150,
         bars=["D2:2a D2:2 D2:2 D2:2 A1:2a A1:2 A1:2 A1:2", "B1:2a B1:2 B1:2 B1:2 G1:2a G1:2 G1:2 G1:2"] * 3
              + ["D2:2a D2:2 D2:2 D2:2 A1:2a A1:2 A1:2 A1:2", "D2:4a r:4 D2:4a r:4"],
         chords=["D,A@8", "Bm,G@8"] * 3 + ["D,A@8", "D"]),
    dict(id="rock-galopp", title="Rock 5 – Galopp", composer="Übung", cat="Rock", level=3,
         source="eigene Übung: Achtel + zwei Sechzehntel, gleichmäßig wechselschlagen", license=OWN, sig="4/4", key=1, bpm=120,
         bars=["E1:2 E1:1 E1:1 " * 4] * 2 + ["C2:2 C2:1 C2:1 " * 4, "D2:2 D2:1 D2:1 " * 4] + ["E1:2 E1:1 E1:1 " * 4] * 2
              + ["C2:2 C2:1 C2:1 " * 4, "E1:2 E1:1 E1:1 E1:2 E1:1 E1:1 G1:2 G1:1 G1:1 A1:2 B1:1 B1:1"],
         chords=["Em", "Em", "C", "D", "Em", "Em", "C", "Em,G@8,A@12"]),
    dict(id="rock-ballade", title="Rock 6 – Ballade mit Durchgangstönen", composer="Übung", cat="Rock", level=2,
         source="eigene Übung: Basslinie läuft stufenweise abwärts", license=OWN, sig="4/4", key=0, bpm=72,
         bars=["C2:4 C2:2 C2:2 C2:2 C2:2 B1:4", "B1:4 B1:2 B1:2 B1:2 B1:2 B1:2 A1:2",
               "A1:4 A1:2 A1:2 A1:2 A1:2 G1:4", "F1:4 F1:2 F1:2 G1:4 G1:2 G1:2"] * 2 + ["C2:16"],
         chords=["C", "G", "Am", "F,G@8"] * 2 + ["C"]),
]


CELLO = ("Werk gemeinfrei; Tonhöhen und Rhythmus aus dem music21-Korpus übernommen, "
         "für diese App neu gesetzt: CC0 (frei nutzbar)")
KATS = ["Lieder", "Klassik", "Funk", "Rock", "Übungen"]


def alle_stuecke():
    """Eigene Stücke plus Cello-Auszüge (tools/cello_auszuege.json, erzeugt mit tools/cello_auszuege.py)."""
    ps = list(PIECES)
    fn = os.path.join(os.path.dirname(__file__), "cello_auszuege.json")
    if os.path.exists(fn):
        for c in json.load(open(fn, encoding="utf-8")):
            ps.append(dict(c, license=CELLO))
    return sorted(ps, key=lambda p: (KATS.index(p["cat"]), p["level"]))  # nach Kategorie, dann leicht → schwer


def main():
    os.makedirs("lib", exist_ok=True)
    idx = []
    for p in alle_stuecke():
        fn = p["id"] + ".musicxml"
        with open(os.path.join("lib", fn), "w", encoding="utf-8") as f:
            f.write(score(p))
        idx.append({k: p[k] for k in ("id", "title", "composer", "cat", "level", "source", "license")} | {"file": fn})
    with open("lib/index.json", "w", encoding="utf-8") as f:
        json.dump({"version": 2, "pieces": idx}, f, ensure_ascii=False, indent=1)
    print(len(idx), "Stücke geschrieben")


if __name__ == "__main__":
    main()
