# Depozit Autonom

Simulator de depozit in Python, cu interfata Pygame si planificare de trasee A*.

## Instalare (PowerShell, Python 3.12)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Mediul `.venv` este deja pregatit pe acest calculator.

## Pornire

```powershell
.\.venv\Scripts\python.exe main.py
```

- Click stanga: adauga sau elimina un obstacol.
- Click dreapta pe o celula libera: stabileste tinta robotului.
- E: afiseaza sau ascunde celulele explorate.
- R: reseteaza robotul.

## Verificare

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Structura

- `main.py`: interfata si bucla simularii.
- `grid.py`: harta si obstacolele.
- `astar.py`: cautarea traseului.
- `robot.py`: miscarea, replanificarea si jurnalul robotului.
- `test_astar.py`: testele algoritmului.
