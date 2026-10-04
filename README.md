# Depozit Autonom — simulator de flota

## Ideea proiectului

Construim un simulator de depozit automatizat: o harta cu rafturi, puncte de
preluare, zone de incarcare/descarcare si 3–8 roboti care executa comenzi precum
„muta cutia de la raftul 3 la iesirea B”. Scopul este sa implementam creierul
flotei: alocare, planificare, coordonare si reactie la obstacole, cu o interfata
care explica deciziile. Este o versiune educationala a problemelor intalnite
in automatizarile industriale si in sisteme precum Amazon Robotics sau Locus
Robotics, nu o reproducere a sistemelor lor.

Fluxul dorit:

1. Apare o comanda cu punct de preluare si destinatie.
2. Sistemul alege cel mai apropiat robot liber.
3. Robotul planifica prin A*, merge la preluare si incarca cutia.
4. Coordonatorul gestioneaza accesul la culoare, asteptarea si ocolirea.
5. Robotul livreaza cutia; un obstacol pus live declanseaza replanificarea.
6. Interfata arata robotii, traseele, comenzile si deciziile, de exemplu
   „Robot 2 asteapta: culoar ocupat de Robot 1”.

Arhitectura tinta:

```text
Interfata web: harta, obstacole, sarcini, log, statistici
                         |
                Server Python / simulator
             /           |             \
       Alocare        Planificare     Coordonare
       sarcini           A*          trafic / rezervari
```

Incepem centralizat: un coordonator vede intreaga flota. Algoritmii sunt
deterministi; LLM-ul nu face parte din nucleu. ROS 2 nu este necesar initial.
Coordonarea distribuita, o interfata in limbaj natural si portarea pe ROS 2 +
Nav2 raman extensii. Interfata actuala este **Pygame**; **serverul si interfata
web nu sunt implementate**. Motorul flotei nu importa Pygame si poate fi
reutilizat ulterior de server.

## Starea actuala / de unde se reia lucrul

**Checkpoint: 4 octombrie 2026, actualizarea 2.** Etapa 2 functioneaza;
etapa 3 are acum A* spatio-temporal si rezolvarea conflictelor pe o fereastra
limitata; etapa 5 a inceput cu un benchmark comparativ headless.

- 5 roboti implicit, 3–8 configurabili; P1–P6 pentru preluare, A–C pentru livrare.
- 5 comenzi la pornire, loturi, generator cu seed si comenzi manuale.
- **Un singur click dreapta creeaza comanda catre celula aleasa**, cu preluarea
  selectata automat dintre statiile accesibile, dupa cel mai scurt traseu A*.
- Shift+click dreapta alege explicit preluarea; urmatorul click dreapta alege
  livrarea. Mesajul de sub harta confirma comanda sau explica de ce nu se poate crea.
- Alocare FIFO pentru comenzile executabile, robot disponibil ales dupa distanta A*.
- Ciclu preluare -> transport -> livrare -> baza; robotii care revin sunt disponibili.
- Coordonator implicit `window`: rezervari pe 12 tick-uri, conflicte de celule si
  traversari, actiune de asteptare si folosirea refugiilor in scenariile testate.
- Coordonator `conservative` pastrat ca referinta si fallback pentru bugetul depasit.
- Obstacole live, invalidarea rezervarilor, verificare comuna a sigurantei miscarii.
- Pauza, pas cu pas, viteza, trasee, statistici si jurnal. Dupa 30 de tick-uri
  consecutive de asteptare, jurnalul semnaleaza lipsa de progres.
- Benchmark JSON cu sarcini identice intre coordonatori, latenta, distante,
  asteptari, conflicte si timpi de executie.
- Demo-ul original ramane disponibil cu `--single`.

**Nu exista o garantie generala de absenta a deadlock-urilor.** Testul cu
refugiu lateral este rezolvat de coordonatorul nou; culoarul fara refugiu,
tintele permanent ocupate si limitele cautarii raman cazuri problematice.

## Instalare si pornire

PowerShell, Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Pentru utilizare fara teste, este suficient `requirements.txt`.

```powershell
# Flota de 8 roboti; acelasi seed reproduce comenzile aleatorii
.\.venv\Scripts\python.exe main.py --robots 8 --seed 42

# Comparatorul conservator
.\.venv\Scripts\python.exe main.py --coordination conservative

# Demo-ul initial, cu un singur robot
.\.venv\Scripts\python.exe main.py --single

# Toate testele
.\.venv\Scripts\python.exe -m pytest -q
```

## Comenzi in modul flota

