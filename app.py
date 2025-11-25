from flask import Flask, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
from models import db, Usuario, Perfil, ItemCardapio, Comanda, ItemComanda, Pagamento
from auth import auth, login_manager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)
login_manager.init_app(app)
app.register_blueprint(auth)

##ve perfil do user e se ta logado ou nao
def usuario_tem_perfil(nome):
    return current_user.is_authenticated and current_user.perfil.nome == nome

#manda pras tela de acordo com o perfil do user
@app.route('/')
@login_required
def index():
    if usuario_tem_perfil('Cliente'):
        return redirect(url_for('ver_comanda_cliente'))
    if usuario_tem_perfil('Atendente'):
        return redirect(url_for('comandas_atendente'))
    if usuario_tem_perfil('Administrador'):
        return redirect(url_for('administracao'))
    return redirect(url_for('auth.login'))

# cliente
@app.route('/cliente/comanda')
@login_required
def ver_comanda_cliente(): #cardapio dispoinvel, comanda n paga, historico das paga e calculo de subtotal
    comanda = Comanda.query.filter_by(cliente_id=current_user.id).filter(Comanda.estado!='paga').order_by(Comanda.criado_em.desc()).first()
    itens = ItemCardapio.query.filter_by(disponivel=True).all()
    subtotal = 0
    if comanda:
        subtotal = sum(float(i.preco) * i.quantidade for i in comanda.itens)

    historico = Comanda.query.filter_by(cliente_id=current_user.id, estado='paga').order_by(Comanda.pago_em.desc()).all()
    usuarios_map = {u.id: u.login for u in Usuario.query.all()}
    historico_totais = {h.id: sum(float(i.preco) * i.quantidade for i in h.itens) for h in historico}

    return render_template('cardapio_cliente.html', itens=itens, comanda=comanda, subtotal=subtotal, historico=historico, usuarios_map=usuarios_map, historico_totais=historico_totais)

@app.route('/cliente/nova_comanda', methods=['POST'])
@login_required
def nova_comanda_cliente(): #criar comanda
    existe = Comanda.query.filter_by(cliente_id=current_user.id).filter(Comanda.estado!='paga').first()
    if existe:
        return redirect(url_for('ver_comanda_cliente'))
    max_codigo = db.session.query(func.max(Comanda.codigo)).scalar() or 0
    novo_codigo = max_codigo + 1
    comanda = Comanda(codigo=novo_codigo, estado='aberta', criado_em=datetime.utcnow(), criado_por=current_user.id, cliente_id=current_user.id)
    db.session.add(comanda)
    db.session.commit()
    return redirect(url_for('ver_comanda_cliente'))

@app.route('/cliente/adicionar_item', methods=['POST'])
@login_required
def adicionar_item_cliente(): #add
    comanda = Comanda.query.filter_by(cliente_id=current_user.id, estado='aberta').first()
    if not comanda:
        return redirect(url_for('ver_comanda_cliente'))
    item_id = int(request.form.get('item_id'))
    quantidade = int(request.form.get('quantidade'))
    item = ItemCardapio.query.get(item_id)
    if item and item.disponivel and quantidade>0:
        ic = ItemComanda(comanda_id=comanda.id, item_id=item.id, nome=item.nome, preco=item.preco, quantidade=quantidade)
        db.session.add(ic)
        db.session.commit()
    return redirect(url_for('ver_comanda_cliente'))

@app.route('/cliente/remover_item/<int:item_id>', methods=['POST'])
@login_required
def remover_item_cliente(item_id): #remove
    ic = ItemComanda.query.get(item_id)
    if ic and ic.comanda_id and ic.comanda.estado == 'aberta' and ic.comanda.cliente_id == current_user.id:
        db.session.delete(ic)
        db.session.commit()
    return redirect(url_for('ver_comanda_cliente'))

@app.route('/cliente/pagar', methods=['GET','POST'])
@login_required
def pagar_cliente(): #paga
    comanda = Comanda.query.filter_by(cliente_id=current_user.id, estado='fechada').first()
    if not comanda:
        return redirect(url_for('ver_comanda_cliente'))
    subtotal = sum(float(i.preco) * i.quantidade for i in comanda.itens) #calcula ototal
    erro = None
    if request.method == 'POST':
        forma = request.form.get('forma')
        valor_recebido = float(request.form.get('valor_recebido'))
        if valor_recebido < subtotal:
            erro = f"Valor insuficiente. Total: R$ {subtotal:.2f}"
        else:
            troco = valor_recebido - subtotal #troco calculado
            pagamento = Pagamento(
                comanda_id=comanda.id,
                forma=forma,
                valor_recebido=valor_recebido,
                troco=troco,
                usuario_id=current_user.id,
                confirmado=False
            )
            db.session.add(pagamento)
            db.session.commit()
            return redirect(url_for('ver_comanda_cliente'))
    return render_template('pagar_cliente.html', comanda=comanda, subtotal=subtotal, erro=erro)

