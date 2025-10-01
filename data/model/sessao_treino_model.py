from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SessaoTreino:
    """Sessão individual de treino (ex: Treino A, Treino B)"""
    id: int
    treino_id: int  # referência ao TreinoPersonalizado
    nome: str  # Ex: "Treino A - Peito e Tríceps"
    ordem: int  # Ordem da sessão (1, 2, 3...)
    dia_semana: Optional[str] = None  # Segunda, Terça, etc
    descricao: Optional[str] = None
    tempo_estimado: Optional[int] = None  # em minutos
    status: str = 'ativo'

