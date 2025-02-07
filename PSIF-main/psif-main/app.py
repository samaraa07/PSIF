from datetime import datetime
from flask import Flask, session, request, render_template, url_for, redirect, flash
from database.db import obter_conexao
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models.usuario import User
from models.lancamentos import Lancamento
from models.participantes import Participante
from models.planilhas import Planilha
from simulacoes import SimulacaoJurosCompostos, SimulacaoSemRendimento
from util import datas

app = Flask(__name__)
app.secret_key = 'chave_secreta'

#  Chave para criptografia de cookies na sessão
app.config['SECRET_KEY'] = 'superdificil'
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

########################################################################

@app.route('/planilhas/<id>', methods=['GET', 'POST'])
@login_required
def planilha(id):
    p = Planilha.find(id)

    if not p:
        return render_template('erro404.html')

    if p.id_usuario == current_user.id:

        datetime_ini = datetime.strptime(p.data_ini, '%Y-%m-%d')
        datetime_fim = datetime.strptime(p.data_fim, '%Y-%m-%d')
        # O +1 é pra contar pelo menos 1 mês
        diferenca = datas.diferenca_meses(datetime_ini, datetime_fim) + 1
        # Gera o nome dos meses
        meses = []
        for i in range(diferenca):
            m = (i + datetime_ini.month) % 12
            # TODO: Gambiarra. Resolver de outra forma depois.
            if m == 0:
                m = 12
            meses += [datas.mes(m)]
        return render_template('planilha.html', planilha=p, meses=meses)
    
    else:
        return render_template('erro404.html')

########################################################################

@app.route('/planilhas', methods=['GET', 'POST'])
@login_required
def planilhas():
    if request.method == 'POST':
        id_usuario = current_user.id
        objetivo = request.form.get('objetivo')
        descricao = request.form.get('descricao')
        data_ini = request.form.get('data_ini')
        data_fim = request.form.get('data_fim')
        p = Planilha(id_usuario, descricao, objetivo, data_ini, data_fim)
        p.salvar()
        
    
    planilhas = Planilha.consultar('SELECT * FROM planilhas WHERE id_usuario=?', (current_user.id,))  # TODO: Filtrar pelo usuário logado
    return render_template('planilhas.html', planilhas=planilhas)

########################################################################

@app.route('/planilhas/<int:id_planilha>/participantes', methods=['GET', 'POST'])
@login_required 
def participantes(id_planilha):
    if request.method == 'POST':
        # TODO: tratar dados ausentes
        nome = request.form.get('nome_participante')
        contato = request.form.get('contato_participante')
        p = Participante(id_planilha=id_planilha, contato=contato, nome=nome)
        p.salvar()

    return redirect(url_for('planilha', id=id_planilha))


###############################################################

@app.route('/planilhas/<int:id_planilha>/excluir', methods=['POST'])
def excluir_planilha(id_planilha):
    p = Planilha.encontrar(id_planilha)
    p.excluir()
    return redirect(url_for('planilhas'))

###############################################################

@app.route('/planilhas/<int:id_planilha>/lancamentos', methods=['GET', 'POST'])
@login_required
def lancamentos(id_planilha):
    if request.method == 'POST':
        participante = request.form.get('participante')
        descricao = request.form.get('descricao')
        data = request.form.get('data')
        valor = request.form.get('valor')
        if not participante:
            flash('Por favor, selecione um participante.', 'error')
            return redirect(url_for('planilha', id=id_planilha))
        l = Lancamento(id_planilha, participante, descricao, data, valor)
        l.salvar()
    return redirect(url_for('planilha', id=id_planilha))

###############################################################

@app.route('/planilhas/<int:id_planilha>/lancamentos/<int:id_lancamento>/excluir', methods=['POST'])
@login_required
def excluir_lancamento(id_planilha, id_lancamento):
    l = Lancamento.encontrar(id_lancamento)
    l.excluir()
    return redirect(url_for('planilha', id=id_planilha))

#################################################################

@app.route('/planilhas/<int:id_planilha>/grafico', methods=['GET'])
@login_required
def grafico(id_planilha):
    # TODO: Criar função para não repetir esse código da rota Planilhas.

    p = Planilha.find(id_planilha)

    if not p:
        return render_template('erro404.html')
    
    datetime_ini = datetime.strptime(p.data_ini, '%Y-%m-%d')
    datetime_fim = datetime.strptime(p.data_fim, '%Y-%m-%d')
    # O +1 é pra contar pelo menos 1 mês
    diferenca = datas.diferenca_meses(datetime_ini, datetime_fim) + 1
    # Gera o nome dos meses
    meses = []
    for i in range(diferenca):
        m = (i + datetime_ini.month) % 12
        # TODO: Gambiarra. Resolver de outra forma depois.
        if m == 0:
            m = 12
        meses += [datas.mes(m)]

    return render_template('grafico.html', planilha=p, meses=meses)