| Comanda | Actiune |
| --- | --- |
| Click stanga pe o celula | Adauga sau elimina obstacolul |
| Click stanga pe un robot / tastele 1–8 | Selecteaza robotul pentru statistici |
| Click dreapta | Creeaza imediat o comanda catre celula aleasa; preluare automata |
| Shift+click dreapta, apoi click dreapta | Alege manual preluarea, apoi livrarea |
| C | Anuleaza selectia unui punct de preluare |
| T | Adauga o comanda aleatorie |
| B | Adauga un lot de 5 comenzi |
| A | Porneste/opreste generatorul automat |
| Spatiu | Pauza / continua |
| N | Un tick pentru intreaga flota, doar in pauza |
| Sus / Jos | Creste / scade viteza (2–33,3 tick-uri/secunda) |
| P | Afiseaza / ascunde traseele |
| R | Reseteaza flota si comenzile, pastrand obstacolele |
| Shift+R | Reseteaza flota, comenzile si harta |
| Esc | Inchide aplicatia |

Resetarea pastreaza pauza, viteza, afisarea traseelor si optiunea generatorului.
Dupa resetare, coada este goala; T/B adauga comenzi sau generatorul o repopuleaza.
Generatorul automat porneste oprit; cand este activ, adauga o comanda la fiecare
40 de tick-uri daca exista mai putin de 20 de comenzi in asteptare.

P1–P6 sunt puncte de serviciu accesibile langa rafturi. A–C sunt iesiri. Cercurile
colorate indica bazele; patratul galben langa un robot indica o cutie transportata.
Nu se pot bloca statiile, bazele, robotii sau capetele comenzilor nefinalizate.
Comenzile cu preluare explicita pot folosi orice doua celule libere distincte.
Un click obisnuit alege cea mai apropiata statie P accesibila fata de destinatie
si diferita de aceasta. El creeaza o sarcina pentru flota, nu intrerupe misiunea
robotului selectat. Daca toti robotii sunt ocupati, comanda asteapta alocarea.
Daca nu exista preluare accesibila, UI-ul afiseaza motivul si nu creeaza comanda.
Comenzile explicite fara traseu static raman in asteptare si sunt reanalizate.
O apasare repetata poate crea o alta comanda; nu mai este necesar un al doilea
click pentru confirmare in modul implicit.

In modul `--single`: click dreapta stabileste direct tinta, E comuta explorarea,
R reseteaza robotul, Shift+R restaureaza harta. Spatiu/N/Sus/Jos/Esc functioneaza
ca inainte. T/B/A/P si comenzile de transport apartin modului flota.

## Cum functioneaza implementarea curenta

### Alocare si sarcini

`Fleet.assign()` parcurge comenzile in ordinea crearii. Verifica daca exista
traseu de la preluare la livrare, apoi compara distantele A* de la robotii
 disponibili la preluare. Egalitatile se rezolva prin ID. O comanda inaccesibila
nu blocheaza alocarea urmatoarelor comenzi executabile. Acesta este un algoritm
greedy, nu o optimizare globala Hungarian.

`Task` retine starea (`pending`, `assigned`, `carrying`, `completed`), robotul
alocat si tick-urile de creare, alocare, preluare si finalizare. `FleetRobot`
retine pozitia, baza, tinta, traseul, faza misiunii, pasii parcursi, asteptarile
si livrarile. Incarcarea/descarcarea sunt instantanee la sosire. Cutia este
reprezentata prin comanda; nu exista inca inventar persistent al rafturilor.

### Siguranta miscarii si rezervarile

`coordination.py` contine doi coordonatori, separati de motorul sarcinilor:

- `WindowCoordinator` planifica in spatiu-timp: `(celula, tick relativ)`, inclusiv
  asteptarea pe loc. Foloseste distante spatiale exacte ca euristica. Tinta este
  rezervata dupa sosire pana la sfarsitul ferestrei; pentru tinte mai indepartate
  se planifica un prefix spre ele.
- Cautarea comuna foloseste ramificare de tip CBS: gaseste primul conflict,
  interzice pe rand celula sau muchia implicata fiecarui robot si replanifica
  traseul afectat. Respinge si schimburile frontale. Robotii fara misiune sunt
  rezervati stationar pentru intreaga fereastra.
- Orizont implicit: 12 tick-uri; buget: 80 de noduri de nivel inalt. Planul comun
  este reutilizat pe masura executarii si refacut cand se schimba tintele/harta,
  robotii nu mai sunt unde era prevazut sau fereastra se epuizeaza.
