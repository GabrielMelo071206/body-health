from typing import List, Optional, Union
from jinja2 import FileSystemLoader
from fastapi.templating import Jinja2Templates


def criar_templates(diretorio_especifico: Optional[Union[str, List[str]]] = None) -> Jinja2Templates:
    """
    Cria um objeto Jinja2Templates configurado com múltiplos diretórios.
    
    O diretório raiz "templates" é sempre incluído automaticamente para garantir
    acesso aos templates base como base.html.
    
    Args:
        diretorio_especifico: Diretório(s) específico(s) além do raiz.
                             Pode ser uma string única ou lista de strings.
                             Exemplo: "templates/admin/categorias" ou
                                     ["templates/admin", "templates/public"]
    
    Returns:
        Objeto Jinja2Templates configurado com os diretórios especificados
    
    Exemplo de uso:
        # Para um diretório específico
        templates = criar_templates("templates/admin/categorias")
        
        # Para múltiplos diretórios
        templates = criar_templates(["templates/admin", "templates/admin/produtos"])
        
        # Apenas com o diretório raiz
        templates = criar_templates()
    """
    # Sempre incluir o diretório raiz onde estão os templates base
    diretorios = ["templates"]
    
    # Adicionar diretórios específicos se fornecidos
    if diretorio_especifico:
        if isinstance(diretorio_especifico, str):
            # Se for uma string única, adiciona à lista
            diretorios.append(diretorio_especifico)
        elif isinstance(diretorio_especifico, list):
            # Se for uma lista, estende a lista de diretórios
            diretorios.extend(diretorio_especifico)
    
    # Criar o objeto Jinja2Templates com diretório base como "."
    # Isso é necessário para que o FileSystemLoader funcione corretamente
    templates = Jinja2Templates(directory=".")
    
    # Configurar o loader com múltiplos diretórios
    # O FileSystemLoader tentará encontrar templates em ordem nos diretórios listados
    templates.env.loader = FileSystemLoader(diretorios)
    
    return templates