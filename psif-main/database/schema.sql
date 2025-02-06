CREATE TABLE planilhas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    objetivo REAL NOT NULL,
    data_ini DATE NOT NULL,
    data_fim DATE NOT NULL,

    FOREIGN KEY (id_usuario) REFERENCES usuarios
);

CREATE TABLE lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_planilha INTEGER NOT NULL,
    id_participante INTEGER NOT NULL,
    data DATE NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,

    FOREIGN KEY (id_planilha) REFERENCES planilhas,
    FOREIGN KEY (id_participante) REFERENCES participantes
);

CREATE TABLE participantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_planilha INTEGER NOT NULL,
    nome TEXT NOT NULL,
    contato TEXT NOT NULL,

    FOREIGN KEY (id_planilha) REFERENCES planilhas
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL
);


CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    contato TEXT NOT NULL,
    preco REAL NOT NULL,
    data_horario TEXT NOT NULL,
    local TEXT NOT NULL,
    id_usuario INTEGER NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios (id) ON DELETE CASCADE
 )
