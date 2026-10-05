# Micul Depozit — simulator de flota retro 2D

## Checkpoint actual — 5 octombrie 2026

**Pornire simpla: fara pereti, cutii sau comenzi.** Pe harta exista doar
robotii, bazele si trei iesiri A–C. Utilizatorul construieste depozitul.
Traseele sunt ascunse implicit; podeaua are textura discreta, fara grila de celule, iar panoul
arata echipa, comenzile si instructiunile esentiale.

**83 de teste trecute.** Aspectul retro, modelele pixel art, alocarea A* si
coordonarea spatio-temporala sunt pastrate. Directia vizuala este in
[DESIGN.md](DESIGN.md); capturile pot fi regenerate local.

## Pornire

PowerShell, Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Mediul existent `.venv` poate fi refolosit. Pentru rulare fara teste ajunge
`requirements.txt`. Nu exista descarcari de sprite-uri sau dependinte grafice noi.

```powershell
.\.venv\Scripts\python.exe main.py --robots 8 --seed 42
.\.venv\Scripts\python.exe main.py --coordination conservative
.\.venv\Scripts\python.exe main.py --single
```

`--single` pastreaza demo-ul original, cu harta si grafica veche. Pornirea goala
si editorul simplificat sunt comportamentul implicit al modului flota.

## Cum construiesti

1. Alege **PERETI [W]**, apoi click stanga pentru a pune/scoate un perete.
2. Alege **CUTII [T]**, apoi click stanga pe o celula libera pentru a pune o cutie.
3. Robotul disponibil cel mai apropiat o preia si o duce la iesirea accesibila
   cea mai apropiata de cutie, dupa distanta A*.
4. Poti apasa PAUZA inainte de a construi si CONTINUA cand harta e pregatita.

Cutia apare pe harta pana la preluare, apoi in fata robotului. Nu poti pune
cutii peste pereti, roboti, baze, iesiri sau alte cutii care asteapta preluarea.
Daca nu exista drum la nicio iesire, primesti un mesaj si cutia nu este creata.

| Comanda | Actiune |
| --- | --- |
| W / PERETI | Selecteaza unealta pentru pereti |
| T / CUTII | Selecteaza unealta pentru cutii; nu genereaza comenzi aleatorii |
| Click stanga pe harta | Foloseste unealta selectata |
| Click dreapta | Pune direct o cutie cu livrare automata |
| Click pe iconita / robot / 1–8 | Selecteaza robotul si afiseaza traseul lui |
| Spatiu / PAUZA | Pauza sau continua |
| N / UN PAS | Un tick, numai in pauza |
| Sus / Jos | Regleaza viteza |
| R | Reseteaza robotii si elimina comenzile/cutiile; pastreaza peretii |
| Shift+R | Reseteaza totul la harta goala |
| H / AJUTOR | Ajutor modal; simularea este suspendata cat timp e deschis |
| Esc | Inchide ajutorul daca e deschis; altfel inchide aplicatia |
| Shift+dreapta, apoi dreapta | Comanda avansata: preluare si destinatie explicite |
| C | Anuleaza preluarea explicita |

A/B si generatorul automat nu mai fac parte din interfata. Generatorul cu seed
ramane disponibil in motor pentru benchmark. P1–P6 nu mai sunt preamplasate in
interfata goala. Totalul din antet reprezinta coada; panoul arata primele trei
comenzi nefinalizate. Logul tehnic ramane in motor, dar nu aglomereaza ecranul.

## Ideea si arhitectura

Construim un simulator de depozit automatizat cu 3–8 roboti care transporta
cutii fara coliziuni: creare comanda -> alocare -> A* -> coordonare -> livrare.
Obstacolele introduse live declanseaza replanificarea. Interfata explica actiunile.
Este o versiune educationala a problemelor din automatizari industriale.

Arhitectura tinta: interfata web -> server Python -> alocare / planificare /
coordonare. Deocamdata interfata este Pygame; motorul este separat si nu importa
Pygame. Coordonarea este centralizata si determinista. Fara LLM in nucleu;
ROS 2 + Nav2 si o interfata in limbaj natural sunt extensii ulterioare.

### Motorul actual

- Comenzi FIFO executabile; robot disponibil ales dupa costul A* pana la preluare.
- Faze: preluare, transport, livrare, revenire la baza. Revenirea poate fi
  intrerupta de o noua alocare. Incarcarea/descarcarea sunt instantanee.
- `WindowCoordinator`: A* pe `(celula, timp)`, asteptare, rezervari de celule si
  muchii; respinge schimburile frontale. Ramificare de tip CBS pentru conflicte.