# comanda geral
@app.route('/comanda/<int:codigo>', methods=['GET','POST'])
@login_required
def ver_comanda(codigo): #ve
    comanda = Comanda.query.filter_by(codigo=codigo).first()
    if not comanda:
        return redirect(url_for('index'))
    erro = None
    if request.method == 'POST':
        item_id = int(request.form.get('item_id'))
        quantidade = int(request.form.get('quantidade'))
        item = ItemCardapio.query.get(item_id)
        if not item or not item.disponivel:
            erro = 'Item indisponível'
        elif quantidade < 1:
            erro = 'Quantidade inválida'
        else:
            if usuario_tem_perfil('Atendente') and comanda.estado == 'aberta':
                ic = ItemComanda(comanda_id=comanda.id, item_id=item.id, nome=item.nome, preco=item.preco, quantidade=quantidade)
                db.session.add(ic)
                db.session.commit()
            elif usuario_tem_perfil('Administrador') and comanda.estado in ['aberta','fechada']:
                ic = ItemComanda(comanda_id=comanda.id, item_id=item.id, nome=item.nome, preco=item.preco, quantidade=quantidade)
                db.session.add(ic)
                db.session.commit()
            else:
                return redirect(url_for('index'))
    subtotal = sum(float(i.preco) * i.quantidade for i in comanda.itens)#calcula o total
    itens = ItemCardapio.query.filter_by(disponivel=True).all()
    usuarios_map = {u.id: u.login for u in Usuario.query.all()}
    return render_template('comanda.html', comanda=comanda, itens_cardapio=itens, subtotal=subtotal, erro=erro, usuarios_map=usuarios_map)

@app.route('/comanda/remover_item/<int:item_id>', methods=['POST'])
@login_required
def remover_item_comanda(item_id): #delet
    ic = ItemComanda.query.get(item_id)
    if not ic or not ic.comanda:
        return redirect(url_for('index'))
    comanda = ic.comanda
    
    if usuario_tem_perfil('Administrador') and comanda.estado == 'aberta':
        db.session.delete(ic)
        db.session.commit()
    elif usuario_tem_perfil('Atendente') and comanda.estado == 'aberta':
        db.session.delete(ic)
        db.session.commit()
    return redirect(url_for('ver_comanda', codigo=comanda.codigo))

@app.route('/recibo/<int:codigo>')
@login_required
def recibo(codigo): #fiscal
    comanda = Comanda.query.filter_by(codigo=codigo).first()
    if not comanda:
        return redirect(url_for('index'))

    # cliente so ve recibo do mesmo
    if usuario_tem_perfil('Cliente') and comanda.cliente_id != current_user.id:
        return redirect(url_for('index'))

    # admi e atendete ve recibo de paga
    if (usuario_tem_perfil('Atendente') or usuario_tem_perfil('Administrador')) and comanda.estado != 'paga':
        return redirect(url_for('index'))

    usuarios_map = {u.id: u.login for u in Usuario.query.all()}
    pagamento = Pagamento.query.filter_by(comanda_id=comanda.id, confirmado=True).order_by(Pagamento.criado_em.desc()).first()
    total = sum(float(i.preco) * i.quantidade for i in comanda.itens)

    return render_template('recibo.html', comanda=comanda, pagamento=pagamento, total=total, usuarios_map=usuarios_map)

# atendente
@app.route('/atendente/comandas')
@login_required
def comandas_atendente(): #ve as ccomanda
    if not usuario_tem_perfil('Atendente'):
        return redirect(url_for('index'))
    comandas = Comanda.query.order_by(Comanda.criado_em.desc()).all()
    clientes = Usuario.query.filter(Usuario.perfil_id==1).all()
    usuarios_map = {u.id: u.login for u in Usuario.query.all()}
    pagamentos_confirmados = {}
    for p in Pagamento.query.filter_by(confirmado=True).order_by(Pagamento.criado_em.desc()).all():
        if p.comanda_id not in pagamentos_confirmados:
            pagamentos_confirmados[p.comanda_id] = p
    totais = {c.id: sum(float(i.preco) * i.quantidade for i in c.itens) for c in comandas}
    return render_template('comandas_atendente.html', comandas=comandas, clientes=clientes, usuarios_map=usuarios_map, pagamentos_confirmados=pagamentos_confirmados, totais=totais)

@app.route('/atendente/nova_comanda', methods=['POST'])
@login_required
def nova_comanda_atendente(): #cria comadna pra cliente
    if not usuario_tem_perfil('Atendente'):
        return redirect(url_for('index'))
    cliente_id = int(request.form.get('cliente_id'))
    existe = Comanda.query.filter_by(cliente_id=cliente_id).filter(Comanda.estado!='paga').first()
    if existe:
        return redirect(url_for('comandas_atendente'))
    max_codigo = db.session.query(func.max(Comanda.codigo)).scalar() or 0
    novo_codigo = max_codigo + 1
    comanda = Comanda(codigo=novo_codigo, estado='aberta', criado_em=datetime.utcnow(), criado_por=current_user.id, cliente_id=cliente_id)
    db.session.add(comanda)
    db.session.commit()
    return redirect(url_for('comandas_atendente'))

