DROP DATABASE IF EXISTS restaurante_banco_ex_pietro;
CREATE DATABASE restaurante_banco_ex_pietro;
USE restaurante_banco_ex_pietro;

CREATE TABLE perfil (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(20) NOT NULL
);

CREATE TABLE usuario (
  id INT AUTO_INCREMENT PRIMARY KEY,
  login VARCHAR(80) NOT NULL UNIQUE,
  senha VARCHAR(200) NOT NULL,
  perfil_id INT NOT NULL,
  FOREIGN KEY (perfil_id) REFERENCES perfil(id)
);

CREATE TABLE item_cardapio (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  preco DECIMAL(10,2) NOT NULL,
  disponivel BOOLEAN DEFAULT TRUE
);

CREATE TABLE comanda (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo INT NOT NULL UNIQUE,
  estado VARCHAR(20) NOT NULL DEFAULT 'aberta',
  cliente_id INT,
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  fechado_em DATETIME,
  pago_em DATETIME,
  criado_por INT,
  fechado_por INT,
  pago_por INT,
  FOREIGN KEY (cliente_id) REFERENCES usuario(id),
  FOREIGN KEY (criado_por) REFERENCES usuario(id),
  FOREIGN KEY (fechado_por) REFERENCES usuario(id),
  FOREIGN KEY (pago_por) REFERENCES usuario(id)
);

CREATE TABLE item_comanda (
  id INT AUTO_INCREMENT PRIMARY KEY,
  comanda_id INT,
  item_id INT,
  nome VARCHAR(120) NOT NULL,
  preco DECIMAL(10,2) NOT NULL,
  quantidade INT NOT NULL,
  FOREIGN KEY (comanda_id) REFERENCES comanda(id) ON DELETE CASCADE,
  FOREIGN KEY (item_id) REFERENCES item_cardapio(id)
);

CREATE TABLE pagamento (
  id INT AUTO_INCREMENT PRIMARY KEY,
  comanda_id INT,
  forma VARCHAR(50),
  valor_recebido DECIMAL(10,2),
  troco DECIMAL(10,2),
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  usuario_id INT,
  confirmado BOOLEAN DEFAULT FALSE,
  confirmado_por INT,
  FOREIGN KEY (comanda_id) REFERENCES comanda(id),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id),
  FOREIGN KEY (confirmado_por) REFERENCES usuario(id)
);

INSERT INTO perfil (nome) VALUES ('Cliente'), ('Atendente'), ('Administrador');

INSERT INTO usuario (login, senha, perfil_id) VALUES
('cliente1', '123', 1),
('atendente1', '123', 2),
('admin', '123', 3);

INSERT INTO item_cardapio (nome, preco, disponivel) VALUES
('Coxinha', 6.50, TRUE),
('Refrigerante', 5.00, TRUE),
('Prato Executivo', 18.90, TRUE);
