import sqlite3
from pathlib import Path
from flask import Flask, render_template, g, request, redirect, url_for, flash, make_response
from datetime import datetime
from io import StringIO
from os import mkdir
import csv


APP = Flask(__name__)
APP.secret_key = "i3SB2YIbUxWhS5nKHmZc"
APP.app_context().push()
HOMEDIR = Path(__file__).parent.absolute()
BANCO = f"{HOMEDIR}/banco/carteira.db"


def cria_banco(banco):
    '''
    CRIA A PASTA E O BANCO DE DADOS CASO NÃO EXISTAM
    '''
    
    if not Path(banco).parents[0].is_dir():
        mkdir(Path(banco).parents[0])
    
    if not Path(banco).is_file():
        conn = sqlite3.connect(banco)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE "categorias" (
	                    "id"	INTEGER NOT NULL UNIQUE,
	                    "categoria"	TEXT NOT NULL UNIQUE,
	                    PRIMARY KEY("id" AUTOINCREMENT))''')
        
        cursor.execute('''CREATE TABLE "modais" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "modal"	TEXT NOT NULL UNIQUE,
                        PRIMARY KEY("id" AUTOINCREMENT))''')

        cursor.execute('''CREATE TABLE "gastos" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "valor"	REAL NOT NULL,
                        "categoria"	TEXT NOT NULL,
                        "modal"	TEXT NOT NULL,
                        "data"	TEXT NOT NULL,
                        "obs"	TEXT,
                        PRIMARY KEY("id"))''')

        cursor.execute('''CREATE TABLE "renda" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "valor"	REAL NOT NULL,
                        "categoria"	TEXT NOT NULL,
                        "data"	TEXT NOT NULL,
                        "obs"	TEXT,
                        PRIMARY KEY("id"))''')
        conn.commit()
        

cria_banco(BANCO)
DB = getattr(g, "_database", None)
DB = g._database = sqlite3.connect(BANCO, check_same_thread=False)
CURSOR = DB.cursor()


def ajustadata(data):
    '''
    FUNCAO PARA AJUSTAR A DATA NO FORMATO DIA/MES/ANO
    '''
    dia = data[8:10]
    mes = data[5:7]
    ano = data[0:4]
    return f"{dia}/{mes}/{ano}"


def queryGastos():
    '''
    FAZ A QUERY DE TODAS AS LINHAS DA TABELA GASTOS E RETORNA UM DICIONARIO COM OS VALORES
    '''
    CURSOR.execute("SELECT id, valor, categoria, modal, data, obs FROM gastos")
    dados = {gasto[0]: {"valor": gasto[1], "categoria": gasto[2], "modal": gasto[3],
                        "data": ajustadata(gasto[4]), "obs": gasto[5]} for gasto in CURSOR.fetchall()}
    return dados


def queryGastosMesAtual():
    '''
    FAZ A QUERY E RETORNA A SOMA DE TODOS OS GASTOS NO MES ATUAL
    '''
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(
        f"SELECT strftime('%Y-%m', data) AS mes, total(valor) AS soma FROM gastos WHERE mes = '{ANO}-{MES}' GROUP BY mes ORDER BY mes")
    dados = CURSOR.fetchall()
    if dados:
        dados = dados[0][1]
    else:
        dados = 0
    return dados


def queryGastosPorDiaNoMes():
    '''
    FAZ A QUERY E RETORNA A SOMATORIA DE TODOS OS GASTOS DO MES ATUAL SEPARADO POR DIA
    '''
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(
        f"SELECT strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM gastos WHERE strftime('%Y-%m', data) = '{ANO}-{MES}'GROUP BY dia ORDER BY dia")
    gastosdia = CURSOR.fetchall()
    gastosdia = {int(dia[0]): dia[1] for dia in gastosdia}
    dados = [0 for x in range(1, 32)]
    for dia in gastosdia:
        dados[dia - 1] = gastosdia[dia]
    return dados


def queryGastosPorCategoria():
    '''
    RETORNA A SOMATORIA DE GASTOS POR CATEGORIA NO ANO ATUAL
    '''
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT categoria, round(total(valor),2) FROM gastos WHERE strftime('%Y', data) = '{ANO}' GROUP BY categoria ORDER BY categoria")
    dados = CURSOR.fetchall()
    categorias = [c[0] for c in dados]
    valores = [v[1] for v in dados]
    
    return dict(zip(categorias, valores))

def queryGastosPorMes():
    '''
    RETORNA A SOMATORIA DE GASTOS POR MES NO ANO ATUAL
    '''
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT strftime('%m', data) as mes, round(total(valor),2) FROM gastos WHERE strftime('%Y', data) = '{ANO}' GROUP BY mes ORDER BY mes")
    valores = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dados = {int(d[0]):d[1] for d in CURSOR.fetchall()}
    for mes in dados:
        valores[mes-1] = dados[mes]
    return valores
    

def listaCategorias():
    '''
    RETORNA A LISTA DE CATEGORIAS NA TABELA CATEGORIAS
    '''
    CURSOR.execute("SELECT categoria FROM categorias")
    cats = [cat[0] for cat in CURSOR.fetchall()]
    return sorted(cats)


def listaModais():
    '''
    RETORNA A LISTA DE MODAIS NA TABELA MODAIS
    '''
    CURSOR.execute("SELECT modal FROM modais")
    modais = [mod[0] for mod in CURSOR.fetchall()]
    return sorted(modais)


def queryRenda():
    '''
    FAZ A QUERY DE TODAS AS LINHAS DA TABELA RENDA E RETORNA UM DICIONARIO COM OS VALORES
    '''
    CURSOR.execute("SELECT id, valor, categoria, data, obs FROM renda")
    dados = {renda[0]: {"valor": renda[1], "categoria": renda[2], "data": ajustadata(renda[3]), "obs": renda[4]} for renda in CURSOR.fetchall()}
    return dados


def queryRendaMesAtual():
    '''
    FAZ A QUERY E RETORNA A SOMA DE TODAS AS RENDAS NO MES ATUAL
    '''
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(
        f"SELECT strftime('%Y-%m', data) AS mes, round(total(valor),2) AS soma FROM renda WHERE mes = '{ANO}-{MES}' GROUP BY mes ORDER BY mes")
    dados = CURSOR.fetchall()
    if dados:
        dados = dados[0][1]
    else:
        dados = 0
    return dados


def queryRendaPorDiaNoMes():
    '''
    FAZ A QUERY E RETORNA A SOMATORIA DE TODOS AS RENDAS DO MES ATUAL SEPARADO POR DIA
    '''
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(
        f"SELECT strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM renda WHERE strftime('%Y-%m', data) = '{ANO}-{MES}'GROUP BY dia ORDER BY dia")
    rendadia = CURSOR.fetchall()
    rendadia = {int(dia[0]): dia[1] for dia in rendadia}
    dados = [0 for x in range(1, 32)]
    for dia in rendadia:
        dados[dia - 1] = rendadia[dia]
    return dados

def queryRendaPorCategoria():
    '''
    RETORNA A SOMATORIA DE RENDAS POR CATEGORIA NO ANO ATUAL
    '''
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT categoria, round(total(valor),2) FROM renda WHERE strftime('%Y', data) = '{ANO}' GROUP BY categoria ORDER BY categoria")
    dados = CURSOR.fetchall()
    categorias = [c[0] for c in dados]
    valores = [v[1] for v in dados]
    
    return dict(zip(categorias, valores))


def queryRendaPorMes():
    '''
    RETORNA A SOMATORIA DE GASTOS POR MES NO ANO ATUAL
    '''
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT strftime('%m', data) as mes, round(total(valor),2) FROM renda WHERE strftime('%Y', data) = '{ANO}' GROUP BY mes ORDER BY mes")
    valores = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dados = {int(d[0]):d[1] for d in CURSOR.fetchall()}
    for mes in dados:
        valores[mes-1] = dados[mes]
    return valores


def querySaldo():
    '''
    RETORNA O SALDO EQUIVALENTE A SOMATORIA DE RENDAS MENOS A SOMATORIA DE GASTOS
    '''
    CURSOR.execute("SELECT total(valor) FROM gastos")
    try:
        gastos = CURSOR.fetchall()[0][0]
    except ValueError:
        gastos = 0
    CURSOR.execute("SELECT total(valor) FROM renda")
    try:
        renda = CURSOR.fetchall()[0][0]
    except ValueError:
        renda = 0
    
    resultado = renda - gastos
    if resultado >= 0:
        resultado = f"+R$ {round(resultado, 2)}"
    else:
        resultado = f"-R$ {round(resultado, 2)}"
    
    return resultado
    
    
def adicionaCategoria(categoria):
    '''
    ADICIONA A CATEGORIA NA TABELA CATEGORIAS
    '''
    if categoria in [None, '', ' ']:
        flash(f"Erro ao adicionar a categoria '{categoria}' à lista.")
        return False
    else:
        CURSOR.execute(
            f"INSERT INTO categorias (categoria) VALUES (?)", (categoria,))
        DB.commit()
        flash(f"Categoria '{categoria}' adicionada com sucesso.")
        return True


def deletaCategoria(categoria):
    '''
    DELETA A CATEGORIA DA TABELA CATEGORIAS
    '''
    if categoria in [None, '', ' ']:
        flash(f"Erro ao remover a categoria '{categoria}' da lista.")
        return False
    else:
        CURSOR.execute(
            f"DELETE FROM categorias WHERE categoria = '{categoria}'")
        DB.commit()
        flash(f"Categoria '{categoria}' removida com sucesso.")
        return True


def adicionaModal(modal):
    '''
    ADICIONA MODAL NA TABELA MODAIS
    '''
    if modal in [None, '', ' ']:
        flash(f"Erro ao adicionar o modal '{modal}' à lista.")
        return False
    else:
        CURSOR.execute(f"INSERT INTO modais (modal) VALUES (?)", (modal,))
        DB.commit()
        flash(f"Modal '{modal}' adicionado com sucesso.")
        return True


def deletaModal(modal):
    '''
    DELETA MODAL DA TABELA MODAIS
    '''
    if modal in [None, '', ' ']:
        flash(f"Erro ao remover o modal '{modal}' da lista.")
        return False
    else:
        CURSOR.execute(f"DELETE FROM modais WHERE modal = '{modal}'")
        DB.commit()
        flash(f"Modal '{modal}' removido com sucesso.")
        return True


def adicionaGasto(valor, categoria, modal, data, obs):
    '''
    ADEQUA E ADICIONA UM GASTO NOVO NA TABELA GASTOS
    '''
    VALOR = valor
    CATEGORIA = categoria
    MODAL = modal
    DATA = data
    OBS = obs
    try:
        VALOR = float(valor)
        if OBS in [None, '', ' ']:
            OBS = ''

        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{DATA} {HORA}"

        CURSOR.execute(f"INSERT INTO gastos (valor, categoria, modal, data, obs) VALUES (?, ?, ?, ?, ?)", (VALOR, CATEGORIA, MODAL, DATA, OBS,))
        DB.commit()
        flash(f"Novo gasto inserido na tabela com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao inserir novo gasto na tabela: '{e}'")
        return False


def deletaGasto(id):
    '''
    DELETA O GASTO SELECIONADO DA TABELA GASTOS
    '''
    ID = int(id)
    try:
        CURSOR.execute(f"DELETE FROM gastos WHERE id = {ID}")
        DB.commit()
        flash(f"Linha {ID} deletada com sucesso.")
        return True
    except Exception as e:
        print(e)
        flash(f"Erro ao deletar linha {ID}: {e}")
        return False


def adicionaRenda(valor, categoria, data, obs):
    '''
    ADEQUA E ADICIONA UMA RENDA NOVA NA TABELA RENDAS
    '''
    VALOR = valor
    CATEGORIA = categoria
    DATA = data
    OBS = obs
    try:
        VALOR = float(valor)
        if OBS in [None, '', ' ']:
            OBS = ''

        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{DATA} {HORA}"

        CURSOR.execute(f"INSERT INTO renda (valor, categoria, data, obs) VALUES (?, ?, ?, ?)", (VALOR, CATEGORIA, DATA, OBS,))
        DB.commit()
        flash(f"Nova renda inserida na tabela com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao inserir nova renda na tabela: '{e}'")
        return False


def deletaRenda(id):
    '''
    DELETA A RENDA SELECIONADA DA TABELA RENDAS
    '''
    ID = int(id)
    try:
        CURSOR.execute(f"DELETE FROM renda WHERE id = {ID}")
        DB.commit()
        flash(f"Linha {ID} deletada com sucesso.")
        return True
    
    except Exception as e:
        print(e)
        flash(f"Erro ao deletar linha {ID}: {e}")
        return False


def exporta_gastos():
    memoria = StringIO()
    CSV = csv.writer(memoria)
    CURSOR.execute("SELECT * FROM gastos")
    valores = CURSOR.fetchall()
    CSV.writerow([i[0] for i in CURSOR.description])
    CSV.writerows(valores)
    
    resposta = make_response(memoria.getvalue())
    resposta.headers['Content-Disposition'] = 'attachment; filename=Gastos.csv'
    resposta.headers["Content-type"] = "text/csv"
    
    return resposta


def exporta_renda():
    memoria = StringIO()
    CSV = csv.writer(memoria)
    CURSOR.execute("SELECT * FROM renda")
    valores = CURSOR.fetchall()
    CSV.writerow([i[0] for i in CURSOR.description])
    CSV.writerows(valores)
    
    resposta = make_response(memoria.getvalue())
    resposta.headers['Content-Disposition'] = 'attachment; filename=Renda.csv'
    resposta.headers["Content-type"] = "text/csv"
    
    return resposta


@APP.route("/")
def index():
    '''
    RETORNA A PAGINA PRINCIPAL QUE CONTEM APENAS O MENU LATERAL
    '''
    return render_template("index.html")

@APP.errorhandler(404)
def erro404(e):
    '''
    RETORNA PARA A PAGINA RESUMO EM CASO DE PAGINA NAO ENCONTRADA
    '''
    return redirect(url_for("index"))


@APP.route("/resumo")
def resumo():
    '''
    RETORNA A PAGINA RESUMO COM TODOS OS DADOS NECESSARIOS
    '''
    gastostotal = queryGastos()
    gastostotalmes = queryGastosMesAtual()
    gastodia = queryGastosPorDiaNoMes()
    rendatotal = queryRenda()
    rendatotalmes = queryRendaMesAtual()
    rendadia = queryRendaPorDiaNoMes()
    saldo = querySaldo()

    return render_template("resumo.html", gastos=gastostotal, renda=rendatotal, gastomes=gastostotalmes, rendames=rendatotalmes, gastodia=gastodia, rendadia=rendadia, saldo=saldo)


@APP.route("/gastos", methods=['GET', 'POST'])
def gastos():
    '''
    RETORNA A PAGINA GASTOS COM TODOS OS DADOS NECESSARIOS
    '''
    categorias = listaCategorias()
    modais = listaModais()
    gastos = queryGastos()
    categoriasGraficoGastosPorCat = queryGastosPorCategoria()
    gastospormes = queryGastosPorMes()

    return render_template("gastos.html", categorias=categorias, modais=modais, gastos=gastos, catsGrafGpC=categoriasGraficoGastosPorCat, GrafGpM=gastospormes)


@APP.route("/gastos_add", methods=["POST"])
def gastos_add():
    '''
    PROCESSA O FORMULARIO DE ADICAO DE GASTO E ATUALIZA A PAGINA GASTOS
    '''
    valor = request.form['valor']
    categoria = request.form['categoria']
    modal = request.form['modal']
    data = request.form['data']
    obs = request.form['obs']
    adicionaGasto(valor, categoria, modal, data, obs)

    return redirect(url_for("gastos"))


@APP.route("/gastos_del", methods=["POST"])
def gastos_del():
    '''
    PROCESSA O FORMULARIO DE EXCLUSAO DE GASTO E ATUALIZA A PAGINA GASTOS
    '''
    ID = request.form['ID']
    deletaGasto(ID)

    return redirect(url_for("gastos"))


@APP.route("/renda", methods=['GET', 'POST'])
def renda():
    '''
    RETORNA A PAGINA RENDA COM TODOS OS DADOS NECESSARIOS
    '''

    categorias = listaCategorias()
    rendas = queryRenda()
    categoriasGraficoRendaPorCat = queryRendaPorCategoria()
    rendapormes = queryRendaPorMes()
    
    return render_template("renda.html", categorias=categorias, rendas=rendas, catsGrafRpC=categoriasGraficoRendaPorCat, GrafRpM=rendapormes)


@APP.route("/renda_add", methods=["POST"])
def renda_add():
    '''
    PROCESSA O FORMULARIO DE ADICAO DE RENDA E ATUALIZA A PAGINA RENDA
    '''
    valor = request.form['valor']
    categoria = request.form['categoria']
    data = request.form['data']
    obs = request.form['obs']
    adicionaRenda(valor, categoria, data, obs)

    return redirect(url_for("renda"))


@APP.route("/renda_del", methods=["POST"])
def renda_del():
    '''
    PROCESSA O FORMULARIO DE EXCLUSAO DE RENDA E ATUALIZA A PAGINA RENDA
    '''
    ID = request.form['ID']
    deletaRenda(ID)

    return redirect(url_for("renda"))


@APP.route("/poupanca")
def poupanca():
    '''
    RETORNA A PAGINA POUPANCA COM TODOS OS DADOS NECESSARIOS
    '''

    return render_template("poupanca.html")


@APP.route("/config", methods=['GET', 'POST'])
def config():
    '''
    RETORNA A PAGINA DE CONFIGURACOES COM TODOS OS DADOS NECESSARIOS
    '''
    categorias = listaCategorias()
    modais = listaModais()

    return render_template("config.html", categorias=categorias, modais=modais)


@APP.route("/config_add_categoria", methods=["POST"])
def config_add_categoria():
    '''
    PROCESSA O FORMULARIO DE ADICAO DE CATEGORIA E ATUALIZA A PAGINA CONFIGURACOES
    '''
    categoria = request.form["add_categoria"]
    adicionaCategoria(categoria)

    return redirect(url_for("config"))


@APP.route("/config_del_categoria", methods=["POST"])
def config_del_categoria():
    '''
    PROCESSA O FORMULARIO DE EXCLUSAO DE CATEGORIA E ATUALIZA A PAGINA CONFIGURACOES
    '''
    categoria = request.form["del_categoria"]
    deletaCategoria(categoria)

    return redirect(url_for("config"))


@APP.route("/config_add_modal", methods=["POST"])
def config_add_modal():
    '''
    PROCESSA O FORMULARIO DE ADICAO DE MODAL E ATUALIZA A PAGINA CONFIGURACOES
    '''
    modal = request.form["add_modal"]
    adicionaModal(modal)

    return redirect(url_for("config"))


@APP.route("/config_del_modal", methods=["POST"])
def config_del_modal():
    '''
    PROCESSA O FORMULARIO DE EXCLUSAO DE MODAL E ATUALIZA A PAGINA CONFIGURACOES
    '''
    modal = request.form["del_modal"]
    deletaModal(modal)

    return redirect(url_for("config"))

@APP.route("/exportar_gastos", methods=["GET"])
def config_exportar_gastos():
    '''
    ENVIA O CSV DA TABELA DE GASTOS
    '''
    resposta = exporta_gastos()

    return resposta

@APP.route("/exportar_renda", methods=["GET"])
def config_exportar_renda():
    '''
    ENVIA O CSV DA TABELA DE RENDA
    '''
    resposta = exporta_renda()

    return resposta

@APP.route("/info")
def info():
    '''
    RETORNA A PAGINA INFORMACOES COM TODOS OS DADOS NECESSARIOS
    '''

    return render_template("info.html")


if __name__ == "__main__":
    import webbrowser
    from waitress import serve
    print("#" * 50)
    print("")
    print("Aplicativo iniciado no link: http://localhost:8080")
    print("")
    print("#" * 50)
    print("\n\n")
    webbrowser.open('http://localhost:8080', new=2)
    # serve(APP, host='0.0.0.0', port=8080)
    APP.run(host='0.0.0.0', port=8080, debug=True)