@app.route('/atendente/fechar/<int:codigo>', methods=['POST'])
@login_required
def fechar_comanda_atendente(codigo): #fecha
    if not usuario_tem_perfil('Atendente'):
        return redirect(url_for('index'))
    comanda = Comanda.query.filter_by(codigo=codigo, estado='aberta').first()
    if comanda and len(comanda.itens) > 0:
        comanda.estado = 'fechada'
        comanda.fechado_em = datetime.utcnow()
        comanda.fechado_por = current_user.id
        db.session.commit()
    return redirect(url_for('comandas_atendente'))

# admin
@app.route('/administracao')
@login_required
def administracao(): #manda pro html do adm
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))
    usuarios = Usuario.query.all()
    usuarios_map = {u.id: u.login for u in usuarios}
    comandas = Comanda.query.order_by(Comanda.criado_em.desc()).all()
    itens = ItemCardapio.query.all()
    pagamentos_pendentes = Pagamento.query.filter_by(confirmado=False).all()
    pagamentos_confirmados = {}
    for p in Pagamento.query.filter_by(confirmado=True).order_by(Pagamento.criado_em.desc()).all():
        if p.comanda_id not in pagamentos_confirmados:
            pagamentos_confirmados[p.comanda_id] = p
    totais = {c.id: sum(float(i.preco) * i.quantidade for i in c.itens) for c in comandas}
    return render_template(
        'administracao.html',
        usuarios=usuarios,
        usuarios_map=usuarios_map,
        comandas=comandas,
        itens=itens,
        pagamentos=pagamentos_pendentes,
        pagamentos_confirmados=pagamentos_confirmados,
        totais=totais
    )

@app.route('/admin/criar_usuario', methods=['POST'])
@login_required
def criar_usuario(): #cria
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))
    login = request.form.get('login')
    senha = request.form.get('senha')
    perfil_id = int(request.form.get('perfil_id'))
    if login and senha and perfil_id:
        u = Usuario(login=login, senha=senha, perfil_id=perfil_id)
        db.session.add(u)
        db.session.commit()
    return redirect(url_for('administracao'))

@app.route('/admin/deletar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def deletar_usuario(usuario_id): #del
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
    return redirect(url_for('administracao'))

@app.route('/admin/confirmar_pagamento/<int:pagamento_id>', methods=['POST'])
@login_required
def confirmar_pagamento(pagamento_id): #aprova
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))
    pagamento = Pagamento.query.get(pagamento_id)
    if not pagamento:
        return redirect(url_for('administracao'))
    comanda = Comanda.query.get(pagamento.comanda_id)
    pagamento.confirmado = True
    pagamento.confirmado_por = current_user.id
    comanda.estado = 'paga'
    comanda.pago_em = datetime.utcnow()
    comanda.pago_por = current_user.id
    db.session.commit()
    return redirect(url_for('administracao'))

@app.route('/admin/pagar_manual/<int:codigo>', methods=['GET','POST'])
@login_required
def pagar_admin(codigo): #caixa
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))
    comanda = Comanda.query.filter_by(codigo=codigo, estado='fechada').first()
    if not comanda:
        return redirect(url_for('administracao'))
    subtotal = sum(float(i.preco) * i.quantidade for i in comanda.itens)
    erro = None
    if request.method == 'POST':
        forma = request.form.get('forma')
        valor_recebido = float(request.form.get('valor_recebido'))
        if valor_recebido < subtotal:
            erro = f"Valor insuficiente. Total: R$ {subtotal:.2f}"
            return render_template('pagar_admin.html', comanda=comanda, subtotal=subtotal, erro=erro)
        troco = valor_recebido - subtotal
        pagamento = Pagamento(comanda_id=comanda.id, forma=forma, valor_recebido=valor_recebido, troco=troco, usuario_id=current_user.id, confirmado=True, confirmado_por=current_user.id)
        comanda.estado = 'paga'
        comanda.pago_em = datetime.utcnow()
        comanda.pago_por = current_user.id
        db.session.add(pagamento)
        db.session.commit()
        return redirect(url_for('administracao'))
    return render_template('pagar_admin.html', comanda=comanda, subtotal=subtotal, erro=erro)

@app.route('/admin/adicionar_item_cardapio', methods=['POST']) #add item pra adm
@login_required
def adicionar_item_cardapio():
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))

    nome = request.form.get('nome')
    preco = float(request.form.get('preco'))
    disponivel = request.form.get('disponivel') == 'on'  

    if nome and preco >= 0:
        item = ItemCardapio(nome=nome, preco=preco, disponivel=disponivel)
        db.session.add(item)
        db.session.commit()

    return redirect(url_for('administracao'))

@app.route('/admin/remover_item_cardapio/<int:item_id>', methods=['POST']) #remove item
@login_required
def remover_item_cardapio(item_id):
    if not usuario_tem_perfil('Administrador'):
        return redirect(url_for('index'))

    item = ItemCardapio.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('administracao'))


if __name__ == '__main__': #roda o flask server la
    with app.app_context():
        db.create_all()
    app.run(debug=True)
