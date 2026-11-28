#!/usr/bin/env python3
"""Zieht Cellostimmen aus dem music21-Korpus und schreibt tools/cello_auszuege.json.

Nur nötig, wenn die Auszüge neu erzeugt werden sollen (braucht: pip install music21).
Die Werke sind gemeinfrei; übernommen werden nur Tonhöhen und Rhythmus, neu gesetzt für die App.
Umrechnung: Bass klingt eine Oktave tiefer als notiert -> klingender Basston = Cello-Ton - 12.
Töne unter E1 (tiefe Cello-Saite C bis Es) werden eine Oktave höher gesetzt, Doppelgriffe auf den tiefsten Ton reduziert.
Aufruf:  python3 tools/cello_auszuege.py   (im Repo-Hauptordner)
"""
import json
from music21 import corpus

N = "C C# D Eb E F F# G Ab A Bb B".split()
NF = "C Db D Eb E F Gb G Ab A Bb B".split()

# id, Datei im Korpus, erster Takt, letzter Takt, Übetempo (Viertel/min), Stufe, Titel, Komponist, Quelle
AUSZUEGE = [
    ("mozart-k80-adagio", "mozart/k80/movement1.mxl", 1, 12, 60, 1, "Quartett G-Dur KV 80 – Adagio (Cello)",
     "Wolfgang Amadeus Mozart (1756–1791)", "1. Satz, Takte 1–12, Cellostimme"),
    ("mozart-k156-presto", "mozart/k156/movement1.mxl", 1, 24, 66, 1, "Quartett G-Dur KV 156 – Presto (Cello)",
     "Wolfgang Amadeus Mozart (1756–1791)", "1. Satz, Takte 1–24, Cellostimme"),
    ("mozart-k155-allegro", "mozart/k155/movement1.mxl", 1, 12, 90, 1, "Quartett D-Dur KV 155 – Allegro (Cello)",
     "Wolfgang Amadeus Mozart (1756–1791)", "1. Satz, Takte 1–12, Cellostimme"),
    ("haydn-op1-1", "haydn/opus1no1/movement1.mxl", 1, 14, 100, 2, "Quartett B-Dur op. 1 Nr. 1 – Presto (Cello)",
     "Joseph Haydn (1732–1809)", "1. Satz, Takte 1–14, Cellostimme"),
    ("mozart-k458-jagd", "mozart/k458/movement1.mxl", 1, 16, 110, 2, "„Jagdquartett“ B-Dur KV 458 – Allegro vivace (Cello)",
     "Wolfgang Amadeus Mozart (1756–1791)", "1. Satz, Takte 1–16, Cellostimme"),
    ("beethoven-op59-1-thema", "beethoven/opus59no1/movement1.mxl", 1, 8, 100, 2, "Rasumowsky-Quartett F-Dur op. 59 Nr. 1 – Thema (Cello)",
     "Ludwig van Beethoven (1770–1827)", "1. Satz, Takte 1–8: das Thema beginnt im Cello"),
    ("beethoven-op18-1-scherzo", "beethoven/opus18no1/movement3.mxl", 1, 16, 110, 2, "Quartett F-Dur op. 18 Nr. 1 – Scherzo (Cello)",
     "Ludwig van Beethoven (1770–1827)", "3. Satz, Takte 1–16, Cellostimme"),
    ("beethoven-op18-1-allegro", "beethoven/opus18no1/movement1.mxl", 1, 20, 100, 3, "Quartett F-Dur op. 18 Nr. 1 – Allegro con brio (Cello)",
     "Ludwig van Beethoven (1770–1827)", "1. Satz, Takte 1–20, Cellostimme"),
]


def name(m, flats):
    return (NF if flats else N)[m % 12] + str(m // 12 - 1)


def auszug(a):
    pid, path, m0, m1, bpm, lvl, title, comp, src = a
    s = corpus.parse(path)
    p = s.parts[-1]
    ts = p.recurse().getElementsByClass("TimeSignature")[0]
    ks = p.recurse().getElementsByClass("KeySignature")[0]
    bar16 = int(round(ts.barDuration.quarterLength * 4))
    bars, hoch = [], 0
    for m in p.getElementsByClass("Measure"):
        if m.number < m0 or m.number > m1:
            continue
        toks, t = [], 0
        for n in m.recurse().notesAndRests:
            if n.duration.isGrace:
                continue
            o = round(n.getOffsetInHierarchy(m) * 4)
            d = round(n.duration.quarterLength * 4)
            if o < t:  # zweite Stimme im selben Takt: weglassen
                continue
            if o > t:
                toks.append("r:%d" % (o - t))
            if n.isRest:
                toks.append("r:%d" % d)
            else:
                mid = min(x.midi for x in n.pitches) - 12
                if mid < 28:
                    mid += 12
                    hoch += 1
                tie = "~" if n.tie is not None and n.tie.type in ("start", "continue") else ""
                toks.append("%s:%d%s" % (name(mid, ks.sharps < 0), d, tie))
            t = o + d
        if t < bar16:
            toks.append("r:%d" % (bar16 - t))
        bars.append(" ".join(toks))
    src2 = src + (", tiefe Töne unter E eine Oktave höher (%d×)" % hoch if hoch else "")
    return dict(id=pid, title=title, composer=comp, cat="Klassik", level=lvl, source=src2,
                sig=ts.ratioString, key=ks.sharps, bpm=bpm, bars=bars, chords=[],
                corpus="music21-Korpus: " + path)


if __name__ == "__main__":
    out = [auszug(a) for a in AUSZUEGE]
    with open("tools/cello_auszuege.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(len(out), "Auszüge geschrieben")