- Daca bugetul nu produce o solutie, se executa un pas cu `ConservativeCoordinator`:
  pozitiile initiale ale celorlalti roboti sunt obstacole, iar destinatiile deja
  alese in tick sunt rezervate. Acest fallback este sigur, dar poate astepta.
- `Fleet.step()` valideaza independent miscarile comune prin `safe_joint_step()`
  inainte sa modifice pozitiile. Detecteaza celule comune, schimburi frontale,
  pasi prea lungi si intrarea in obstacole; un plan invalid opreste flota in acel tick.

Fata de varianta veche, robotii pot acum urma in acelasi tick celula eliberata
de robotul din fata, daca intregul plan comun este sigur. In testul cu doi roboti
in sensuri opuse si un refugiu lateral, unul foloseste refugiul si ambii ajung
la tinta. Asteptarea lunga este raportata, dar aceasta nu este o detectare
formala a ciclurilor de deadlock.

### Limite cunoscute

- Fara garantie de progres in orice harta: blocaje reciproce, asteptare la o
  tinta ocupata si ocoliri repetate sunt posibile. Orizontul si bugetul sunt
  finite; rezolvarea unui prefix nu demonstreaza progresul pe termen lung.
- Bazele sunt parcari; nu exista inca baterie, incarcare electrica sau durate
  fizice de incarcare/descarcare. Robotii ocupa exact o celula, fara inertie.
- Comenzile si harta editata sunt in memorie; nu exista salvare/incarcare.
  Istoricul comenzilor creste pe durata rularii, iar logul pastreaza 80 de mesaje.
- Replanificarea este sincrona. Limita de noduri nu este un termen limita de
  timp real. Coordonatorul nou costa mai mult CPU; nu este pretins optim global.
- Robotii inactivi nu se muta automat pentru a elibera o tinta ocupata de ei.
- Fara server web, Hungarian, comparator fara coordonare, ROS 2 sau integrare LLM.

## Planul pe etape

Estimarile de mai jos sunt cele din idee, nu termene promise.

| Etapa | Livrabil | Estimare initiala | Stare |
| --- | --- | --- | --- |
| 1 | Grid + un robot + A* + vizualizare | 1–2 saptamani | Implementata; `--single` |
| 2 | 4–5 roboti + sarcini aleatorii + alocare simpla | 2 saptamani | Implementata; implicit 5, configurabil 3–8 |
| 3 | Rezervari spatio-temporale / prioritati, evitare conflicte si deadlock | 3–4 saptamani | Partial: A* spatio-temporal + CBS limitat; fara garantie generala de progres |
| 4 | Obstacole live + replanificare | 1–2 saptamani | Implementata, inclusiv invalidarea rezervarilor |
| 5 | Benchmark: fara/cu coordonare, naiv/Hungarian | 2 saptamani | Inceputa: conservator vs. fereastra; restul neimplementat |
| 6 | LLM ca interfata; ROS 2 + Nav2 | Optional | Neinceputa |

### Urmatoarea sesiune: pasi concreti

1. Ruleaza testele si citeste `coordination.py`, `Fleet.step()` si `commands.py`.
   Regresia raportata de utilizator este acoperita inclusiv printr-un eveniment
   real Pygame: o apasare dreapta creeaza a sasea comanda, peste cele cinci demo.
2. Extinde scenariile dense, robotul inactiv care ocupa o tinta, deadlock ciclic,
   pasaj imposibil si sarcini cu destinatii comune. Separa mereu siguranta de progres.
3. Adauga prioritati cu vechime, detectarea ciclurilor de asteptare si mutarea
   robotilor inactivi spre parcari/refugii. Nu declara orice caz rezolvabil.
4. Evalueaza orizonturi/bugete diferite in benchmark. Optimizeaza cache-ul
   distantelor si masoara blocarea UI-ului in scenarii aglomerate.
5. Adauga salvare/incarcare JSON pentru harta si scenarii, pentru reproducerea
   bugurilor semnalate de utilizator. UI-ul poate primi o lista vizibila de comenzi.
6. Continua etapa 5 cu Hungarian vs. greedy si comparator fara coordonare care
   NUMARA coliziunile, fara a deveni modul implicit. Adauga export CSV si grafice.
7. Dupa stabilizarea motorului, adauga serverul Python si UI web. Motorul trebuie
   sa ramana autoritatea pentru miscare; nu dubla regulile de trafic in interfata.
8. LLM si ROS 2 raman bonusuri, dupa etapele de algoritmi si benchmark.

## Benchmark reproductibil

