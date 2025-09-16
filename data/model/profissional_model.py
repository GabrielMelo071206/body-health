from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Profissional:
    usuario_id: int  
    especialidade: str
    registro_profissional: Optional[str] = None
    status: str = 'pendente'  # NOVO: 'pendente', 'aprovado', 'rejeitado'
    data_solicitacao: datetime = None
    data_aprovacao: Optional[datetime] = None
    aprovado_por: Optional[int] = None  # ID do admin que aprovou