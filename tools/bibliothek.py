#!/usr/bin/env python3
"""Erzeugt die Bibliothek der App: lib/*.musicxml und lib/index.json.

Alle Stücke sind eigene Notensetzungen für die App (CC0).
Klassik und Volkslieder: nur gemeinfreie Melodien, aus dem Gedächtnis neu gesetzt,
keine fremde Notenausgabe abgeschrieben. Übungen: eigene Muster.

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


def note_xml(tok):
    p, d = tok.split(":")
    d = int(d)
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
    x += "<duration>%d</duration><voice>1</voice><type>%s</type>%s</note>" % (d, typ, "<dot/>" if dot else "")
    return x, d


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
        tot = 0
        for tok in bar.split():
            x, d = note_xml(tok)
            m += x
            tot += d
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
    dict(id="rock-achtel", title="Rock-Achtel", composer="Übung", cat="Übungen", level=1,
         source="eigene Übung", license=OWN, sig="4/4", key=1, bpm=110,
         bars=rep(["E1:2 " * 8, "C2:2 " * 8, "D2:2 " * 8, "E1:2 E1:2 E1:2 E1:2 D2:2 D2:2 B1:2 B1:2"], 2),
         chords=rep(["Em", "C", "D", "Em,D@8"], 2)),
    dict(id="reggae", title="Reggae-Muster", composer="Übung", cat="Übungen", level=2,
         source="eigene Übung: Schlag 1 frei lassen", license=OWN, sig="4/4", key=0, bpm=76,
         bars=rep(["r:4 A1:4 C2:2 E2:2 A1:4", "r:4 D2:4 F#2:2 A2:2 D2:4"], 4),
         chords=rep(["Am", "D"], 4)),
    dict(id="funk-oktaven", title="Funk-Oktaven", composer="Übung", cat="Übungen", level=3,
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
]


def main():
    os.makedirs("lib", exist_ok=True)
    idx = []
    for p in PIECES:
        fn = p["id"] + ".musicxml"
        with open(os.path.join("lib", fn), "w", encoding="utf-8") as f:
            f.write(score(p))
        idx.append({k: p[k] for k in ("id", "title", "composer", "cat", "level", "source", "license")} | {"file": fn})
    with open("lib/index.json", "w", encoding="utf-8") as f:
        json.dump({"version": 1, "pieces": idx}, f, ensure_ascii=False, indent=1)
    print(len(idx), "Stücke geschrieben")


if __name__ == "__main__":
    main()
