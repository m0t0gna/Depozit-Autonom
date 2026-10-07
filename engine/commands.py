"""Comenzi de transport independente de UI, inclusiv actiunea cu un click."""
from engine.astar import astar


class TaskCommands:
    def __init__(self, fleet):
        self.fleet = fleet
        self.pickup = None
        self.message = 'Click dreapta: comanda catre celula aleasa; preluarea este automata.'

    def cancel(self):
        self.pickup = None
        self.message = 'Selectie anulata. Click dreapta creeaza imediat o comanda.'

    def right_click(self, cell, custom=False):
        """Un click = livrare; Shift+click incepe alegerea manuala A -> B."""
        if cell is None:
            return None
        if not self.fleet.grid.is_free(cell):
            self.message = 'Celula blocata: alege un culoar sau o statie libera.'
            return None
        if custom:
            self.pickup = cell
            self.message = f'Preluare {cell} selectata. Click dreapta pe destinatie; C anuleaza.'
            return None
        pickup = self.pickup
        if pickup is None:
            candidates = []
            for station in self.fleet.pickups:
                if station == cell:
                    continue
                path, _ = astar(self.fleet.grid, station, cell)
                if path:
                    candidates.append((len(path), station))
            if not candidates:
                self.message = 'Nicio preluare accesibila. Elibereaza un culoar sau foloseste Shift+click.'
                return None
            _, pickup = min(candidates)
        if pickup == cell:
            self.message = 'Destinatia trebuie sa difere de preluare. Alege alta celula.'
            return None
        task = self.fleet.add_task(pickup, cell)
        self.pickup = None
        self.message = f'Comanda #{task.id} creata: {pickup} -> {cell}. Va fi preluata de un robot liber.'
        return task
