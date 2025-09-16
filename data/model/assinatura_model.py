from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Assinatura:
    id: int
    usuario_id: int   
    plano_id: int
    data_inicio: datetime
    data_fim: datetime