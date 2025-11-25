from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required
from models import Usuario

auth = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def carregar_usuario(usuario_id): #flask login pro user do banco
    return Usuario.query.get(int(usuario_id))

@auth.route('/login', methods=['GET', 'POST'])
def login(): #funcao pra digita verifica e entra
    if request.method == 'POST':
        login_digitado = request.form.get('login')
        senha_digitada = request.form.get('senha')
        usuario = Usuario.query.filter_by(login=login_digitado).first()
        if usuario and usuario.senha == senha_digitada:
            login_user(usuario)
            return redirect(url_for('index'))
        return render_template('login.html', erro='Login ou senha inválidos')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout(): #sair
    logout_user()
    return redirect(url_for('auth.login'))
