# util/file_upload.py - NOVO ARQUIVO
import os
import uuid
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "static/uploads/profissionais"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def salvar_foto_registro(arquivo: UploadFile) -> str:
    """Salva foto de registro profissional e retorna o path"""
    
    if not arquivo or not arquivo.filename:
        raise HTTPException(400, "Arquivo obrigatório")
    
    # Validar tipo
    tipos_permitidos = ['image/jpeg', 'image/png', 'image/jpg']
    if arquivo.content_type not in tipos_permitidos:
        raise HTTPException(400, "Apenas imagens JPG/PNG são permitidas")
    
    # Validar tamanho (máximo 5MB)
    conteudo = await arquivo.read()
    if len(conteudo) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(400, "Arquivo muito grande (máximo 5MB)")
    
    # Gerar nome único
    extensao = arquivo.filename.split('.')[-1].lower()
    nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
    caminho_completo = os.path.join(UPLOAD_DIR, nome_arquivo)
    
    # Salvar arquivo
    with open(caminho_completo, "wb") as f:
        f.write(conteudo)
    
    # Retornar path web
    return f"/static/uploads/profissionais/{nome_arquivo}"

def validar_cpf_cnpj(documento: str) -> bool:
    """Validação básica de CPF/CNPJ"""
    documento = ''.join(filter(str.isdigit, documento))
    
    if len(documento) == 11:  # CPF
        return validar_cpf(documento)
    elif len(documento) == 14:  # CNPJ
        return validar_cnpj(documento)
    else:
        return False

def validar_cpf(cpf: str) -> bool:
    """Validação básica de CPF"""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Algoritmo de validação do CPF
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2

def validar_cnpj(cnpj: str) -> bool:
    """Validação básica de CNPJ"""
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    
    # Algoritmo simplificado
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto1 = soma1 % 11
    digito1 = 0 if resto1 < 2 else 11 - resto1
    
    if int(cnpj[12]) != digito1:
        return False
    
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto2 = soma2 % 11
    digito2 = 0 if resto2 < 2 else 11 - resto2
    
    return int(cnpj[13]) == digito2