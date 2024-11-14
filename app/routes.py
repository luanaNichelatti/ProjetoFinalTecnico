import os
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Item, User  # Certifique-se de que o modelo Produto é Item no seu caso
from app.forms import CadastroForm, LoginForm, CompraProdutoForm, VendaProdutoForm

# Configuração para upload de imagens
UPLOAD_FOLDER = 'static/img/produtos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def page_home():
    return render_template("home.html")

@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def page_produto():
    compra_form = CompraProdutoForm()
    venda_form = VendaProdutoForm()

    if request.method == "POST":
        produto_id = request.form.get('produto_id')

        if produto_id:
            return redirect(url_for('page_pagamento', produto_id=produto_id))

    itens = Item.query.filter_by(dono=None)
    dono_itens = Item.query.filter_by(dono=current_user.id)

    return render_template("produtos.html", itens=itens, compra_form=compra_form, dono_itens=dono_itens, venda_form=venda_form)

@app.route('/pagamento', methods=['GET', 'POST'])
@login_required
def page_pagamento():
    produto_id = request.args.get('produto_id')

    if request.method == "POST":
        pagamento = request.form.get('pagamento')
        produto_obj = Item.query.get(produto_id)
        if produto_obj:
            flash(f"Pagamento realizado com sucesso usando {pagamento}.", category='success')
            # Adicione lógica adicional se necessário (e.g., atualizar banco de dados)

        return redirect(url_for('page_produto'))

    return render_template('pagamento.html', produto_id=produto_id)

@app.route('/cadastro', methods=['GET', 'POST'])
def page_cadastro():
    form = CadastroForm()
    if form.validate_on_submit():
        usuario = User(
            usuario=form.usuario.data,
            email=form.email.data,
            senhacrip=form.senha1.data
        )
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('page_produto'))
    if form.errors != {}:
        for err in form.errors.values():
            flash(f"Erro ao cadastrar usuário {err}", category='danger')

    return render_template("cadastro.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def page_login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario_logado = User.query.filter_by(usuario=form.usuario.data).first()
        if usuario_logado and usuario_logado.converte_senha(senha_texto_claro=form.senha.data):
            login_user(usuario_logado)
            flash(f'Sucesso! Seu login é: {usuario_logado.usuario}', category='success')
            return redirect(url_for('page_produto'))
        else:
            flash('Usuário ou senha estão incorretos! Tente novamente.', category='danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def page_logout():
    logout_user()
    flash("Você fez o logout", category='info')
    return redirect(url_for('page_home'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def page_perfil():
    if request.method == "POST":
        # Atualiza o usuário
        current_user.usuario = request.form['usuario']
        current_user.email = request.form['email']
        # Aqui você pode adicionar lógica para salvar o endereço e outras informações
        new_senha = request.form['senha1']
        confirm_senha = request.form['senha2']

        if new_senha and new_senha == confirm_senha:
            current_user.senhacrip = new_senha

        db.session.commit()
        flash('Informações do perfil atualizadas com sucesso!', category='success')
        return redirect(url_for('page_perfil'))

    return render_template('perfil.html')

@app.route('/produto_detalhes/<int:produto_id>', methods=['GET'])
@login_required
def page_produto_detalhes(produto_id):
    item = Item.query.get(produto_id)
    if not item:
        flash("Produto não encontrado.", category='danger')
        return redirect(url_for('page_produto'))

    return render_template('produto_detalhes.html', item=item)

@app.route('/contato', methods=['GET'])
def page_contato():
    return render_template('contato.html')

# Função para upload de imagem de produto
@app.route('/upload_imagem/<int:produto_id>', methods=['POST'])
@login_required
def upload_imagem(produto_id):
    item = Item.query.get(produto_id)
    if not item:
        flash('Produto não encontrado!', category='danger')
        return redirect(url_for('page_produto'))

    if 'imagem' not in request.files:
        flash('Nenhuma imagem foi enviada!', category='danger')
        return redirect(url_for('page_produto_detalhes', produto_id=produto_id))

    imagem = request.files['imagem']
    if imagem and allowed_file(imagem.filename):
        filename = secure_filename(imagem.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagem.save(filepath)
        item.imagem = filename  # Armazena o nome da imagem no banco de dados
        db.session.commit()  # Salva as alterações no banco de dados
        flash('Imagem carregada com sucesso!', category='success')
        return redirect(url_for('page_produto_detalhes', produto_id=produto_id))
    else:
        flash('Tipo de arquivo não permitido. Tente novamente.', category='danger')
        return redirect(url_for('page_produto_detalhes', produto_id=produto_id))

