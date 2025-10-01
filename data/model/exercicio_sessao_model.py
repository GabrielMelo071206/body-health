from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ExercicioSessao:
    """Exercício dentro de uma sessão de treino"""
    id: int
    sessao_id: int  # referência à SessaoTreino
    exercicio_id: int  # referência ao Exercicio (já existe no sistema)
    ordem: int  # Ordem do exercício na sessão
    series: int
    repeticoes: str  # Ex: "12", "10-12", "até a falha"
    carga: Optional[str] = None  # Ex: "20kg", "peso corporal"
    descanso: Optional[str] = None  # Ex: "60s", "1-2min"
    tecnica: Optional[str] = None  # Ex: "Drop set", "Bi-set", "Super lenta"
    observacoes: Optional[str] = None
    video_demonstracao: Optional[str] = None
