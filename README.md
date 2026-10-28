# Hafrsfjord Hornmusik og Haandbryggerlaug

Bryggeloggen fra hhogh.no, 13 brygg fra 2014 til 2016. Det opprinnelige WordPress-nettstedet ble kapret, så postene er hentet tilbake fra Internet Archive (versjoner fra før innbruddet) og publisert som en statisk side på GitHub Pages.

- `scripts/extract.py` henter tittel, dato, forfatter, tekst og kommentarer fra arkiverte post-sider.
- `scripts/download.py` laster ned bilder og vedlegg fra Wayback Machine. Der originalen ikke er arkivert, brukes den største arkiverte versjonen.
- `scripts/build.py` bygger HTML-sidene. Gamle lenker på formen `/?p=13` sendes videre til riktig brygg.

Ikke reddet (finnes ikke i arkivet): ett bilde i Batch #1, videoene i Batch #5 og #8, og ett bilde i Batch #10.
