from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Dieta:
    id: int
    profissional_id: int
    cliente_id: Optional[int] = None  
    descricao: str = ''
    gratuito: bool = True
    data_inicio: datetime = datetime.now()
    data_fim: Optional[datetime] = None