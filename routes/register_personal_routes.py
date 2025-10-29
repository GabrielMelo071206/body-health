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
from fastapi import Form, Request, Depends
from fastapi.responses import RedirectResponse
from datetime import datetime
from data.repo import personal_aluno_repo, treino_personalizado_repo
from data.model.treino_personalizado_model import TreinoPersonalizado
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
        
   # routes/personal.py - ROTA PARA SALVAR TREINO CORRIGIDA



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
    # routes/register_personal_routes.py
# SUBSTITUA AS ROTAS DE TREINO POR ESTAS VERSÕES CORRIGIDAS

# ============================================
# ROTA: LISTAR TREINOS (mantém igual)
# ============================================
    @app.get("/personal/treinos")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Lista todos os treinos do personal"""
        try:
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            if not profissional:
                return templates.TemplateResponse("personal/treinos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "treinos": []
                })
            
            personal = personal_repo.obter_por_profissional(profissional.id)
            if not personal:
                return templates.TemplateResponse("personal/treinos/listar.html", {
                    "request": request,
                    "usuario": usuario_logado,
                    "treinos": []
                })
            
            alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            todos_treinos = []
            
            for rel in alunos_relacionamento:
                try:
                    treinos_aluno = treino_personalizado_repo.obter_por_aluno(rel.id)
                    cliente = cliente_repo.obter_por_id(rel.aluno_id)
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                    aluno_nome = usuario_aluno.nome if usuario_aluno else 'N/A'
                    
                    for treino in treinos_aluno:
                        todos_treinos.append({
                            'id': treino.id,
                            'nome': treino.nome,
                            'aluno_nome': aluno_nome,
                            'objetivo': treino.objetivo,
                            'nivel_dificuldade': treino.nivel_dificuldade,
                            'status': 'ativo',
                            'criado_em': None,
                            'frequencia_semanal': getattr(treino, 'dias_semana', None),
                            'duracao_semanas': treino.duracao_semanas,
                            'descricao': treino.descricao
                        })
                except Exception as e:
                    print(f"[ERRO] Erro ao buscar treinos do aluno {rel.id}: {e}")
                    continue
            
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
                "treinos": []
            })


    # ============================================
    # ROTA: NOVO TREINO (GET)
    # ============================================
    @app.get("/personal/treinos/novo")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Formulário para criar novo treino"""
        try:
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/treinos?erro=Personal não encontrado", status_code=303)
            
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


    # ============================================
    # ROTA: EDITAR TREINO (GET) - CORRIGIDA
    # ============================================
    @app.get("/personal/treinos/{treino_id}/editar")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_editar_get(
        request: Request,
        treino_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Formulário para editar treino - VERSÃO CORRIGIDA"""
        try:
            print(f"[DEBUG] Carregando formulário de edição do treino {treino_id}")
            
            # Buscar treino
            treino = treino_personalizado_repo.obter_por_id(treino_id)
            if not treino:
                print(f"[ERRO] Treino {treino_id} não encontrado")
                return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
            
            print(f"[DEBUG] Treino encontrado: {treino.nome}")
            print(f"[DEBUG] PersonalAluno ID: {treino.personal_aluno_id}")
            
            # Buscar personal e validar propriedade
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/treinos?erro=Personal não encontrado", status_code=303)
            
            # Validar que o treino pertence a este personal
            aluno_rel = personal_aluno_repo.obter_por_id(treino.personal_aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                print(f"[ERRO] Treino não pertence ao personal logado")
                return RedirectResponse("/personal/treinos?erro=Acesso negado", status_code=303)
            
            # Buscar todos os alunos do personal (para o dropdown)
            alunos_rel_lista = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            alunos_disponiveis = []
            
            for rel in alunos_rel_lista:
                cliente = cliente_repo.obter_por_id(rel.aluno_id)
                if cliente:
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if usuario_aluno:
                        alunos_disponiveis.append({
                            'id': rel.id,
                            'nome': usuario_aluno.nome,
                            'email': usuario_aluno.email
                        })
            
            # Converter treino para dict com campos corretos do formulário
            treino_dict = {
                'id': treino.id,
                'aluno_id': treino.personal_aluno_id,  # ID do relacionamento
                'nome': treino.nome,
                'objetivo': treino.objetivo,
                'nivel_dificuldade': treino.nivel_dificuldade,
                'frequencia_semanal': treino.dias_semana,  # ← IMPORTANTE: dias_semana → frequencia_semanal
                'duracao_semanas': treino.duracao_semanas,
                'descricao': treino.descricao,
                'status': 'ativo'  # Valor fixo (campo não existe no banco)
            }
            
            print(f"[DEBUG] Treino dict preparado: {treino_dict}")
            
            return templates.TemplateResponse("personal/treinos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "treino": treino_dict,
                "alunos_disponiveis": alunos_disponiveis,
                "titulo": "Editar Treino",
                "acao": "/personal/treinos/salvar"
            })
            
        except Exception as e:
            print(f"[ERRO] Editar treino GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/treinos?erro=Erro ao carregar treino", status_code=303)


    # ============================================
    # ROTA: SALVAR TREINO (POST) - CORRIGIDA
    # ============================================
    @app.post("/personal/treinos/salvar")
    @requer_autenticacao(['profissional'])
    async def personal_treinos_salvar(
        request: Request,
        usuario_logado: dict = Depends(obter_usuario_logado),
        treino_id: Optional[int] = Form(None),
        aluno_id: int = Form(...),
        nome: str = Form(...),
        objetivo: str = Form(...),
        nivel_dificuldade: str = Form(...),
        frequencia_semanal: int = Form(...),
        duracao_semanas: int = Form(...),
        descricao: Optional[str] = Form(None),
        observacoes: Optional[str] = Form(None),
        status: str = Form('ativo')
    ):
        """
        Salvar treino (criar ou atualizar) - VERSÃO FINAL CORRIGIDA
        """
        try:
            print("=" * 80)
            print(f"[DEBUG] SALVANDO TREINO")
            print(f"[DEBUG] treino_id: {treino_id} (None = criar novo, número = editar)")
            print(f"[DEBUG] aluno_id: {aluno_id}")
            print(f"[DEBUG] nome: {nome}")
            print(f"[DEBUG] objetivo: {objetivo}")
            print(f"[DEBUG] nivel_dificuldade: {nivel_dificuldade}")
            print(f"[DEBUG] frequencia_semanal: {frequencia_semanal}")
            print(f"[DEBUG] duracao_semanas: {duracao_semanas}")
            print("=" * 80)
            
            if treino_id:
                # ============== ATUALIZAR TREINO EXISTENTE ==============
                print(f"[DEBUG] Modo: ATUALIZAR treino {treino_id}")
                
                treino_existente = treino_personalizado_repo.obter_por_id(treino_id)
                
                if not treino_existente:
                    print(f"[ERRO] Treino {treino_id} não encontrado")
                    return RedirectResponse(
                        "/personal/treinos?erro=Treino não encontrado",
                        status_code=303
                    )
                
                print(f"[DEBUG] Treino encontrado: {treino_existente.nome}")
                
                # Atualizar campos (usando os campos corretos do banco)
                treino_existente.nome = nome
                treino_existente.objetivo = objetivo
                treino_existente.nivel_dificuldade = nivel_dificuldade
                treino_existente.dias_semana = frequencia_semanal  # ← Campo correto
                treino_existente.duracao_semanas = duracao_semanas
                treino_existente.descricao = descricao
                treino_existente.atualizado_em = datetime.now()
                
                print(f"[DEBUG] Chamando treino_personalizado_repo.alterar()...")
                sucesso = treino_personalizado_repo.alterar(treino_existente)
                
                if sucesso:
                    print(f"[SUCESSO] Treino {treino_id} atualizado com sucesso")
                    return RedirectResponse(
                        "/personal/treinos?sucesso=Treino atualizado com sucesso",
                        status_code=303
                    )
                else:
                    print(f"[ERRO] Falha ao atualizar treino {treino_id}")
                    return RedirectResponse(
                        "/personal/treinos?erro=Erro ao atualizar treino no banco",
                        status_code=303
                    )
            
            else:
                # ============== CRIAR NOVO TREINO ==============
                print(f"[DEBUG] Modo: CRIAR NOVO treino")
                
                # Validar que o aluno existe
                aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
                if not aluno_rel:
                    print(f"[ERRO] PersonalAluno {aluno_id} não encontrado")
                    return RedirectResponse(
                        "/personal/treinos?erro=Aluno não encontrado",
                        status_code=303
                    )
                
                print(f"[DEBUG] Criando objeto TreinoPersonalizado...")
                
                # Criar objeto (campos obrigatórios primeiro)
                novo_treino = TreinoPersonalizado(
                    id=0,
                    personal_aluno_id=aluno_id,
                    nome=nome,
                    objetivo=objetivo,
                    nivel_dificuldade=nivel_dificuldade
                )
                
                # Setar campos opcionais
                novo_treino.dias_semana = frequencia_semanal
                novo_treino.duracao_semanas = duracao_semanas
                novo_treino.descricao = descricao
                novo_treino.divisao_treino = None
                novo_treino.data_inicio = datetime.now()
                novo_treino.data_fim = None
                novo_treino.criado_em = datetime.now()
                novo_treino.atualizado_em = None
                
                print(f"[DEBUG] Objeto criado: {novo_treino}")
                print(f"[DEBUG] Chamando treino_personalizado_repo.inserir()...")
                
                treino_id_inserido = treino_personalizado_repo.inserir(novo_treino)
                
                if treino_id_inserido:
                    print(f"[SUCESSO] Treino criado com ID: {treino_id_inserido}")
                    return RedirectResponse(
                        "/personal/treinos?sucesso=Treino criado com sucesso",
                        status_code=303
                    )
                else:
                    print(f"[ERRO] Falha ao inserir treino")
                    return RedirectResponse(
                        "/personal/treinos?erro=Erro ao criar treino no banco",
                        status_code=303
                    )
                    
        except Exception as e:
            print(f"[ERRO CRÍTICO] Ao salvar treino: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return RedirectResponse(
                f"/personal/treinos?erro=Erro: {str(e)}",
                status_code=303
            )


    # ============================================
    # ROTA: EXCLUIR TREINO
    # ============================================
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
            
            treino_personalizado_repo.excluir(treino_id)
            
            return RedirectResponse("/personal/treinos?sucesso=Treino excluído com sucesso", status_code=303)
        except Exception as e:
            print(f"[ERRO] Excluir treino: {str(e)}")
            return RedirectResponse("/personal/treinos?erro=Erro ao excluir treino", status_code=303)

    # =================== GESTÃO DE AVALIAÇÕES FÍSICAS ===================


# =================== GESTÃO DE AVALIAÇÕES FÍSICAS ===================

# ============================================
# ROTA: LISTAR AVALIAÇÕES (já existe, mantém)
# ============================================
    @app.get("/personal/avaliacoes")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Lista todas as avaliações físicas dos alunos do personal"""
        from datetime import datetime

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

            # Formatar datas após montar todas_avaliacoes
            for aval in todas_avaliacoes:
                data = aval.get("data_avaliacao")
                if data:
                    if isinstance(data, str):
                        try:
                            data = datetime.fromisoformat(data)
                        except ValueError:
                            pass
                    aval["data_formatada"] = data.strftime('%d/%m/%Y') if hasattr(data, "strftime") else str(data)
                else:
                    aval["data_formatada"] = "-"

            # Ordenar por data (mais recente primeiro)
            todas_avaliacoes.sort(key=lambda x: x['data_avaliacao'], reverse=True)

            return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacoes": todas_avaliacoes
            })

        except Exception as e:
            print(f"[ERRO] Listar avaliações: {str(e)}")
            import traceback
            traceback.print_exc()
            return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacoes": [],
                "erro": "Erro ao carregar avaliações"
            })


    # ============================================
    # ROTA: NOVA AVALIAÇÃO (GET) - NOVA
    # ============================================
    @app.get("/personal/avaliacoes/nova")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_nova_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Formulário para criar nova avaliação física"""
        try:
            # Buscar personal
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/avaliacoes?erro=Personal não encontrado", status_code=303)
            
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
            
            # Verificar se há query param 'aluno' (vindo de detalhes do aluno)
            aluno_selecionado_id = request.query_params.get('aluno')
            
            return templates.TemplateResponse("personal/avaliacoes/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacao": None,
                "alunos_disponiveis": alunos_disponiveis,
                "aluno_selecionado_id": aluno_selecionado_id,
                "titulo": "Nova Avaliação Física",
                "acao": "/personal/avaliacoes/salvar"
            })
            
        except Exception as e:
            print(f"[ERRO] Nova avaliação GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/avaliacoes?erro=Erro ao carregar formulário", status_code=303)


    # ============================================
    # ROTA: SALVAR AVALIAÇÃO (POST) - NOVA
    # ============================================
    @app.post("/personal/avaliacoes/salvar")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_salvar(
        request: Request,
        usuario_logado: dict = Depends(obter_usuario_logado),
        avaliacao_id: Optional[int] = Form(None),
        aluno_id: int = Form(...),  # ID do PersonalAluno
        data_avaliacao: str = Form(...),
        peso: Optional[float] = Form(None),
        altura: Optional[float] = Form(None),
        percentual_gordura: Optional[float] = Form(None),
        massa_magra: Optional[float] = Form(None),
        circunferencias: Optional[str] = Form(None),
        observacoes: Optional[str] = Form(None),
        proxima_avaliacao: Optional[str] = Form(None)
    ):
        """Salvar avaliação física (criar ou atualizar)"""
        try:
            print(f"[DEBUG] Salvando avaliação física...")
            print(f"[DEBUG] avaliacao_id: {avaliacao_id}")
            print(f"[DEBUG] aluno_id: {aluno_id}")
            print(f"[DEBUG] peso: {peso}, altura: {altura}")
            
            # Converter data_avaliacao de string para datetime
            try:
                data_aval_dt = datetime.strptime(data_avaliacao, '%Y-%m-%d')
            except ValueError:
                return RedirectResponse(
                    "/personal/avaliacoes?erro=Data de avaliação inválida",
                    status_code=303
                )
            
            # Calcular IMC se peso e altura foram fornecidos
            imc = None
            if peso and altura and altura > 0:
                imc = peso / (altura * altura)
                print(f"[DEBUG] IMC calculado: {imc}")
            
            # Converter proxima_avaliacao se fornecida
            proxima_aval_dt = None
            if proxima_avaliacao:
                try:
                    proxima_aval_dt = datetime.strptime(proxima_avaliacao, '%Y-%m-%d')
                except ValueError:
                    proxima_aval_dt = None
            
            if avaliacao_id:
                # ============== ATUALIZAR AVALIAÇÃO EXISTENTE ==============
                print(f"[DEBUG] Modo: ATUALIZAR avaliação {avaliacao_id}")
                
                avaliacao_existente = avaliacao_fisica_repo.obter_por_id(avaliacao_id)
                
                if not avaliacao_existente:
                    return RedirectResponse(
                        "/personal/avaliacoes?erro=Avaliação não encontrada",
                        status_code=303
                    )
                
                # Atualizar campos
                avaliacao_existente.data_avaliacao = data_aval_dt
                avaliacao_existente.peso = peso
                avaliacao_existente.altura = altura
                avaliacao_existente.imc = imc
                avaliacao_existente.percentual_gordura = percentual_gordura
                avaliacao_existente.massa_magra = massa_magra
                avaliacao_existente.circunferencias = circunferencias
                avaliacao_existente.observacoes = observacoes
                avaliacao_existente.proxima_avaliacao = proxima_aval_dt
                
                sucesso = avaliacao_fisica_repo.alterar(avaliacao_existente)
                
                if sucesso:
                    print(f"[SUCESSO] Avaliação {avaliacao_id} atualizada")
                    return RedirectResponse(
                        "/personal/avaliacoes?sucesso=Avaliação atualizada com sucesso",
                        status_code=303
                    )
                else:
                    return RedirectResponse(
                        "/personal/avaliacoes?erro=Erro ao atualizar avaliação",
                        status_code=303
                    )
            
            else:
                # ============== CRIAR NOVA AVALIAÇÃO ==============
                print(f"[DEBUG] Modo: CRIAR nova avaliação")
                
                # Validar que o aluno existe
                aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
                if not aluno_rel:
                    return RedirectResponse(
                        "/personal/avaliacoes?erro=Aluno não encontrado",
                        status_code=303
                    )
                
                from data.model.avaliacao_fisica_model import AvaliacaoFisica
                
                # Criar nova avaliação
                nova_avaliacao = AvaliacaoFisica(
                    id=0,
                    personal_aluno_id=aluno_id,
                    data_avaliacao=data_aval_dt,
                    peso=peso,
                    altura=altura,
                    imc=imc,
                    percentual_gordura=percentual_gordura,
                    massa_magra=massa_magra,
                    circunferencias=circunferencias,
                    observacoes=observacoes,
                    proxima_avaliacao=proxima_aval_dt
                )
                
                print(f"[DEBUG] Objeto criado: {nova_avaliacao}")
                
                avaliacao_id_inserido = avaliacao_fisica_repo.inserir(nova_avaliacao)
                
                if avaliacao_id_inserido:
                    print(f"[SUCESSO] Avaliação criada com ID: {avaliacao_id_inserido}")
                    return RedirectResponse(
                        "/personal/avaliacoes?sucesso=Avaliação criada com sucesso",
                        status_code=303
                    )
                else:
                    return RedirectResponse(
                        "/personal/avaliacoes?erro=Erro ao criar avaliação",
                        status_code=303
                    )
                    
        except Exception as e:
            print(f"[ERRO CRÍTICO] Ao salvar avaliação: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return RedirectResponse(
                f"/personal/avaliacoes?erro=Erro: {str(e)}",
                status_code=303
            )


    # ============================================
    # ROTA: VER DETALHES DA AVALIAÇÃO - NOVA
    # ============================================
    @app.get("/personal/avaliacoes/{avaliacao_id}")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_detalhes(
        request: Request,
        avaliacao_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Ver detalhes de uma avaliação física"""
        try:
            avaliacao = avaliacao_fisica_repo.obter_por_id(avaliacao_id)
            
            if not avaliacao:
                return RedirectResponse("/personal/avaliacoes?erro=Avaliação não encontrada", status_code=303)
            
            # Buscar dados do aluno
            aluno_rel = personal_aluno_repo.obter_por_id(avaliacao.personal_aluno_id)
            aluno_nome = "N/A"
            
            if aluno_rel:
                cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
                if cliente:
                    usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                    if usuario_aluno:
                        aluno_nome = usuario_aluno.nome
            
            return templates.TemplateResponse("personal/avaliacoes/detalhes.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacao": avaliacao,
                "aluno_nome": aluno_nome
            })
            
        except Exception as e:
            print(f"[ERRO] Detalhes avaliação: {str(e)}")
            return RedirectResponse("/personal/avaliacoes?erro=Erro ao carregar detalhes", status_code=303)


    # ============================================
    # ROTA: EDITAR AVALIAÇÃO (GET) - NOVA
    # ============================================
    @app.get("/personal/avaliacoes/{avaliacao_id}/editar")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_editar_get(
        request: Request,
        avaliacao_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Formulário para editar avaliação física"""
        try:
            avaliacao = avaliacao_fisica_repo.obter_por_id(avaliacao_id)
            
            if not avaliacao:
                return RedirectResponse("/personal/avaliacoes?erro=Avaliação não encontrada", status_code=303)
            
            # Buscar personal e alunos
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/avaliacoes?erro=Personal não encontrado", status_code=303)
            
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
            
            def formatar_data_para_input(data):
                from datetime import datetime
                if isinstance(data, str):
                    try:
                        data = datetime.fromisoformat(data)
                    except ValueError:
                        return data  # Retorna a string original se falhar
                return data.strftime('%Y-%m-%d') if data else ''

            avaliacao_dict = {
            'id': avaliacao.id,
            'personal_aluno_id': avaliacao.personal_aluno_id,
            'data_avaliacao': formatar_data_para_input(avaliacao.data_avaliacao),
            'peso': avaliacao.peso,
            'altura': avaliacao.altura,
            'imc': avaliacao.imc,
            'percentual_gordura': avaliacao.percentual_gordura,
            'massa_magra': avaliacao.massa_magra,
            'circunferencias': avaliacao.circunferencias,
            'observacoes': avaliacao.observacoes,
            'proxima_avaliacao': formatar_data_para_input(avaliacao.proxima_avaliacao)
        }

            
            return templates.TemplateResponse("personal/avaliacoes/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacao": avaliacao_dict,
                "alunos_disponiveis": alunos_disponiveis,
                "titulo": "Editar Avaliação Física",
                "acao": "/personal/avaliacoes/salvar"
            })

        except Exception as e:
            print(f"[ERRO] Editar avaliação GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/avaliacoes?erro=Erro ao carregar avaliação", status_code=303)

    # ============================================
    # ROTA: EXCLUIR AVALIAÇÃO - NOVA
    # ============================================
    @app.post("/personal/avaliacoes/excluir/{avaliacao_id}")
    @requer_autenticacao(['profissional'])
    async def personal_avaliacoes_excluir(
        request: Request,
        avaliacao_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Excluir avaliação física"""
        try:
            avaliacao = avaliacao_fisica_repo.obter_por_id(avaliacao_id)
            
            if not avaliacao:
                return RedirectResponse("/personal/avaliacoes?erro=Avaliação não encontrada", status_code=303)
            
            avaliacao_fisica_repo.excluir(avaliacao_id)
            
            return RedirectResponse("/personal/avaliacoes?sucesso=Avaliação excluída com sucesso", status_code=303)
            
        except Exception as e:
            print(f"[ERRO] Excluir avaliação: {str(e)}")
            return RedirectResponse("/personal/avaliacoes?erro=Erro ao excluir avaliação", status_code=303)
        
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
   

    # =================== ROTAS ADICIONAIS DE PROGRESSOS ===================

    @app.get("/personal/progressos/novo")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        """Formulário para criar novo registro de progresso"""
        try:
            # Buscar personal
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/progressos?erro=Personal não encontrado", status_code=303)
            
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
            
            # Data de hoje para o formulário
            data_hoje = datetime.now().strftime('%Y-%m-%d')
            
            return templates.TemplateResponse("personal/progressos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "progresso": None,
                "alunos_disponiveis": alunos_disponiveis,
                "data_hoje": data_hoje
            })
        except Exception as e:
            print(f"[ERRO] Novo progresso GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/progressos?erro=Erro ao carregar formulário", status_code=303)


    @app.post("/personal/progressos/salvar")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_salvar(
        request: Request,
        progresso_id: Optional[int] = Form(None),
        aluno_id: int = Form(...),
        data_registro: str = Form(...),
        peso: Optional[float] = Form(None),
        humor: Optional[str] = Form(None),
        energia: Optional[int] = Form(None),
        observacoes: Optional[str] = Form(None),
        circunferencia_cintura: Optional[float] = Form(None),
        circunferencia_quadril: Optional[float] = Form(None),
        circunferencia_braco: Optional[float] = Form(None),
        circunferencia_perna: Optional[float] = Form(None),
        circunferencia_peito: Optional[float] = Form(None),
        circunferencia_abdomem: Optional[float] = Form(None),
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Salvar progresso (criar ou atualizar)"""
        try:
            # Converter data string para datetime
            data_registro_dt = datetime.strptime(data_registro, '%Y-%m-%d')
            
            # Validar se é um aluno do personal logado
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/progressos?erro=Personal não encontrado", status_code=303)
            
            # Validar propriedade do aluno
            aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/progressos?erro=Aluno não encontrado ou acesso negado", status_code=303)
            
            if progresso_id:
                # Atualizar progresso existente
                progresso = progresso_aluno_repo.obter_por_id(progresso_id)
                if progresso:
                    progresso.data_registro = data_registro_dt
                    progresso.peso = peso
                    progresso.humor = humor if humor else None
                    progresso.energia = energia if energia is not None else None
                    progresso.observacoes = observacoes if observacoes else None
                    
                    # Medidas corporais (verificar se os atributos existem)
                    if hasattr(progresso, 'circunferencia_cintura'):
                        progresso.circunferencia_cintura = circunferencia_cintura
                    if hasattr(progresso, 'circunferencia_quadril'):
                        progresso.circunferencia_quadril = circunferencia_quadril
                    if hasattr(progresso, 'circunferencia_braco'):
                        progresso.circunferencia_braco = circunferencia_braco
                    if hasattr(progresso, 'circunferencia_perna'):
                        progresso.circunferencia_perna = circunferencia_perna
                    if hasattr(progresso, 'circunferencia_peito'):
                        progresso.circunferencia_peito = circunferencia_peito
                    if hasattr(progresso, 'circunferencia_abdomem'):
                        progresso.circunferencia_abdomem = circunferencia_abdomem
                    
                    progresso_aluno_repo.alterar(progresso)
                    return RedirectResponse("/personal/progressos?sucesso=Progresso atualizado com sucesso", status_code=303)
            else:
                # Criar novo progresso
                from data.model.progresso_aluno_model import ProgressoAluno
                
                novo_progresso = ProgressoAluno(
                    id=0,
                    personal_aluno_id=aluno_id,
                    data_registro=data_registro_dt
                )
                
                # Setar atributos opcionais
                novo_progresso.peso = peso
                novo_progresso.humor = humor if humor else None
                novo_progresso.energia = energia if energia is not None else None
                novo_progresso.observacoes = observacoes if observacoes else None
                
                # Medidas corporais (verificar se os atributos existem)
                if hasattr(novo_progresso, 'circunferencia_cintura'):
                    novo_progresso.circunferencia_cintura = circunferencia_cintura
                if hasattr(novo_progresso, 'circunferencia_quadril'):
                    novo_progresso.circunferencia_quadril = circunferencia_quadril
                if hasattr(novo_progresso, 'circunferencia_braco'):
                    novo_progresso.circunferencia_braco = circunferencia_braco
                if hasattr(novo_progresso, 'circunferencia_perna'):
                    novo_progresso.circunferencia_perna = circunferencia_perna
                if hasattr(novo_progresso, 'circunferencia_peito'):
                    novo_progresso.circunferencia_peito = circunferencia_peito
                if hasattr(novo_progresso, 'circunferencia_abdomem'):
                    novo_progresso.circunferencia_abdomem = circunferencia_abdomem
                
                progresso_aluno_repo.inserir(novo_progresso)
                return RedirectResponse("/personal/progressos?sucesso=Progresso registrado com sucesso", status_code=303)
                
        except Exception as e:
            print(f"[ERRO] Salvar progresso: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/progressos?erro=Erro ao salvar progresso", status_code=303)


    @app.get("/personal/progressos/{progresso_id}")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_detalhes(
        request: Request,
        progresso_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Ver detalhes do progresso"""
        try:
            # Validar propriedade
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/progressos?erro=Personal não encontrado", status_code=303)
            
            # Buscar progresso
            progresso = progresso_aluno_repo.obter_por_id(progresso_id)
            if not progresso:
                return RedirectResponse("/personal/progressos?erro=Progresso não encontrado", status_code=303)
            
            # Buscar dados do aluno e validar propriedade
            aluno_rel = personal_aluno_repo.obter_por_id(progresso.personal_aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/progressos?erro=Acesso negado", status_code=303)
            
            # Buscar nome do aluno
            cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
            usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
            aluno_nome = usuario_aluno.nome if usuario_aluno else 'N/A'
            
            # CORREÇÃO: Converter data_registro para datetime se vier como string
            data_registro_convertida = progresso.data_registro
            if isinstance(progresso.data_registro, str):
                try:
                    data_registro_convertida = datetime.fromisoformat(progresso.data_registro.split('.')[0])
                except (ValueError, AttributeError):
                    try:
                        data_registro_convertida = datetime.strptime(progresso.data_registro, '%d/%m/%Y')
                    except ValueError:
                        data_registro_convertida = datetime.now()
            
            # Buscar último progresso anterior (para comparação)
            todos_progressos = progresso_aluno_repo.obter_por_aluno(progresso.personal_aluno_id)
            
            # Converter datas de todos os progressos
            for prog in todos_progressos:
                if isinstance(prog.data_registro, str):
                    try:
                        prog.data_registro = datetime.fromisoformat(prog.data_registro.split('.')[0])
                    except (ValueError, AttributeError):
                        try:
                            prog.data_registro = datetime.strptime(prog.data_registro, '%d/%m/%Y')
                        except ValueError:
                            prog.data_registro = datetime.now()
            
            todos_progressos.sort(key=lambda x: x.data_registro, reverse=True)
            
            ultimo_progresso = None
            for prog in todos_progressos:
                if prog.id != progresso_id and prog.data_registro < data_registro_convertida:
                    ultimo_progresso = prog
                    break
            
            # Calcular estatísticas
            total_registros = len(todos_progressos)
            primeiro_registro = todos_progressos[-1].data_registro if todos_progressos else None
            
            dias_acompanhamento = 0
            if primeiro_registro:
                dias_acompanhamento = (datetime.now() - primeiro_registro).days
            
            # Organizar medidas (se houver)
            medidas = {}
            if hasattr(progresso, 'circunferencia_cintura') and progresso.circunferencia_cintura:
                medidas['Cintura'] = progresso.circunferencia_cintura
            if hasattr(progresso, 'circunferencia_quadril') and progresso.circunferencia_quadril:
                medidas['Quadril'] = progresso.circunferencia_quadril
            if hasattr(progresso, 'circunferencia_braco') and progresso.circunferencia_braco:
                medidas['Braço'] = progresso.circunferencia_braco
            if hasattr(progresso, 'circunferencia_perna') and progresso.circunferencia_perna:
                medidas['Perna'] = progresso.circunferencia_perna
            if hasattr(progresso, 'circunferencia_peito') and progresso.circunferencia_peito:
                medidas['Peito'] = progresso.circunferencia_peito
            if hasattr(progresso, 'circunferencia_abdomem') and progresso.circunferencia_abdomem:
                medidas['Abdômen'] = progresso.circunferencia_abdomem
            
            # Criar objeto progresso com dados formatados
            progresso_dict = {
                'id': progresso.id,
                'aluno_id': progresso.personal_aluno_id,
                'aluno_nome': aluno_nome,
                'data_registro': data_registro_convertida,
                'peso': progresso.peso if hasattr(progresso, 'peso') else None,
                'humor': progresso.humor if hasattr(progresso, 'humor') else None,
                'energia': progresso.energia if hasattr(progresso, 'energia') else None,
                'observacoes': progresso.observacoes if hasattr(progresso, 'observacoes') else None,
                'medidas': medidas if medidas else None
            }
            
            return templates.TemplateResponse("personal/progressos/detalhes.html", {
                "request": request,
                "usuario": usuario_logado,
                "progresso": type('obj', (object,), progresso_dict),
                "ultimo_progresso": ultimo_progresso,
                "total_registros": total_registros,
                "primeiro_registro": primeiro_registro,
                "dias_acompanhamento": dias_acompanhamento
            })
            
        except Exception as e:
            print(f"[ERRO] Detalhes progresso: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/progressos?erro=Erro ao carregar detalhes", status_code=303)


    @app.get("/personal/progressos/{progresso_id}/editar")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_editar_get(
        request: Request,
        progresso_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Formulário para editar progresso"""
        try:
            # Validar propriedade
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/progressos?erro=Personal não encontrado", status_code=303)
            
            progresso = progresso_aluno_repo.obter_por_id(progresso_id)
            if not progresso:
                return RedirectResponse("/personal/progressos?erro=Progresso não encontrado", status_code=303)
            
            # Validar propriedade do aluno
            aluno_rel = personal_aluno_repo.obter_por_id(progresso.personal_aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/progressos?erro=Acesso negado", status_code=303)
            
            # Buscar todos os alunos (para o select, mesmo que desabilitado)
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
            
            # Buscar nome do aluno atual
            cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
            usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
            
            # CORREÇÃO: Converter data_registro para datetime se vier como string
            data_registro_convertida = progresso.data_registro
            if isinstance(progresso.data_registro, str):
                try:
                    data_registro_convertida = datetime.fromisoformat(progresso.data_registro.split('.')[0])
                except (ValueError, AttributeError):
                    try:
                        data_registro_convertida = datetime.strptime(progresso.data_registro, '%d/%m/%Y')
                    except ValueError:
                        data_registro_convertida = datetime.now()
            
            # Criar objeto progresso com dados completos
            progresso_dict = {
                'id': progresso.id,
                'aluno_id': progresso.personal_aluno_id,
                'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                'data_registro': data_registro_convertida,
                'peso': progresso.peso if hasattr(progresso, 'peso') else None,
                'humor': progresso.humor if hasattr(progresso, 'humor') else None,
                'energia': progresso.energia if hasattr(progresso, 'energia') else None,
                'observacoes': progresso.observacoes if hasattr(progresso, 'observacoes') else None,
                'circunferencia_cintura': progresso.circunferencia_cintura if hasattr(progresso, 'circunferencia_cintura') else None,
                'circunferencia_quadril': progresso.circunferencia_quadril if hasattr(progresso, 'circunferencia_quadril') else None,
                'circunferencia_braco': progresso.circunferencia_braco if hasattr(progresso, 'circunferencia_braco') else None,
                'circunferencia_perna': progresso.circunferencia_perna if hasattr(progresso, 'circunferencia_perna') else None,
                'circunferencia_peito': progresso.circunferencia_peito if hasattr(progresso, 'circunferencia_peito') else None,
                'circunferencia_abdomem': progresso.circunferencia_abdomem if hasattr(progresso, 'circunferencia_abdomem') else None
            }
            
            return templates.TemplateResponse("personal/progressos/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "progresso": type('obj', (object,), progresso_dict),
                "alunos_disponiveis": alunos_disponiveis,
                "data_hoje": None
            })
            
        except Exception as e:
            print(f"[ERRO] Editar progresso GET: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/progressos?erro=Erro ao carregar progresso", status_code=303)


    @app.post("/personal/progressos/excluir/{progresso_id}")
    @requer_autenticacao(['profissional'])
    async def personal_progressos_excluir(
        request: Request,
        progresso_id: int,
        usuario_logado: dict = Depends(obter_usuario_logado)
    ):
        """Excluir progresso"""
        try:
            # Validar propriedade
            profissional = profissional_repo.obter_por_id(usuario_logado['id'])
            personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
            
            if not personal:
                return RedirectResponse("/personal/progressos?erro=Personal não encontrado", status_code=303)
            
            progresso = progresso_aluno_repo.obter_por_id(progresso_id)
            if not progresso:
                return RedirectResponse("/personal/progressos?erro=Progresso não encontrado", status_code=303)
            
            # Validar propriedade do aluno
            aluno_rel = personal_aluno_repo.obter_por_id(progresso.personal_aluno_id)
            if not aluno_rel or aluno_rel.personal_id != personal.id:
                return RedirectResponse("/personal/progressos?erro=Acesso negado", status_code=303)
            
            # Excluir progresso
            progresso_aluno_repo.excluir(progresso_id)
            
            return RedirectResponse("/personal/progressos?sucesso=Progresso excluído com sucesso", status_code=303)
        except Exception as e:
            print(f"[ERRO] Excluir progresso: {str(e)}")
            import traceback
            traceback.print_exc()
            return RedirectResponse("/personal/progressos?erro=Erro ao excluir progresso", status_code=303)
        
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