- Orizont: 12 tick-uri, maximum 80 de noduri de cautare la nivel inalt. Planurile
  sunt refolosite si invalidate la schimbarea hartii/tintelor/pozitiilor.
- Fallback conservator daca bugetul nu produce solutie. Validare independenta a
  fiecarui pas comun, inaintea modificarii pozitiilor robotilor.
- Refugiul lateral este folosit in scenariul de test cu doi roboti in sens opus.
  **Nu exista garantie generala de absenta a deadlock-urilor.** Culoarele fara
  refugiu, tintele ocupate permanent si limitele cautarii pot impiedica progresul.
- Robotii inactivi nu se muta automat pentru a elibera o tinta. Bazele nu simuleaza
  baterii; cutiile sunt comenzi, fara inventar persistent al rafturilor.

`Fleet()` fara argumente pastreaza harta clasica si statiile pentru benchmarkuri
si compatibilitatea testelor. `fleet_ui.run()` creeaza explicit un `Grid(30, 20)`
gol si `pickups=[]`. Aceasta separare este intentionata: nu modifica scenariile
benchmark doar pentru a schimba harta cu care porneste utilizatorul.

## Etape si continuare

| Etapa | Scop | Stare |
| --- | --- | --- |
| 1 | Grid + un robot + A* | Implementata; demo `--single` |
| 2 | Flota + comenzi + alocare simpla | Implementata; 3–8 roboti |
| 3 | Rezervari si evitare conflicte/deadlock | Partial: siguranta si CBS limitat; progresul general ramane deschis |
| 4 | Obstacole live + replanificare | Implementata, inclusiv invalidarea rezervarilor |
| 5 | Benchmark coordonare si alocare | Conservator vs. window implementat; Hungarian si comparator fara coordonare lipsesc |
| 6 | LLM si ROS 2 + Nav2 | Optional, neinceputa |

Estimari din ideea initiala: 1–2 saptamani etapa 1, doua etapa 2, 3–4 etapa 3,
1–2 etapa 4, doua etapa 5. Acestea nu sunt termene promise.

**Punct de reluare pentru urmatoarea sesiune:**

1. Ruleaza testele; citeste `DepotUI`, `retro_view.py` si `DESIGN.md` pentru UI.
   Comportamentul nou este: W/T selecteaza unelte; harta si coada pornesc goale.
2. Adauga salvare/incarcare JSON pentru harta si scenarii create de utilizator.
3. Redimensionare pentru ecrane mici: UI-ul actual necesita 1320x810. Pastreaza
   o singura conversie mouse -> canvas si testeaza marginile/hit-test-urile.
4. Lista de comenzi cu scroll, stergerea unei cutii nealocate, feedback la livrare
   si optiune pentru reducerea animatiei. Nu readauga linii decorative pe harta.
5. Extinde scenariile dense, destinatiile comune si blocajele ciclice. Separa
   siguranta de progres. Studiaza prioritati cu vechime si mutarea robotilor idle.
6. Compara orizonturi/bugete si Hungarian vs. greedy; adauga CSV si grafice.
7. Abia dupa stabilizarea motorului, construieste serverul Python si UI web.

