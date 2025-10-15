from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from data.repo import plano_repo, usuario_repo, cliente_repo, profissional_repo
from data.repo import personal_repo, personal_aluno_repo, treino_personalizado_repo
from data.repo import avaliacao_fisica_repo, progresso_aluno_repo, sessao_treino_repo
from data.model.usuario_model import Usuario
from data.model.cliente_model import Cliente
from data.model.profissional_model import Profissional
from data.model.plano_model import Plano
from data.model.personal_model import Personal
from data.model.personal_aluno_model import PersonalAluno
from data.model.treino_personalizado_model import TreinoPersonalizado
from util.file_upload import salvar_foto_registro
from util.security import criar_hash_senha, verificar_senha, gerar_senha_aleatoria
from util.auth_decorator import criar_sessao, obter_usuario_logado, requer_autenticacao
from util.email_service import email_service
from data.dtos.cadastro_cliente_dto import validar_cadastro_cliente
from data.dtos.cadastro_profissional_dto import validar_cadastro_profissional, validar_foto_registro
from data.dtos.login_dto import validar_login

templates = Jinja2Templates(directory="templates")







def register_personal_routes(app: FastAPI):
    @app.get("/personal/dashboard")
    @requer_autenticacao(['profissional'])
    async def personal_dashboard(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Dashboard do Personal Trainer com tratamento completo de erros"""
        
        # Contexto base padrão (sempre funciona mesmo com erros)
        contexto_base = {
            "request": request,
            "usuario": usuario_logado,
            "total_alunos": 0,
            "alunos_ativos": 0,
            "total_treinos": 0,
            "total_avaliacoes": 0,
            "atividades": [],
            "lembretes": [],
            "avaliacoes_media": None
        }
        
        try:
            # Buscar profissional
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                print(f"[AVISO] Profissional não encontrado para usuário {usuario_logado['id']}")
                return templates.TemplateResponse("personal/dashboard.html", contexto_base)
            
            # Buscar personal (pode não existir ainda)
            personal = personal_repo.obter_por_profissional(profissional.id)
            
            if not personal:
                print(f"[AVISO] Personal não encontrado para profissional {profissional.id}")
                return templates.TemplateResponse("personal/dashboard.html", contexto_base)
            
            # Estatísticas
            alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            total_alunos = len(alunos)
            alunos_ativos = len([a for a in alunos if a.status == 'ativo'])
            
            # Contar treinos
            total_treinos = 0
            for aluno in alunos:
                try:
                    treinos = treino_personalizado_repo.obter_por_aluno(aluno.id)
                    total_treinos += len(treinos)
                except Exception as e:
                    print(f"[ERRO] Erro ao contar treinos do aluno {aluno.id}: {e}")
            
            # Contar avaliações
            total_avaliacoes = 0
            for aluno in alunos:
                try:
                    avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno.id)
                    total_avaliacoes += len(avaliacoes)
                except Exception as e:
                    print(f"[ERRO] Erro ao contar avaliações do aluno {aluno.id}: {e}")
            
            # Contexto com dados reais
            contexto_sucesso = {
                "request": request,
                "usuario": usuario_logado,
                "total_alunos": total_alunos,
                "alunos_ativos": alunos_ativos,
                "total_treinos": total_treinos,
                "total_avaliacoes": total_avaliacoes,
                "atividades": [],
                "lembretes": [],
                "avaliacoes_media": personal.avaliacoes_media if hasattr(personal, 'avaliacoes_media') else None
            }
            
            return templates.TemplateResponse("personal/dashboard.html", contexto_sucesso)
            
        except Exception as e:
            print(f"[ERRO] Dashboard Personal: {str(e)}")
            import traceback
            traceback.print_exc()
            return templates.TemplateResponse("personal/dashboard.html", contexto_base)
    # =================== GESTÃO DE ALUNOS ===================
    @app.get("/personal/alunos")
    @requer_autenticacao(['profissional'])
    async def personal_alunos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Lista alunos do personal com validação de propriedade"""
        try:
            # Buscar personal do profissional logado
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                return templates.TemplateResponse("personal/alunos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "alunos": [],
                    "erro": "Dados de profissional não encontrados"
                })
            
            personal = personal_repo.obter_por_profissional(profissional.id)
            if not personal:
                return templates.TemplateResponse("personal/alunos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "alunos": [],
                    "aviso": "Cadastro de Personal não encontrado. Entre em contato com o suporte."
                })
            
            # Buscar alunos do personal
            alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            
            # Enriquecer com dados do usuário
            alunos = []
            for rel in alunos_relacionamento:
                try:
                    cliente = cliente_repo.obter_por_id(rel.aluno_id)
                    if not cliente:
                        continue
                        
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if not usuario_aluno:
                        continue
                    
                    # CORREÇÃO: Converter data_inicio para datetime se vier como string
                    data_inicio_convertida = rel.data_inicio
                    if isinstance(rel.data_inicio, str):
                        try:
                            # Tentar formato ISO (YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD)
                            data_inicio_convertida = datetime.fromisoformat(rel.data_inicio.split('.')[0])
                        except (ValueError, AttributeError):
                            try:
                                # Tentar formato brasileiro (DD/MM/YYYY)
                                data_inicio_convertida = datetime.strptime(rel.data_inicio, '%d/%m/%Y')
                            except ValueError:
                                data_inicio_convertida = None
                    
                    alunos.append({
                        'id': rel.id,
                        'aluno_id': rel.aluno_id,
                        'nome': usuario_aluno.nome,
                        'email': usuario_aluno.email,
                        'objetivo': rel.objetivo,
                        'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
                        'status': rel.status,
                        'observacoes': rel.observacoes
                    })
                except Exception as e:
                    print(f"[ERRO] Erro ao processar aluno {rel.aluno_id}: {e}")
                    continue
            
            return templates.TemplateResponse("personal/alunos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "alunos": alunos
            })
            
        except Exception as e:
            print(f"[ERRO] Listar alunos: {str(e)}")
            import traceback
            traceback.print_exc()
            return templates.TemplateResponse("personal/alunos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "alunos": [],
                "erro": "Erro ao carregar lista de alunos"
            })


    @app.get("/personal/alunos/novo")
    @requer_autenticacao(['profissional'])
    async def personal_alunos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        # Buscar lista de clientes disponíveis para vincular
        clientes = cliente_repo.obter_todos()
        clientes_disponiveis = []
        
        for cliente in clientes:
            usuario = usuario_repo.obter_por_id(cliente.usuario_id)
            if usuario:
                clientes_disponiveis.append({
                    'id': cliente.usuario_id,
                    'nome': usuario.nome,
                    'email': usuario.email
                })
        
        return templates.TemplateResponse("personal/alunos/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "aluno": None,
            "clientes_disponiveis": clientes_disponiveis
        })
        
    @app.post("/personal/treinos/salvar")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_salvar(
        request: Request,
        treino_id: Optional[int] = Form(None),
        aluno_id: int = Form(...),
        nome: str = Form(...),
        objetivo: str = Form(...),
        nivel_dificuldade: str = Form(...),
        frequencia_semanal: int = Form(...),
        duracao_semanas: int = Form(...),
        descricao: Optional[str] = Form(None),
        observacoes: Optional[str] = Form(None),
        status: str = Form('ativo'),
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Salvar treino (criar ou atualizar) - VERSÃO CORRIGIDA"""
        try:
            if treino_id:
                # Atualizar treino existente
                treino = treino_personalizado_repo.obter_por_id(treino_id)
                if treino:
                    treino.nome = nome
                    treino.objetivo = objetivo
                    treino.nivel_dificuldade = nivel_dificuldade
                    treino.frequencia_semanal = frequencia_semanal
                    treino.duracao_semanas = duracao_semanas
                    treino.descricao = descricao
                    treino.observacoes = observacoes
                    treino.status = status
                    treino_personalizado_repo.alterar(treino)
                    return RedirectResponse("/personal/treinos?sucesso=Treino atualizado com sucesso", status_code=303)
            else:
                # Criar novo treino - COM ARGUMENTOS OBRIGATÓRIOS
                novo_treino = TreinoPersonalizado(
                    id=0,
                    personal_aluno_id=aluno_id,  # Campo correto
                    nome=nome,
                    objetivo=objetivo,
                    nivel_dificuldade=nivel_dificuldade
                )
                
                # Setar atributos opcionais
                novo_treino.frequencia_semanal = frequencia_semanal
                novo_treino.duracao_semanas = duracao_semanas
                novo_treino.descricao = descricao
                novo_treino.observacoes = observacoes
                novo_treino.status = status
                novo_treino.criado_em = datetime.now()
                
                treino_personalizado_repo.inserir(novo_treino)
                return RedirectResponse("/personal/treinos?sucesso=Treino criado com sucesso", status_code=303)
                
        except Exception as e:
            print(f"[ERRO] Salvar treino: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/treinos?erro=Erro ao salvar treino", status_code=303)


    @app.get("/personal/alunos/{aluno_id}")
    @requer_autenticacao(['profissional'])
    async def personal_alunos_detalhes(
        request: Request, 
        aluno_id: int, 
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Detalhes do aluno com validação de propriedade"""
        try:
            # Validar se o aluno pertence ao personal logado
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
            
            personal = personal_repo.obter_por_profissional(profissional.id)
            if not personal:
                return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
            
            # Buscar relacionamento e validar propriedade
            aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/alunos?erro=Aluno não encontrado ou acesso negado", status_code=303)
            
            # Buscar dados do cliente/usuário
            cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
            if not cliente:
                return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
            
            usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
            if not usuario_aluno:
                return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
            
            # CORREÇÃO: Converter data_inicio para datetime se vier como string
            data_inicio_convertida = aluno_rel.data_inicio
            if isinstance(aluno_rel.data_inicio, str):
                try:
                    data_inicio_convertida = datetime.fromisoformat(aluno_rel.data_inicio.split('.')[0])
                except (ValueError, AttributeError):
                    try:
                        data_inicio_convertida = datetime.strptime(aluno_rel.data_inicio, '%d/%m/%Y')
                    except ValueError:
                        data_inicio_convertida = None
            
            # Montar objeto aluno
            aluno = {
                'id': aluno_rel.id,
                'aluno_id': aluno_rel.aluno_id,
                'nome': usuario_aluno.nome,
                'email': usuario_aluno.email,
                'objetivo': aluno_rel.objetivo,
                'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
                'status': aluno_rel.status,
                'observacoes': aluno_rel.observacoes
            }
            
            # Buscar treinos ativos
            treinos_ativos = []
            try:
                treinos_ativos = treino_personalizado_repo.obter_por_aluno(aluno_id)
            except Exception as e:
                print(f"[ERRO] Erro ao buscar treinos: {e}")
            
            # Buscar avaliações
            avaliacoes = []
            ultima_avaliacao = None
            try:
                avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno_id)
                if avaliacoes:
                    ultima_avaliacao = avaliacoes[0].data_avaliacao
            except Exception as e:
                print(f"[ERRO] Erro ao buscar avaliações: {e}")
            
            # Buscar progressos
            progressos = []
            try:
                progressos = progresso_aluno_repo.obter_por_aluno(aluno_id)
            except Exception as e:
                print(f"[ERRO] Erro ao buscar progressos: {e}")
            
            return templates.TemplateResponse("personal/alunos/detalhes.html", {
                "request": request,
                "usuario": usuario_logado,
                "aluno": aluno,
                "treinos_ativos": treinos_ativos,
                "ultima_avaliacao": ultima_avaliacao,
                "avaliacoes": avaliacoes,
                "progressos": progressos
            })
            
        except Exception as e:
            print(f"[ERRO] Detalhes aluno: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/alunos?erro=Erro ao carregar detalhes do aluno", status_code=303)


    @app.get("/personal/alunos/{aluno_id}/editar")
    @requer_autenticacao(['profissional'])
    async def personal_alunos_editar_get(
        request: Request, 
        aluno_id: int, 
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Formulário de edição com validação de propriedade"""
        try:
            # Validar propriedade
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
            
            personal = personal_repo.obter_por_profissional(profissional.id)
            if not personal:
                return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
            
            aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/alunos?erro=Aluno não encontrado", status_code=303)
            
            # Buscar dados do aluno
            cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
            usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
            
            if not usuario_aluno:
                return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
            
            # CORREÇÃO: Converter data_inicio para datetime se vier como string
            data_inicio_convertida = aluno_rel.data_inicio
            if isinstance(aluno_rel.data_inicio, str):
                try:
                    data_inicio_convertida = datetime.fromisoformat(aluno_rel.data_inicio.split('.')[0])
                except (ValueError, AttributeError):
                    try:
                        data_inicio_convertida = datetime.strptime(aluno_rel.data_inicio, '%d/%m/%Y')
                    except ValueError:
                        data_inicio_convertida = None
            
            aluno = {
                'id': aluno_rel.id,
                'nome': usuario_aluno.nome,
                'email': usuario_aluno.email,
                'objetivo': aluno_rel.objetivo,
                'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
                'status': aluno_rel.status,
                'observacoes': aluno_rel.observacoes
            }
            
            return templates.TemplateResponse("personal/alunos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "aluno": aluno,
                "clientes_disponiveis": []  # Não precisa ao editar
            })
            
        except Exception as e:
            print(f"[ERRO] Editar aluno GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/alunos?erro=Erro ao carregar aluno", status_code=303)

    # =================== GESTÃO COMPLETA DE TREINOS ===================
    # Adicione estas rotas após a rota personal_treinos_listar existente

    # =================== GESTÃO DE TREINOS - LISTAGEM ===================
    @app.get("/personal/treinos")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Lista todos os treinos do personal com validação de propriedade"""
        try:
            # Buscar profissional e personal
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                return templates.TemplateResponse("personal/treinos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "treinos": [],
                    "erro": "Dados de profissional não encontrados"
                })
            
            personal = personal_repo.obter_por_profissional(profissional.id)
            if not personal:
                return templates.TemplateResponse("personal/treinos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "treinos": [],
                    "aviso": "Cadastro de Personal não encontrado"
                })
            
            # Buscar todos os alunos do personal
            alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            
            # Buscar treinos de cada aluno
            todos_treinos = []
            for rel in alunos_relacionamento:
                try:
                    treinos_aluno = treino_personalizado_repo.obter_por_aluno(rel.id)
                    
                    # Buscar nome do aluno
                    cliente = cliente_repo.obter_por_id(rel.aluno_id)
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                    aluno_nome = usuario_aluno.nome if usuario_aluno else 'N/A'
                    
                    # Adicionar treinos com informações do aluno (CAMPOS CORRETOS DO BANCO)
                    for treino in treinos_aluno:
                        todos_treinos.append({
                            'id': treino.id,
                            'nome': treino.nome,
                            'aluno_nome': aluno_nome,
                            'objetivo': treino.objetivo,
                            'nivel_dificuldade': treino.nivel_dificuldade,
                            'status': 'ativo',  # Valor fixo (campo não existe no banco)
                            'criado_em': None,  # Campo não existe no banco
                            'frequencia_semanal': getattr(treino, 'dias_semana', None),  # Usar dias_semana
                            'duracao_semanas': treino.duracao_semanas,
                            'descricao': treino.descricao,
                            'divisao_treino': getattr(treino, 'divisao_treino', None)
                        })
                except Exception as e:
                    print(f"[ERRO] Erro ao buscar treinos do aluno {rel.id}: {e}")
                    continue
            
            # Ordenar por ID (mais recente primeiro, já que não temos data)
            todos_treinos.sort(key=lambda x: x['id'], reverse=True)
            
            return templates.TemplateResponse("personal/treinos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "treinos": todos_treinos
            })
            
        except Exception as e:
            print(f"[ERRO] Listar treinos: {str(e)}")
            import traceback
            traceback.print_exc()
            return templates.TemplateResponse("personal/treinos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "treinos": [],
                "erro": "Erro ao carregar lista de treinos"
            })


    # =================== SALVAR TREINO - CORRIGIDO ===================


    @app.get("/personal/treinos/novo")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Formulário para criar novo treino"""
        try:
            # Buscar personal
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/treinos?erro=Personal não encontrado", status_code=303)
            
            # Buscar alunos do personal
            alunos_rel = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            alunos_disponiveis = []
            
            for rel in alunos_rel:
                cliente = cliente_repo.obter_por_id(rel.aluno_id)
                if cliente:
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if usuario_aluno:
                        alunos_disponiveis.append({
                            'id': rel.id,
                            'nome': usuario_aluno.nome,
                            'email': usuario_aluno.email
                        })
            
            return templates.TemplateResponse("personal/treinos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "treino": None,
                "alunos_disponiveis": alunos_disponiveis,
                "titulo": "Criar Novo Treino",
                "acao": "/personal/treinos/salvar"
            })
        except Exception as e:
            print(f"[ERRO] Novo treino GET: {str(e)}")
            return RedirectResponse("/personal/treinos?erro=Erro ao carregar formulário", status_code=303)

    # =================== SALVAR TREINO - CORRIGIDO ===================
    @app.post("/personal/treinos/salvar")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_salvar(
        request: Request,
        treino_id: Optional[int] = Form(None),
        aluno_id: int = Form(...),
        nome: str = Form(...),
        objetivo: str = Form(...),
        nivel_dificuldade: str = Form(...),
        frequencia_semanal: int = Form(...),
        duracao_semanas: int = Form(...),
        descricao: Optional[str] = Form(None),
        observacoes: Optional[str] = Form(None),
        status: str = Form('ativo'),
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Salvar treino (criar ou atualizar) - CAMPOS CORRETOS DO BANCO"""
        try:
            if treino_id:
                # Atualizar treino existente
                treino = treino_personalizado_repo.obter_por_id(treino_id)
                if treino:
                    treino.nome = nome
                    treino.objetivo = objetivo
                    treino.nivel_dificuldade = nivel_dificuldade
                    treino.dias_semana = frequencia_semanal  # Campo correto
                    treino.duracao_semanas = duracao_semanas
                    treino.descricao = descricao
                    # observacoes e status não existem no banco
                    treino_personalizado_repo.alterar(treino)
                    return RedirectResponse("/personal/treinos?sucesso=Treino atualizado com sucesso", status_code=303)
            else:
                # Criar novo treino - COM CAMPOS CORRETOS
                novo_treino = TreinoPersonalizado(
                    id=0,
                    personal_aluno_id=aluno_id,
                    nome=nome,
                    objetivo=objetivo,
                    nivel_dificuldade=nivel_dificuldade
                )
                
                # Setar atributos opcionais (CAMPOS CORRETOS)
                novo_treino.dias_semana = frequencia_semanal  # Campo correto
                novo_treino.duracao_semanas = duracao_semanas
                novo_treino.descricao = descricao
                novo_treino.divisao_treino = None  # Pode adicionar depois
                # observacoes, status e criado_em não existem no banco
            
                
                treino_personalizado_repo.inserir(novo_treino)
                return RedirectResponse("/personal/treinos?sucesso=Treino criado com sucesso", status_code=303)
                
        except Exception as e:
            print(f"[ERRO] Salvar treino: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/treinos?erro=Erro ao salvar treino", status_code=303)
                                    
    @app.get("/personal/treinos/{treino_id}")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_detalhes(
        request: Request,
        treino_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Ver detalhes do treino"""
        try:
            treino = treino_personalizado_repo.obter_por_id(treino_id)
            if not treino:
                return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
            
            # Buscar dados do aluno
            aluno_rel = personal_aluno_repo.obter_por_id(treino.aluno_id)
            aluno_nome = "N/A"
            
            if aluno_rel:
                cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
                if cliente:
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if usuario_aluno:
                        aluno_nome = usuario_aluno.nome
            
            # Buscar sessões de treino (se houver)
            sessoes = sessao_treino_repo.obter_por_treino(treino_id) if hasattr(sessao_treino_repo, 'obter_por_treino') else []
            
            return templates.TemplateResponse("personal/treinos/detalhes.html", {
                "request": request,
                "usuario": usuario_logado,
                "treino": treino,
                "aluno_nome": aluno_nome,
                "sessoes": sessoes
            })
        except Exception as e:
            print(f"[ERRO] Detalhes treino: {str(e)}")
            return RedirectResponse("/personal/treinos?erro=Erro ao carregar detalhes", status_code=303)


    @app.get("/personal/treinos/{treino_id}/editar")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_editar_get(
        request: Request,
        treino_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Formulário para editar treino"""
        try:
            treino = treino_personalizado_repo.obter_por_id(treino_id)
            if not treino:
                return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
            
            # Buscar personal e alunos
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            alunos_rel = personal_aluno_repo.obter_alunos_por_personal(personal.id) if personal else []
            alunos_disponiveis = []
            
            for rel in alunos_rel:
                cliente = cliente_repo.obter_por_id(rel.aluno_id)
                if cliente:
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if usuario_aluno:
                        alunos_disponiveis.append({
                            'id': rel.id,
                            'nome': usuario_aluno.nome,
                            'email': usuario_aluno.email
                        })
            
            return templates.TemplateResponse("personal/treinos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "treino": treino,
                "alunos_disponiveis": alunos_disponiveis,
                "titulo": "Editar Treino",
                "acao": "/personal/treinos/salvar"
            })
        except Exception as e:
            print(f"[ERRO] Editar treino GET: {str(e)}")
            return RedirectResponse("/personal/treinos?erro=Erro ao carregar treino", status_code=303)


    @app.post("/personal/treinos/excluir/{treino_id}")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_excluir(
        request: Request,
        treino_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Excluir treino"""
        try:
            treino = treino_personalizado_repo.obter_por_id(treino_id)
            if not treino:
                return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
            
            # Excluir sessões relacionadas primeiro (se houver)
            if hasattr(sessao_treino_repo, 'excluir_por_treino'):
                sessao_treino_repo.excluir_por_treino(treino_id)
            
            # Excluir treino
            treino_personalizado_repo.excluir(treino_id)
            
            return RedirectResponse("/personal/treinos?sucesso=Treino excluído com sucesso", status_code=303)
        except Exception as e:
            print(f"[ERRO] Excluir treino: {str(e)}")
            return RedirectResponse("/personal/treinos?erro=Erro ao excluir treino", status_code=303)



    # =================== GESTÃO DE AVALIAÇÕES FÍSICAS ===================
    @app.get("/personal/avaliacoes")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        try:
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "avaliacoes": []
                })
            
            # Buscar todos os alunos e suas avaliações
            alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            todas_avaliacoes = []
            
            for aluno in alunos:
                avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno.id)
                for avaliacao in avaliacoes:
                    cliente = cliente_repo.obter_por_id(aluno.aluno_id)
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                    
                    todas_avaliacoes.append({
                        'id': avaliacao.id,
                        'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                        'data_avaliacao': avaliacao.data_avaliacao,
                        'peso': avaliacao.peso,
                        'imc': avaliacao.imc,
                        'percentual_gordura': avaliacao.percentual_gordura
                    })
            
            # Ordenar por data (mais recente primeiro)
            todas_avaliacoes.sort(key=lambda x: x['data_avaliacao'], reverse=True)
            
            return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacoes": todas_avaliacoes
            })
        except Exception as e:
            print(f"[ERRO] Listar avaliações: {str(e)}")
            return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacoes": []
            })

    # =================== GESTÃO DE PROGRESSOS ===================
    @app.get("/personal/progressos")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        try:
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return templates.TemplateResponse("personal/progressos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "progressos": []
                })
            
            # Buscar progressos de todos os alunos
            alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            todos_progressos = []
            
            for aluno in alunos:
                progressos = progresso_aluno_repo.obter_por_aluno(aluno.id)
                for progresso in progressos:
                    cliente = cliente_repo.obter_por_id(aluno.aluno_id)
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                    
                    todos_progressos.append({
                        'id': progresso.id,
                        'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                        'data_registro': progresso.data_registro,
                        'peso': progresso.peso,
                        'humor': progresso.humor,
                        'energia': progresso.energia
                    })
            
            # Ordenar por data
            todos_progressos.sort(key=lambda x: x['data_registro'], reverse=True)
            
            return templates.TemplateResponse("personal/progressos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "progressos": todos_progressos
            })
        except Exception as e:
            print(f"[ERRO] Listar progressos: {str(e)}")
            return templates.TemplateResponse("personal/progressos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "progressos": []
            })

    # =================== PERFIL DO PERSONAL ===================
    @app.get("/personal/perfil")
    @requer_autenticacao(['profissional'])
    async def personal_perfil(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        try:
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            return templates.TemplateResponse("personal/perfil.html", {
                "request": request,
                "usuario": usuario_logado,
                "profissional": profissional,
                "personal": personal
            })
        except Exception as e:
            print(f"[ERRO] Perfil personal: {str(e)}")
            return templates.TemplateResponse("personal/perfil.html", {
                "request": request,
                "usuario": usuario_logado,
                "profissional": None,
                "personal": None
            })
