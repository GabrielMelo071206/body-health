from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Profissional:
    usuario_id: int  
    especialidade: str
    registro_profissional: Optional[str] = None