## Verificari si benchmark

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe render_preview.py
.\.venv\Scripts\python.exe benchmark.py --robots 8 --seeds 7 19 42 --ticks 600 --jobs 20 --interval 20 --output artifacts/benchmark.json
```

Testele actuale: **83 passed**. Sunt acoperite A*, siguranta, refugii,
reproductibilitate, click unic, ajutor modal, geometrie, selectie in timpul
animatiei, pornire goala, unelte, livrarea cutiilor puse manual si reset complet.
Capturile 3/5/8, ajutorul si plansa de sprite-uri sunt regenerabile; randarea
fara fereastra nu inlocuieste o sesiune manuala completa pe desktop.

Raportul algoritmic existent `artifacts/benchmark.json` este din checkpointul
anterior: 8 roboti, 20 comenzi, 600 tick-uri, seed-uri 7/19/42. Ambii coordonatori
au livrat 20/20 fara conflicte in fiecare scenariu. Asteptari conservator:
21/7/17; window: 1/0/1. Window a costat aproximativ 0,69–0,71 secunde/rulare,
conservator 0,10–0,16 pe calculatorul local. Nu este o garantie universala.

Scenariile sunt identice intre coordonatori si retinute in JSON. Latenta medie
si p95 includ doar comenzile finalizate: citeste si `unfinished`. `submitted`
poate fi sub `requested_jobs` daca rularea e prea scurta. Timpii CPU nu sunt
deterministi. Schimbarile vizuale nu reprezinta o noua masuratoare benchmark.

## Fisiere

- `fleet.py`: sarcini, alocare, faze si executie comuna.
- `coordination.py`: coordonatori, rezervari, cautare si validare.
- `fleet_ui.py`: `DepotUI`, unelte, plasarea cutiilor si pornirea goala.
- `retro_view.py`: geometrie, iconite, randare si animatie fara modificarea motorului.
- `route_view.py`: previzualizare completa a traseului, separata de rezervarile de trafic.
- `pixel_art.py`: sprite-uri 15x15, pereti, cutii, paleta si alfabet bitmap.
- `atelier_decor.py`: podea texturata, marcaje vopsite si planta pixel art, fara efect asupra motorului.
- `commands.py`: fluxul avansat de preluare/destinatie explicita.
- `main.py`: CLI; `grid.py`, `astar.py`, `robot.py`: componentele initiale.
- `benchmark.py`: scenarii headless si export JSON.
- `render_preview.py`: capturi de pornire, ajutor si plansa sprite-urilor.
- `DESIGN.md`: directie vizuala si continuare.
- `test_*.py`: regresiile functionale si de interactiune.

## Istoric scurt

- 22 teste: un robot, A*, obstacole si pauza.
- 43 teste: flota, transport si coordonare conservatoare.
- 62 teste: click unic, coordonare temporala, refugiu si benchmark.
- 73 teste: identitate retro, sprite-uri, animatie, butoane si ajutor.
- **77 teste, actual:** interfata simplificata, harta goala, unelte pereti/cutii,
  fara comenzi automate si fara grila/linii de traseu afisate implicit.

Nu a fost lasat un proces de simulare sau server pornit. Pastreaza aici deciziile,
verificarile si limitarile reale pentru reluarea lucrului dupa o intrerupere.


### Finisaje vizuale — 5 octombrie 2026

Spatiile goale au acum o podea cu placi mari in nuante foarte apropiate,
granulatie rara, bordura vopsita, baze numerotate si iesiri etichetate cu sageti
scurte. Inscripția estompata ATELIER este pur decorativa. Panoul are o planta
pixel art si un mesaj de coada goala asezat pe o zona de hartie discreta.

Implementarea este in `atelier_decor.py`, apelata din `retro_view.py` inaintea
obiectelor hartii. Fundalul este memorat in cache si determinist: nu se schimba
la fiecare cadru si nu consuma RNG-ul comenzilor. Peretii/cutiile utilizatorului
sunt desenate peste decor. Harta continua sa porneasca fara obstacole sau cutii.

La reluare: pastreaza contrastul decorului sub cel al robotilor si al obiectelor.
Nu transforma marcajele pictate in obstacole, nu readauga trasee multiple sau
o grila accentuata. Capturile 3/5/8 si ajutorul se regenereaza cu
`python render_preview.py`. Verificarea ramane suita de 77 de teste existente.


### Corectie trasee si selectie — checkpoint actual

**83 teste trecute.** Butonul TRASEE si scurtatura P au fost eliminate. Panoul
ECHIPA DE TURA contine cinci iconite la pornirea implicita (se adapteaza la 3–8).
Click pe iconita, pe robotul vizibil sau tasta 1–8 afiseaza automat numai ruta lui.
La pornire nu este desenata nicio ruta, pana cand alegi un robot.

Cauza fragmentarii: `robot.path` contine adesea doar fereastra rezervata de 12
tick-uri, iar randarea veche afisa puncte neconectate si elimina ordinea cu set().
`route_view.display_route()` pastreaza ordinea si ocolirile, elimina doar
repetarile consecutive de asteptare, apoi completeaza prefixul prin A* pana la
tinta curenta. Linia continua porneste de la sprite-ul animat. Daca harta invalideaza
prefixul, previzualizarea se recalculeaza. Robotul fara misiune sau cu tinta
inaccesibila primeste un mesaj explicit in panou.

Continuarea dincolo de fereastra planificata este ORIENTATIVA, nu rezervata:
traficul poate modifica traseul. Tinta curenta inseamna preluarea, livrarea sau
baza, in functie de faza misiunii. Motorul si siguranta miscarii nu au fost schimbate.

Testele suplimentare din `test_route_view.py` verifica ruta lunga, asteptari,
intoarceri, pereti noi, tinta inaccesibila, selectia prin iconite si actualizarea
in timpul miscarii. `artifacts/selected-route.png` arata un exemplu cu ruta activa;
capturile obisnuite continua sa arate pornirea goala. Toate sunt regenerate de
`render_preview.py`. Pentru reluare, citeste `route_view.py` si `DepotUI.select_robot`.