#################################################################

@app.route('/planilhas/<int:id_planilha>/lista_participantes', methods=['GET'])
@login_required
def lista_participantes(id_planilha):
    # TODO: Criar função para não repetir esse código da rota Planilhas.

    p = Planilha.find(id_planilha)

    if not p:
        return render_template('erro404.html')
    
    return render_template('participantes.html', planilha=p)

#################################################################

@app.route('/planilhas/<int:id_planilha>/lista_lancamentos', methods=['GET'])
@login_required
def lista_lancamentos(id_planilha):
    # TODO: Criar função para não repetir esse código da rota Planilhas.

    p = Planilha.find(id_planilha)

    if not p:
        return render_template('erro404.html')
    
    return render_template('lancamentos.html', planilha=p)

#################################################################

@app.route('/evento')
def evento():
    return render_template('eventos.html')

@app.route('/submit', methods=['GET'])
def submit():
    opcao = request.args.get('opcao')
    
    if opcao == 'Piscina':
        return redirect(url_for('evento_detalhe', nome_evento='Piscina'))
    elif opcao == 'Churrasco':
        return redirect(url_for('evento_detalhe', nome_evento='Churrasco'))
    else:
        return 'Opção inválida'

@app.route('/evento/<nome_evento>')
def evento_detalhe(nome_evento):
    return render_template('evento_detalhe.html', nome_evento=nome_evento)

@app.route('/eventos', methods=['GET', 'POST'])
@login_required
def eventos():
    conn = obter_conexao()
    if request.method == 'POST':
        nome = request.form['nome']
        contato = request.form['contato']
        preco = request.form['preco']
        data_horario = request.form['data_horario']
        local = request.form['local']
        
        conn.execute(
            'INSERT INTO eventos (nome, contato, preco, data_horario, local, id_usuario) VALUES (?, ?, ?, ?, ?, ?)',
            (nome, contato, preco, data_horario, local, current_user.id)
        )
        conn.commit()
    
    eventos = conn.execute('SELECT * FROM eventos WHERE id_usuario = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('eventos.html', eventos=eventos)

@app.route('/eventos/<int:id_evento>/editar', methods=['GET', 'POST'])
@login_required
def editar_evento(id_evento):
    conn = obter_conexao()
    evento = conn.execute('SELECT * FROM eventos WHERE id = ? AND id_usuario = ?', (id_evento, current_user.id)).fetchone()
    
    if request.method == 'POST':
        nome = request.form['nome']
        contato = request.form['contato']
        preco = request.form['preco']
        data_horario = request.form['data_horario']
        local = request.form['local']
        
        conn.execute('UPDATE eventos SET nome = ?, contato = ?, preco = ?, data_horario = ?, local = ? WHERE id = ? AND id_usuario = ?',
                     (nome, contato, preco, data_horario, local, id_evento, current_user.id))
        conn.commit()
        conn.close()
        return redirect(url_for('eventos'))
    
    conn.close()
    return render_template('editar_evento.html', evento=evento)

@app.route('/eventos/<int:id_evento>/excluir', methods=['POST'])
@login_required
def excluir_evento(id_evento):
    conn = obter_conexao()
    conn.execute('DELETE FROM eventos WHERE id = ? AND id_usuario = ?', (id_evento, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('eventos'))

if __name__ == '__main__':
    app.run(debug=True)


####################################################################

@app.route('/juros', methods=['GET', 'POST'])
@login_required
def juros():
    if request.method == 'POST':
        try:
            objetivo = float(request.form['objetivo'])  # Valor total que se quer juntar
            taxa_juros = float(request.form['taxa']) / 100 / 12  # Convertendo para taxa mensal
            periodo_meses = int(request.form['periodo'])  # Período em meses
            num_participantes = int(request.form['pessoas'])  # Número de pessoas
            
            modelo = SimulacaoJurosCompostos(objetivo, taxa_juros, periodo_meses, num_participantes)
            mensalidade_por_pessoa, mensalidade_total, montante_acumulado = modelo.simular()

            # Arredondar valores para exibição
            objetivo = round(objetivo, 2)
            taxa_juros = round(taxa_juros * 100 * 12, 2)  # Convertendo de volta para percentual anual
            periodo_meses = round(periodo_meses, 2)
            mensalidade_por_pessoa = round(mensalidade_por_pessoa, 2)
            mensalidade_total = round(mensalidade_total, 2)
            montante_acumulado = round(montante_acumulado, 2)

            return render_template('juros.html', 
                                   objetivo=objetivo, 
                                   taxa_juros=taxa_juros, 
                                   periodo_meses=periodo_meses,
                                   num_participantes=num_participantes,
                                   mensalidade_por_pessoa=mensalidade_por_pessoa,
                                   mensalidade_total=mensalidade_total,
                                   montante_acumulado=montante_acumulado
                                  )
        except ValueError:
            return render_template('juros.html', error="Por favor, insira valores numéricos válidos.")

    return render_template('juros.html')

####################################################################

@app.route('/simulacao_sem_rendimentos', methods=['GET', 'POST'])
@login_required
def simulacao_sem_rendimentos():
    if request.method == 'POST':
        try:
            objetivo = float(request.form['objetivo'])  # Valor total que se quer juntar
            num_parcelas = int(request.form['num_parcelas'])  # Número de parcelas
            num_participantes = int(request.form['num_participantes'])  # Número de participantes
        except ValueError:
            return render_template('simulacao_sem_rendimentos.html', error="Por favor, insira valores numéricos válidos.")

        modelo = SimulacaoSemRendimento(objetivo, num_parcelas, num_participantes)
        mensalidade_por_participante, mensalidade_total, montante_acumulado = modelo.simular()

        # Arredondar valores para exibição
        objetivo = round(objetivo, 2)
        num_parcelas = round(num_parcelas, 2)
        mensalidade_por_participante = round(mensalidade_por_participante, 2)
        mensalidade_total = round(mensalidade_total, 2)
        montante_acumulado = round(montante_acumulado, 2)

        return render_template('simulacao_sem_rendimentos.html', 
                                objetivo=objetivo, 
                                num_parcelas=num_parcelas,
                                num_participantes=num_participantes,
                                mensalidade_por_participante=mensalidade_por_participante,
                                mensalidade_total=mensalidade_total,
                                montante_acumulado=montante_acumulado
                                )

    return render_template('simulacao_sem_rendimentos.html')




#################################################################################

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Verificar se o usuário já existe no banco de dados
        conn = obter_conexao()
        usuario_existente = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()

        if usuario_existente:
            conn.close()
            return "Usuário já existe", 400

        # Inserir novo usuário no banco de dados
        senha_hash = generate_password_hash(senha)
        conn.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                     (nome, email, senha_hash))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('cadastro.html')

#################################################################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = User.encontrar(email)
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('juros'))
        else:
            return "Credenciais inválidas", 401

    return render_template('login.html')

