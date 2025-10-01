CRIAR_TABELA_EXERCICIO_SESSAO = """
CREATE TABLE IF NOT EXISTS exercicio_sessao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id INTEGER NOT NULL,
    exercicio_id INTEGER NOT NULL,
    ordem INTEGER NOT NULL,
    series INTEGER NOT NULL,
    repeticoes TEXT NOT NULL,
    carga TEXT,
    descanso TEXT,
    tecnica TEXT,
    observacoes TEXT,
    video_demonstracao TEXT,
    FOREIGN KEY (sessao_id) REFERENCES sessao_treino(id) ON DELETE CASCADE,
    FOREIGN KEY (exercicio_id) REFERENCES exercicio(id) ON DELETE CASCADE
);
"""

INSERIR_EXERCICIO_SESSAO = """
INSERT INTO exercicio_sessao (
    sessao_id, exercicio_id, ordem, series, repeticoes,
    carga, descanso, tecnica, observacoes, video_demonstracao
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_EXERCICIO_SESSAO = """
UPDATE exercicio_sessao
SET sessao_id=?, exercicio_id=?, ordem=?, series=?, repeticoes=?,
    carga=?, descanso=?, tecnica=?, observacoes=?, video_demonstracao=?
WHERE id=?
"""

EXCLUIR_EXERCICIO_SESSAO = """
DELETE FROM exercicio_sessao WHERE id=?
"""

OBTER_POR_ID_EXERCICIO_SESSAO = """
SELECT es.*, e.nome AS exercicio_nome, e.grupo_muscular
FROM exercicio_sessao es
INNER JOIN exercicio e ON es.exercicio_id = e.id
WHERE es.id=?
"""

OBTER_TODOS_EXERCICIO_SESSAO = """
SELECT es.*, e.nome AS exercicio_nome, e.grupo_muscular
FROM exercicio_sessao es
INNER JOIN exercicio e ON es.exercicio_id = e.id
ORDER BY es.ordem
"""

OBTER_POR_SESSAO = """
SELECT es.*, e.nome AS exercicio_nome, e.grupo_muscular, e.descricao AS exercicio_descricao
FROM exercicio_sessao es
INNER JOIN exercicio e ON es.exercicio_id = e.id
WHERE es.sessao_id=?
ORDER BY es.ordem
"""
