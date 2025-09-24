CRIAR_TABELA_PROFISSIONAL = """
CREATE TABLE IF NOT EXISTS profissional (
    id INTEGER PRIMARY KEY,
    especialidade TEXT NOT NULL,
    registro_profissional TEXT,
    status TEXT DEFAULT 'pendente',
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_aprovacao TIMESTAMP,
    aprovado_por INTEGER,
    cpf_cnpj TEXT,
    foto_registro TEXT,
    FOREIGN KEY (id) REFERENCES usuario(id),
    FOREIGN KEY (aprovado_por) REFERENCES usuario(id)
);
"""

INSERIR_PROFISSIONAL = """
INSERT INTO profissional (
    id, especialidade, registro_profissional, status, 
    data_solicitacao, data_aprovacao, aprovado_por, cpf_cnpj, foto_registro
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

ALTERAR_PROFISSIONAL = """
UPDATE profissional
SET especialidade = ?,
    registro_profissional = ?,
    status = ?,
    data_solicitacao = ?,
    data_aprovacao = ?,
    aprovado_por = ?
WHERE id = ?;
"""

EXCLUIR_PROFISSIONAL = """
DELETE FROM profissional WHERE id = ?;
"""

OBTER_POR_ID_PROFISSIONAL = """
SELECT 
    p.id, 
    p.especialidade, 
    p.registro_profissional,
    p.status, 
    p.data_solicitacao,
    p.data_aprovacao,
    p.aprovado_por,
    u.nome, 
    u.email, 
    u.senha
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
WHERE p.id = ?;
"""

OBTER_TODOS_PROFISSIONAL = """
SELECT 
    p.id, 
    p.especialidade, 
    p.registro_profissional,
    p.status,
    p.data_solicitacao,
    p.data_aprovacao,
    p.aprovado_por,
    u.nome, 
    u.email, 
    u.senha
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
ORDER BY u.nome;
"""

OBTER_PENDENTES = """
SELECT 
    p.id, 
    p.especialidade, 
    p.registro_profissional, 
    p.status, 
    p.data_solicitacao,
    u.nome, 
    u.email
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
WHERE p.status = 'pendente'
ORDER BY p.data_solicitacao DESC;
"""

OBTER_TODOS_COM_STATUS = """
SELECT 
    p.id, 
    p.especialidade, 
    p.registro_profissional, 
    p.status, 
    p.data_solicitacao, 
    p.data_aprovacao,
    u.nome, 
    u.email,
    admin.nome AS aprovado_por_nome
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
LEFT JOIN usuario admin ON p.aprovado_por = admin.id
ORDER BY u.nome;
"""

APROVAR_PROFISSIONAL = """
UPDATE profissional 
SET status = 'aprovado', 
    data_aprovacao = CURRENT_TIMESTAMP, 
    aprovado_por = ?
WHERE id = ?;
"""

REJEITAR_PROFISSIONAL = """
UPDATE profissional 
SET status = 'rejeitado', 
    data_aprovacao = CURRENT_TIMESTAMP, 
    aprovado_por = ?
WHERE id = ?;
"""
