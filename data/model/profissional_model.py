from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# data/model/profissional_model.py - ADICIONAR CAMPOS
@dataclass
class Profissional:
    id: int  
    especialidade: str
    registro_profissional: Optional[str] = None
    status: str = 'pendente'
    data_solicitacao: Optional[datetime] = None
    data_aprovacao: Optional[datetime] = None
    aprovado_por: Optional[int] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
    aprovado_por_nome: Optional[str] = None
    # NOVOS CAMPOS
    cpf_cnpj: Optional[str] = None
    foto_registro: Optional[str] = None