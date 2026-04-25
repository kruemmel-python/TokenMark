# Chaotisches Brainstorming

- TokenMark soll chaotische Meeting-Notizen aufnehmen
- Zielgruppe: Python Entwickler und technische Autoren
- Markdown bleibt am Ende kontrollierte Ausgabe
- Pipeline: Notizen -> Intent Graph -> Blueprint -> Markdown -> TokenMark QA
- Risiko: KI darf keine Fakten erfinden
- Wie markieren wir offene Fragen?
- tokenmark compose meeting.md --type technical-guide --audience developers
- PDF und i18n sollen danach normal funktionieren
- QA: Links, Code, Platzhalter müssen stabil bleiben