#################################################################################

##################### TESTE ####################################################

@app.route('/juros_e_planilha', methods=['GET', 'POST'])
@login_required
def juros_e_planilha():
    if request.method == 'POST':
        try:
            # Dados da planilha
            descricao = request.form.get('descricao')
            data_ini = request.form.get('data_ini')
            data_fim = request.form.get('data_fim')

            datetime_ini = datetime.strptime(data_ini, '%Y-%m-%d')
            datetime_fim = datetime.strptime(data_fim, '%Y-%m-%d')

            # Dados da simulação de juros
            objetivo = float(request.form['objetivo'])
            taxa_juros = float(request.form['taxa']) / 100 / 12
            # O +1 é pra contar pelo menos 1 mês
            periodo_meses = datas.diferenca_meses(datetime_ini, datetime_fim) + 1
            num_participantes = int(request.form['pessoas'])
            
            # Simulação de juros
            modelo = SimulacaoJurosCompostos(objetivo, taxa_juros, periodo_meses, num_participantes)
            mensalidade_por_pessoa, mensalidade_total, montante_acumulado = modelo.simular()

            # Arredondar valores para exibição
            objetivo = round(objetivo, 2)
            taxa_juros = round(taxa_juros * 100 * 12, 2)
            mensalidade_por_pessoa = round(mensalidade_por_pessoa, 2)
            mensalidade_total = round(mensalidade_total, 2)
            montante_acumulado = round(montante_acumulado, 2)

            # Criar a planilha se o botão for pressionado
            if 'criar_planilha' in request.form:
                planilha = Planilha(id_usuario=current_user.id, descricao=descricao, objetivo=objetivo, data_ini=data_ini, data_fim=data_fim)
                planilha_id = planilha.salvar()  # Salva e obtém o id
                flash('Planilha criada com sucesso!', 'success')
                return redirect(url_for('planilha', id=planilha_id))  # Redireciona para a planilha criada

            return render_template('juros_e_planilha.html', 
                                   objetivo=objetivo, 
                                   taxa_juros=taxa_juros, 
                                   periodo_meses=periodo_meses,
                                   num_participantes=num_participantes,
                                   mensalidade_por_pessoa=mensalidade_por_pessoa,
                                   mensalidade_total=mensalidade_total,
                                   montante_acumulado=montante_acumulado,
                                   descricao=descricao,
                                   data_ini=data_ini,
                                   data_fim=data_fim
                                  )
        except ValueError:
            return render_template('juros_e_planilha.html', error="Por favor, insira valores numéricos válidos.")

    return render_template('juros_e_planilha.html')

@app.route('/logout')
@login_required  # TODO: Não precisa estar logado para deslogar
def logout():
    logout_user()
    return redirect(url_for('index'))
