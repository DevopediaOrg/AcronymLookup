CREATE TABLE acronyms (
    aid INTEGER PRIMARY KEY AUTOINCREMENT,
    acronym VARCHAR(20) NOT NULL
);

CREATE TABLE definitions (
    did INTEGER PRIMARY KEY AUTOINCREMENT,
    definition VARCHAR(300) NOT NULL,
    context VARCHAR(5000) NOT NULL,
    url VARCHAR(300) NOT NULL
);

CREATE TABLE acronyms_definitions (
    aid INTEGER NOT NULL,
    did INTEGER NOT NULL
);

CREATE TABLE true_definitions (
    acronym VARCHAR(20) NOT NULL,
    true_definition VARCHAR(300) NOT NULL,
    url VARCHAR(300) NOT NULL
);