```powershell
.\.venv\Scripts\python.exe benchmark.py --robots 8 --seeds 7 19 42 --ticks 600 --jobs 20 --interval 20 --output artifacts/benchmark.json
```

Nu necesita fereastra sau Pygame. Fiecare coordonator primeste aceleasi comenzi,
la aceleasi tick-uri. Raportul retine si scenariul efectiv. `submitted` poate fi
mai mic decat `requested_jobs` daca rularea este prea scurta pentru intervalul ales.
Latentele sunt calculate doar pentru comenzile finalizate; `unfinished` trebuie
citit impreuna cu ele. Timpii de executie sunt masuratori locale, nu deterministe.

Rezultatul rularii salvate in `artifacts/benchmark.json`, 8 roboti, 20 comenzi,
600 tick-uri pentru fiecare caz:

| Seed | Coordonator | Livrate | Asteptari totale | Latenta medie (tick-uri) | Conflicte |
| --- | --- | --- | --- | --- | --- |
| 7 | conservative | 20/20 | 21 | 31.30 | 0 |
| 7 | window | 20/20 | 1 | 30.45 | 0 |
| 19 | conservative | 20/20 | 7 | 27.65 | 0 |
| 19 | window | 20/20 | 0 | 27.10 | 0 |
| 42 | conservative | 20/20 | 17 | 26.85 | 0 |
| 42 | window | 20/20 | 1 | 25.10 | 0 |

Coordonatorul window a costat aproximativ 0,69–0,71 secunde/rulare fata de
0,10–0,16 secunde pentru comparator pe acest calculator. Rezultatele nu sunt
o dovada de superioritate universala: scenariile dense/imposibile trebuie
masurate separat. Niciun fallback nu a fost necesar in aceste trei scenarii.

## Fisiere si verificari la checkpoint

| Fisier | Rol |
| --- | --- |
| `main.py` | CLI; flota implicit, `--single`, `--robots`, `--seed`, `--coordination` |
| `fleet.py` | Motor: sarcini, alocare, faze, executia comuna si statistici |
| `coordination.py` | A* spatio-temporal, rezolvare limitata de conflicte, fallback, validare |
| `commands.py` | Comanda dintr-un click, preluare manuala si mesaje pentru utilizator |
| `fleet_ui.py` | Harta, mouse/tastatura, generator, panou, feedback si log |
| `benchmark.py` | Scenarii headless identice, metrici si export JSON |
| `grid.py`, `astar.py`, `robot.py` | Grid, A* spatial si robotul demo-ului initial |
| `test_astar.py`, `test_simulation.py`, `test_fleet.py` | Cele 43 de teste anterioare |
| `test_coordination.py`, `test_commands.py`, `test_benchmark.py` | Rezervari, progres, click unic si benchmark |
| `artifacts/fleet-5.png`, `artifacts/fleet-8.png` | Previzualizari actualizate |
| `artifacts/benchmark.json` | Rezultatele comparative si scenariile rulate |

Verificari la acest checkpoint:

- `python -m pytest -q`: **62 passed**.
- Teste pentru asteptare in spatiu-timp, rezervari de muchii, ocuparea tintei dupa
  sosire, prefix spre tinta indepartata, refugiu lateral si urmarire in acelasi tick.
- Teste pentru invalidarea rezervarilor dupa obstacole, robot inactiv, fallback
  la buget mic si bariera independenta de siguranta.
- Teste pentru un click dreapta, Shift+click, click invalid, selectie anulata,
  preluare accesibila dupa distanta A* si integrarea evenimentului Pygame.
- Toate testele vechi de livrare, coliziune, reproductibilitate si editare live.
- Benchmark real pentru ambii coordonatori pe cele trei seed-uri documentate.
- Randare fara fereastra pentru 5/8 roboti si inspectie vizuala a capturilor;
  nu echivaleaza cu o sesiune manuala completa pe desktop.

### Istoric scurt

- Checkpoint 1: 22 teste, un robot, A*, obstacole si pauza.
- Checkpoint 2: 43 teste, flota 3–8, transport si coordonare conservatoare.
- Checkpoint 3 (actual): 62 teste, click unic, coordonare temporala cu refugiu,
  benchmark comparativ. Urmatorul accent: progres in trafic dens si reproducerea
  scenariilor prin salvare/incarcare.

Nu exista un server sau proces de simulare lasat pornit de aceasta sesiune.
Actualizeaza acest README la urmatoarea sesiune cu deciziile, verificarile si
limitarile reale, nu doar cu intentii.
