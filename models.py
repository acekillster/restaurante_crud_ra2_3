from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Perfil(db.Model):
    __tablename__ = 'perfil'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)
    perfil = db.relationship('Perfil')

class ItemCardapio(db.Model):
    __tablename__ = 'item_cardapio'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    disponivel = db.Column(db.Boolean, default=True)

class Comanda(db.Model):
    __tablename__ = 'comanda'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='aberta')
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    fechado_em = db.Column(db.DateTime)
    pago_em = db.Column(db.DateTime)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fechado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    pago_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    itens = db.relationship('ItemComanda', backref='comanda', cascade='all, delete-orphan')


class ItemComanda(db.Model):
    __tablename__ = 'item_comanda'
    id = db.Column(db.Integer, primary_key=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item_cardapio.id'))
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)


class Pagamento(db.Model):
    __tablename__ = 'pagamento'
    id = db.Column(db.Integer, primary_key=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'))
    forma = db.Column(db.String(50))
    valor_recebido = db.Column(db.Numeric(10, 2))
    troco = db.Column(db.Numeric(10, 2))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    confirmado = db.Column(db.Boolean, default=False)
    confirmado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'))
