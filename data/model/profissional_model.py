from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Profissional:
    id: int  
    especialidade: str
    registro_profissional: Optional[str] = None
    status: str = 'pendente'  # 'pendente', 'aprovado', 'rejeitado', 'inativo'
    data_solicitacao: Optional[datetime] = None
    data_aprovacao: Optional[datetime] = None
    aprovado_por: Optional[int] = None  # ID do admin que aprovou
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
    aprovado_por_nome: Optional[str] = None