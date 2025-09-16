from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Cliente:
    usuario_id: int            
    plano_id: Optional[int] = None  

