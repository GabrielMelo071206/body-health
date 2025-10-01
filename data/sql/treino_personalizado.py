CRIAR_TABELA_TREINO_PERSONALIZADO = """
CREATE TABLE IF NOT EXISTS treino_personalizado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_aluno_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    descricao TEXT,
    objetivo TEXT NOT NULL,
    nivel_dificuldade TEXT NOT NULL,
    duracao_semanas INTEGER,
    dias_semana INTEGER DEFAULT 3,
    divisao_treino TEXT,
    observacoes TEXT,
    status TEXT DEFAULT 'ativo',
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP,
    FOREIGN KEY (personal_aluno_id) REFERENCES personal_aluno(id) ON DELETE CASCADE
);
"""

INSERIR_TREINO_PERSONALIZADO = """
INSERT INTO treino_personalizado (
    personal_aluno_id, nome, descricao, objetivo, nivel_dificuldade,
    duracao_semanas, dias_semana, divisao_treino, observacoes,
    status, data_inicio, data_fim, criado_em, atualizado_em
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_TREINO_PERSONALIZADO = """
UPDATE treino_personalizado
SET personal_aluno_id=?, nome=?, descricao=?, objetivo=?, nivel_dificuldade=?,
    duracao_semanas=?, dias_semana=?, divisao_treino=?, observacoes=?,
    status=?, data_inicio=?, data_fim=?, atualizado_em=?
WHERE id=?
"""

EXCLUIR_TREINO_PERSONALIZADO = """
DELETE FROM treino_personalizado WHERE id=?
"""

OBTER_POR_ID_TREINO_PERSONALIZADO = """
SELECT tp.*, u.nome AS aluno_nome
FROM treino_personalizado tp
INNER JOIN personal_aluno pa ON tp.personal_aluno_id = pa.id
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
WHERE tp.id=?
"""

OBTER_TODOS_TREINO_PERSONALIZADO = """
SELECT tp.*, u.nome AS aluno_nome
FROM treino_personalizado tp
INNER JOIN personal_aluno pa ON tp.personal_aluno_id = pa.id
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
ORDER BY tp.criado_em DESC
"""

OBTER_POR_ALUNO = """
SELECT * FROM treino_personalizado
WHERE personal_aluno_id=? AND status='ativo'
ORDER BY criado_em DESC
"""