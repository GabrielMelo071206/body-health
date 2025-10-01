CRIAR_TABELA_PERSONAL_ALUNO = """
CREATE TABLE IF NOT EXISTS personal_aluno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_id INTEGER NOT NULL,
    aluno_id INTEGER NOT NULL,
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    status TEXT DEFAULT 'ativo',
    objetivo TEXT,
    observacoes TEXT,
    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE,
    FOREIGN KEY (aluno_id) REFERENCES cliente(id) ON DELETE CASCADE
);
"""

INSERIR_PERSONAL_ALUNO = """
INSERT INTO personal_aluno (
    personal_id, aluno_id, data_inicio, data_fim, 
    status, objetivo, observacoes
)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_PERSONAL_ALUNO = """
UPDATE personal_aluno
SET personal_id=?, aluno_id=?, data_inicio=?, data_fim=?,
    status=?, objetivo=?, observacoes=?
WHERE id=?
"""

EXCLUIR_PERSONAL_ALUNO = """
DELETE FROM personal_aluno WHERE id=?
"""

OBTER_POR_ID_PERSONAL_ALUNO = """
SELECT pa.*, u.nome AS aluno_nome, u.email AS aluno_email
FROM personal_aluno pa
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
WHERE pa.id=?
"""

OBTER_TODOS_PERSONAL_ALUNO = """
SELECT pa.*, u.nome AS aluno_nome, u.email AS aluno_email
FROM personal_aluno pa
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
ORDER BY pa.data_inicio DESC
"""

OBTER_ALUNOS_POR_PERSONAL = """
SELECT pa.*, u.nome AS aluno_nome, u.email AS aluno_email
FROM personal_aluno pa
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
WHERE pa.personal_id=? AND pa.status='ativo'
ORDER BY u.nome
"""
