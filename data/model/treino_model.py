from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Treino:
    id: int
    id_cliente: int
    id_profissional: int
    capa: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    duracao: Optional[int] = None  # duração em minutos
    nivel_dificuldade: Optional[str] = None  # Ex: Iniciante, Intermediário, Avançado
    objetivo: Optional[str] = None  # Ex: Perda de peso, Ganho de massa muscular
    status: str = 'ativo'  # Ex: ativo, inativo
    criado_em: Optional[datetime] = None 
    atualizado_em: Optional[datetime] = None
    criado_por: Optional[int] = None  # ID do profissional que criou o treino
    atualizado_por: Optional[int] = None  # ID do profissional que atualizou o treino
