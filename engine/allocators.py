from engine.astar import astar
import numpy as np
from scipy.optimize import linear_sum_assignment

class GreedyAllocator:
    """Alocare FIFO: prima comandă primește cel mai apropiat robot."""
    name = "greedy"
    
    def assign(self, fleet):
        for task in fleet.tasks:
            if task.status != 'pending':
                continue
            free = [r for r in fleet.robots if r.available]
            if not free:
                break
                
            # Verificăm dacă dropoff-ul este accesibil
            delivery_path, _ = astar(fleet.grid, task.pickup, task.dropoff)
            if delivery_path is None:
                continue
                
            candidates = []
            for robot in free:
                path, _ = astar(fleet.grid, robot.pos, task.pickup)
                if path is not None:
                    candidates.append((len(path) - 1, robot.id, robot))
                    
            if not candidates:
                continue
                
            _, _, robot = min(candidates)
            fleet._execute_assignment(robot, task)

class HungarianAllocator:
    """Alocare globală optimă folosind algoritmul Hungarian (Munkres)."""
    name = "hungarian"
    
    def assign(self, fleet):
        pending_tasks = [t for t in fleet.tasks if t.status == 'pending']
        free_robots = [r for r in fleet.robots if r.available]
        
        if not pending_tasks or not free_robots:
            return
            
        # Păstrăm doar comenzile cu drum valid spre livrare
        valid_tasks = []
        for task in pending_tasks:
            dp, _ = astar(fleet.grid, task.pickup, task.dropoff)
            if dp is not None:
                valid_tasks.append(task)
                
        if not valid_tasks:
            return
            
        n_robots = len(free_robots)
        n_tasks = len(valid_tasks)
        
        # Construim matricea de cost. Cost mare = imposibil
        cost_matrix = np.full((n_robots, n_tasks), 1000000.0)
        
        for i, robot in enumerate(free_robots):
            for j, task in enumerate(valid_tasks):
                path, _ = astar(fleet.grid, robot.pos, task.pickup)
                if path is not None:
                    cost_matrix[i, j] = len(path) - 1
                    
        # linear_sum_assignment găsește pairing-ul care minimizează costul total
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        for i, j in zip(row_ind, col_ind):
            # Dacă costul e sub pragul de infinit, înseamnă că e un drum valid
            if cost_matrix[i, j] < 1000000.0:
                fleet._execute_assignment(free_robots[i], valid_tasks[j])
