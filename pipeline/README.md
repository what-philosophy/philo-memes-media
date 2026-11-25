# what_philosophy pipeline

Runbook für den täglichen Task "what_philosophy: Buffer rollierend auffüllen". Englischer, gesichtsloser Meme-Account what_philosophy (Instagram + TikTok): absurd lange Originalpassagen von Philosophen als Karussell, eingerahmt von einer banalen modernen Frage, am Ende ein trockener Payoff.

## Bausteine
- `render2.py` rendert `posts/<JJJJ-KWxx>.json` nach `OUT/<id>/ig|tt/NN.png` (ig 1080x1350, tt 1080x1920). Passagen werden wörtlich aus `sources/` geschnitten (start/end-Strings), nie abgetippt.
- `sources/` gemeinfreie Volltexte. Weitere über GITenberg: `gh api -X GET search/repositories -f q="<Titel> org:GITenberg"`, dann `git clone --depth 1 https://github.com/GITenberg/<repo>`, Textdatei hierher kopieren.
- `queue.json` Warteschlange mit Status ready/scheduled/sent und geplantem Datum.
- Bilder für Buffer: `<JJJJ-KWxx>/<id>/ig|tt/NN.jpg` im Repo-Root, öffentlich unter `https://raw.githubusercontent.com/what-philosophy/philo-memes-media/main/...`. Geänderte Slides immer unter neuem Namen (z.B. `06_v2.jpg`), nie überschreiben.

## Buffer
- Org "My organization" 6b05664317a16160600aaa78, Gratisplan: max 10 geplante Posts pro Kanal.
- Instagram 6b056c968541f09ecb87e549: schedulingType automatic, mode customScheduled, metadata.instagram {type: "post", shouldShareToFeed: true}. Text: caption + Leerzeile + Hashtags.
- TikTok 6b056e828541f09ecb87ffe5: schedulingType automatic, mode customScheduled, metadata.tiktok {title: Hook-Text ohne Zeilenumbrüche, max. 90 Zeichen}. Text: caption + Leerzeichen + Hashtags.
- Jedes Bild als asset {image: {url, metadata: {altText}}}; altText = Slidetext kurz bzw. "<Philosoph>, <Werk>, page n".
- dueAt "JJJJ-MM-TTT18:30:00+01:00" (Winterzeit; ab letztem Märzsonntag +02:00).

## Regeln für neue Posts
- Nur gemeinfreie Übersetzungen (Übersetzer vor 1956 gestorben bzw. Erscheinen vor 1929) oder englische Originale. Kein Heidegger, kein Kaufmann, kein Miller, kein Wittgenstein-Ogden. Passagen wörtlich, Auslassungen mit [...], OCR-Fehler nur über "fix" und dokumentiert.
- Formate mischen: Frage-Antwort, Eskalation (shrink: true), Kontrast (short + meme + passage), Meta, Selbstwiderspruch.
- Payoff: bei langen Passagen und grundsätzlich bei Hegel "what?". Erklärende Pointen nur bei gut lesbaren Texten (Hume, Locke, Berkeley), etwa 1/3 der Posts, als Test gegen "what?".
- Hegel passt am besten, aber Variation über alle Philosophen; nicht zweimal derselbe Philosoph an aufeinanderfolgenden Tagen; keine Passage doppelt (gegen alle bisherigen posts/*.json prüfen).
- Hooks klein geschrieben, banale moderne Situation (Dating, Geld, Alltag, Therapie, Arbeit). Captions klein, trocken, ohne Punkt am Ende. 3-4 Hashtags, immer #philosophymemes und #philosophy.
- Max 10 Slides. Vor dem Push Kontaktbogen der tt-Version ansehen: Text darf nicht in die Safe-Zone (rechts 150 px) laufen.
