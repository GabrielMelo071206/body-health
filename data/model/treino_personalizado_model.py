# from dataclasses import dataclass
# from typing import Optional
# from datetime import datetime


# @dataclass
# class TreinoPersonalizado:
#     """Treino criado pelo Personal para um aluno específico"""
#     id: int
#     personal_aluno_id: int  # referência ao relacionamento Personal-Aluno
#     nome: str
#     descricao: Optional[str] = None
#     objetivo: str  # Hipertrofia, Emagrecimento, Condicionamento, etc
#     nivel_dificuldade: str  # Iniciante, Intermediário, Avançado
#     duracao_semanas: Optional[int] = None
#     dias_semana: int = 3  # Quantos dias por semana
#     divisao_treino: Optional[str] = None  # Ex: "ABC", "ABCD", "Push/Pull/Legs"
#     observacoes: Optional[str] = None
#     status: str = 'ativo'  # ativo, pausado, concluído
#     data_inicio: Optional[datetime] = None
#     data_fim: Optional[datetime] = None
#     criado_em: datetime = datetime.now()
#     atualizado_em: Optional[datetime] = None

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TreinoPersonalizado:
    """Treino criado pelo Personal para um aluno específico"""
    
    # 1. NON-DEFAULT ARGUMENTS (Required fields first)
    # These fields MUST be passed a value when creating an instance.
    id: int
    personal_aluno_id: int  # referência ao relacionamento Personal-Aluno
    nome: str
    objetivo: str           # Hipertrofia, Emagrecimento, Condicionamento, etc
    nivel_dificuldade: str  # Iniciante, Intermediário, Avançado

    # 2. DEFAULT ARGUMENTS (Optional fields next)
    # These fields will use the provided default if a value is not passed.
    descricao: Optional[str] = None
    duracao_semanas: Optional[int] = None
    dias_semana: int = 3    # Quantos dias por semana
    divisao_treino: Optional[str] = None  # Ex: "ABC", "ABCD", "Push/Pull/Legs"
    observacoes: Optional[str] = None
    status: str = 'ativo'   # ativo, pausado, concluído
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    criado_em: datetime = datetime.now()
    atualizado_em: Optional[datetime] = None