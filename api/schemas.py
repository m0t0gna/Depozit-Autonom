from pydantic import BaseModel
from typing import List, Tuple, Optional

class RobotState(BaseModel):
    id: int
    pos: Tuple[int, int]
    home: Tuple[int, int]
    phase: str
    task_id: Optional[int]
    goal: Optional[Tuple[int, int]]
    steps: int
    wait_ticks: int
    deliveries: int
    carrying: bool

class TaskState(BaseModel):
    id: int
    pickup: Tuple[int, int]
    dropoff: Tuple[int, int]
    status: str
    robot_id: Optional[int]

class FleetState(BaseModel):
    tick: int
    robots: List[RobotState]
    tasks: List[TaskState]
    grid_width: int
    grid_height: int
    blocked: List[Tuple[int, int]]
    dropoffs: List[Tuple[int, int]]
    completed: int
    pending: int

class TaskRequest(BaseModel):
    pickup: Tuple[int, int]
    dropoff: Tuple[int, int]

class EditRequest(BaseModel):
    cell: Tuple[int, int]
