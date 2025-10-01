from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Personal:
    id: int
    profissional_id: int  # referência ao Profissional (que já tem especialidade)
    cref: Optional[str] = None  # Registro no Conselho Regional de Educação Física
    especialidades: Optional[str] = None  # Ex: "Musculação, Funcional, Crossfit"
    biografia: Optional[str] = None
    anos_experiencia: Optional[int] = None
    valor_mensalidade: Optional[float] = None
    status: str = 'ativo'  # ativo, inativo
    data_cadastro: Optional[datetime] = None
    foto_perfil: Optional[str] = None
    avaliacoes_media: Optional[float] = None  # Média de avaliações dos alunos
    total_alunos: int = 0
