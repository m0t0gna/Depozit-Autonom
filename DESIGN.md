# Directie vizuala — Micul Depozit

Checkpoint: 5 octombrie 2026. Ghid de continuare, nu o cerinta pentru motor.

## Identitate

Un atelier mic de colete, vazut de sus, cu roboti prietenosi. Referinta de forma
este jocul 2D cu sprite-uri mici si meniuri desenate in pixeli. Fara gradient,
glow, blur, carduri translucide sau culori neon. Interfata trebuie sa para parte
din atelier: fise de lucru, bonuri, nume scurte, hartie si cerneala.

Paleta este in `pixel_art.py`: hartie crem, cerneala brun-inchis, verde salvie,
teracota si accente pastel pentru roboti. Nu folosi culoarea ca unic indicator:
robotii au ID si nume, iesirile au A–C, starea este scrisa in panou.

## Sprite-uri

- Sursele sunt functiile `robot_sprite()` si `tile_sprite()` din `pixel_art.py`.
- Grila de baza: 15x15 pixeli. Pe harta: scalare 2x, deci celule de 30x30.
- Foloseste scalare nearest-neighbor (`pygame.transform.scale`), fara antialias.
- Robotii: PIP, MOMO, LUNA, OTTO, COCO, NORI, TOTO, MILO. Sunt nume de afisare;
  motorul continua sa foloseasca ID-uri numerice, independente de prezentare.
- Silueta: antena, carcasa, ecran cu ochi, senile si colet vizibil cand transporta.
- Orientare cardinala, clipire discreta, alternarea senilelor, interpolare intre
  celule. `Animation` este exclusiv vizuala si nu schimba pozitiile motorului.
- Peretii sunt obstacole reale. Nu decora o celula accesibila cu obiecte care
  par solide, fara sa clarifici functia lor. Baza nu simuleaza o baterie reala.
- Sprite-urile si literele titlurilor sunt originale, desenate in cod; nu exista
  fisiere externe de font sau imagini care trebuie descarcate pentru pornire.

## Geometrie si interactiuni

`retro_view.py` este sursa geometriei: `MAP_X`, `HEADER`, `CELL`, `window_size`,
`button_rects`, `roster_rects`, `help_close_rect`. Nu copia offset-uri numerice
in teste sau in controller; altfel mouse-ul si desenarea se pot desincroniza.

Harta standard si panoul necesita o fereastra de 1320x810. Redimensionarea si
scalarea pentru ecrane mai mici nu sunt implementate; reprezinta un pas viitor.

`fleet_ui.py` contine `DepotUI` si bucla Pygame. Butoanele si tastatura folosesc
aceleasi actiuni. Ajutorul este modal: blocheaza click-urile catre harta si
suspenda tick-urile, pastrand optiunea de pauza existenta la inchidere.
Click pe un robot animat foloseste sprite-ul vizibil, nu doar celula logica.

Panoul arata cel mult trei comenzi nefinalizate; totalul din antet arata coada.
Jurnalul tehnic nu este afisat implicit; locul lui este ocupat de instructiunile de construire. Prioritatea este sa ramana
vizibile harta, echipa, comanda curenta si feedbackul ultimei actiuni.

## Verificare vizuala reproductibila

```powershell
.\.venv\Scripts\python.exe render_preview.py
.\.venv\Scripts\python.exe -m pytest -q
```

Scriptul regenereaza `artifacts/fleet-3.png`, `fleet-5.png`, `fleet-8.png`,
`retro-help.png` si `pixel-sprites.png`. Seed-ul si numarul de tick-uri sunt fixe.
Inspecteaza minim 3/8 roboti, ajutorul, confirmarea de click dreapta si statiile.
Nu modifica testele motorului ca sa maschezi o regresie de prezentare.

## Extensii recomandate

1. Redimensionare cu pastrarea raportului si conversia unica mouse -> canvas.
2. Lista de comenzi cu scroll si selectare, fara supraaglomerarea panoului.
3. Feedback la livrare (mica animatie pixel), cu optiune de reducere a animatiei.
4. Etichete/hinturi pentru statiile survolate si editor explicit de obstacole.
5. Salvare/incarcare de scenarii, apoi legarea acestei identitati de viitoarea UI web.

Pastreaza benchmarkul si coordonarea independente de aceasta directie vizuala.


## Corectie de directie: editor simplu, harta goala

Preferinta utilizatorului: fara pereti sau cutii la pornire, le pune manual.
UI-ul construieste Grid gol si pickups=[]; raman robotii, bazele si iesirile A–C.
Podeaua are textura discreta si variatii fine pe placi mari, fara grila de celule. Nu desena linii care unesc robotii
sau traseele tuturor simultan. Click pe iconita unui robot afiseaza linia continua pana la tinta lui; la pornire nu este afisat niciun traseu.

W selecteaza PERETI, T selecteaza CUTII. Ambele sunt unelte, nu generatori.
Click pe harta pune elementul; cutia este o comanda catre cea mai apropiata
iesire accesibila si este desenata pana la preluare. Click dreapta este scurtatura
pentru plasarea cutiei. Shift+dreapta pastreaza fluxul avansat cu destinatie explicita.
R elimina cutiile/comenzile si reseteaza robotii; Shift+R goleste si peretii.
Modelul vechi de raft ramane disponibil in sursa, dar editorul foloseste pereti
simpli fara cutii decorative. Capturile de pornire trebuie sa arate harta goala.


## Finisaje pentru spatiile goale

`atelier_decor.py` genereaza podeaua o singura data pe configuratie (cache).
Decorul foloseste culori apropiate de fond, granulatie rara, bordura vopsita si
marcaje de baze/iesiri. Nu exista noi obiecte solide in spatiul de lucru.
Inscripția centrala este intentionat estompata. Planta este numai in panoul
lateral, in afara hartii. Toate detaliile sunt desenate inaintea obiectelor
functionale si nu ating Grid, sarcinile sau generatorul aleator al motorului.


## Selectia traseului prin iconite

Panoul echipei foloseste acum o singura bara de iconite: cinci implicit, 3–8
in functie de flota. Elimina orice buton global TRASEE si scurtatura P. Selectia
unei iconite/robot/1–8 activeaza ruta acelui robot. Highlight-ul verde indica
iconita selectata. Geometria continua sa provina din `roster_rects()`.

Ruta este o linie continua verde, cu un contur crem pentru contrast pe podea,
si se leaga de pozitia animata a robotului. Nu folosi set() pentru ordinea pasilor.
`route_view.py` completeaza prefixul limitat cu o continuare A* orientativa;
textul din panou explica faptul ca traficul poate ajusta ruta. Nu prezenta
previzualizarea completa drept rezervare garantata.
