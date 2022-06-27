import sqlite3
from pathlib import Path
from colorama import Cursor
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
    """
    CRIA A PASTA E O BANCO DE DADOS CASO NÃO EXISTAM
    """

    if not Path(banco).parents[0].is_dir():
        mkdir(Path(banco).parents[0])

    if not Path(banco).is_file():
        conn = sqlite3.connect(banco)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE "categorias" (
	                    "id"	INTEGER NOT NULL UNIQUE,
	                    "categoria"	TEXT NOT NULL UNIQUE,
	                    PRIMARY KEY("id" AUTOINCREMENT))"""
        )

        cursor.execute("INSERT INTO categorias (categoria) VALUES ('Poupança')")

        cursor.execute(
            """CREATE TABLE "modais" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "modal"	TEXT NOT NULL UNIQUE,
                        PRIMARY KEY("id" AUTOINCREMENT))"""
        )

        cursor.execute("INSERT INTO modais (modal) VALUES ('Dinheiro')")
        cursor.execute("INSERT INTO modais (modal) VALUES ('Débito')")
        cursor.execute("INSERT INTO modais (modal) VALUES ('Crédito')")

        cursor.execute(
            """CREATE TABLE "gastos" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "valor"	REAL NOT NULL,
                        "categoria"	TEXT NOT NULL,
                        "modal"	TEXT NOT NULL,
                        "data"	TEXT NOT NULL,
                        "obs"	TEXT,
                        PRIMARY KEY("id"))"""
        )

        cursor.execute(
            """CREATE TABLE "renda" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "valor"	REAL NOT NULL,
                        "categoria"	TEXT NOT NULL,
                        "data"	TEXT NOT NULL,
                        "obs"	TEXT,
                        PRIMARY KEY("id"))"""
        )

        cursor.execute(
            """CREATE TABLE "sonhos" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "nome"	TEXT NOT NULL UNIQUE,
                        "meta"	REAL NOT NULL,
                        "obs"	TEXT,
                        "status"	TEXT NOT NULL,
                        PRIMARY KEY("id"))"""
        )

        cursor.execute(
            """CREATE TABLE "aplicacoes" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "nome"	TEXT NOT NULL,
                        "valor"	REAL NOT NULL,
                        "data"	TEXT NOT NULL,
                        PRIMARY KEY("id"))"""
        )

        conn.commit()


cria_banco(BANCO)
DB = getattr(g, "_database", None)
DB = g._database = sqlite3.connect(BANCO, check_same_thread=False)
CURSOR = DB.cursor()


def ajustadata(data):
    """
    FUNCAO PARA AJUSTAR A DATA NO FORMATO DIA/MES/ANO
    """
    dia = data[8:10]
    mes = data[5:7]
    ano = data[0:4]
    return f"{dia}/{mes}/{ano}"


def queryGastos():
    """
    FAZ A QUERY DE TODAS AS LINHAS DA TABELA GASTOS E RETORNA UM DICIONARIO COM OS VALORES
    """
    CURSOR.execute("SELECT id, valor, categoria, modal, data, obs FROM gastos")
    dados = {gasto[0]: {"valor": gasto[1], "categoria": gasto[2], "modal": gasto[3], "data": ajustadata(gasto[4]), "obs": gasto[5]} for gasto in CURSOR.fetchall()}
    return dados


def queryGastoUnico(ID):
    """
    FAZ A QUERY DA LINHA DO ID SELECIONADO
    """
    CURSOR.execute(f"SELECT id, valor, categoria, modal, data, obs FROM gastos WHERE id = {ID}")
    dados = {valor[0]: {"valor": valor[1], "categoria": valor[2], "modal": valor[3], "data": ajustadata(valor[4]), "obs": valor[5]} for valor in CURSOR.fetchall()}
    return dados


def queryGastosMesAtual():
    """
    FAZ A QUERY E RETORNA A SOMA DE TODOS OS GASTOS NO MES ATUAL
    """
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(f"SELECT strftime('%Y-%m', data) AS mes, total(valor) AS soma FROM gastos WHERE mes = '{ANO}-{MES}' GROUP BY mes ORDER BY mes")
    dados = CURSOR.fetchall()
    if dados:
        dados = dados[0][1]
    else:
        dados = 0
    return dados


def queryGastosPorDiaNoMes():
    """
    FAZ A QUERY E RETORNA A SOMATORIA DE TODOS OS GASTOS DO MES ATUAL SEPARADO POR DIA
    """
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(f"SELECT strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM gastos WHERE strftime('%Y-%m', data) = '{ANO}-{MES}'GROUP BY dia ORDER BY dia")
    gastosdia = CURSOR.fetchall()
    gastosdia = {int(dia[0]): dia[1] for dia in gastosdia}
    dados = [0 for x in range(1, 32)]
    for dia in gastosdia:
        dados[dia - 1] = gastosdia[dia]
    return dados


def queryGastosPorCategoria():
    """
    RETORNA A SOMATORIA DE GASTOS POR CATEGORIA NO ANO ATUAL
    """
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT categoria, round(total(valor),2) FROM gastos WHERE strftime('%Y', data) = '{ANO}' GROUP BY categoria ORDER BY categoria")
    dados = CURSOR.fetchall()
    categorias = [c[0] for c in dados]
    valores = [v[1] for v in dados]

    return dict(zip(categorias, valores))


def queryGastosPorMes():
    """
    RETORNA A SOMATORIA DE GASTOS POR MES NO ANO ATUAL
    """
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT strftime('%m', data) as mes, round(total(valor),2) FROM gastos WHERE strftime('%Y', data) = '{ANO}' GROUP BY mes ORDER BY mes")
    valores = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dados = {int(d[0]): d[1] for d in CURSOR.fetchall()}
    for mes in dados:
        valores[mes - 1] = dados[mes]
    return valores


def listaCategorias():
    """
    RETORNA A LISTA DE CATEGORIAS NA TABELA CATEGORIAS
    """
    CURSOR.execute("SELECT categoria FROM categorias")
    cats = [cat[0] for cat in CURSOR.fetchall()]
    return sorted(cats)


def listaModais():
    """
    RETORNA A LISTA DE MODAIS NA TABELA MODAIS
    """
    CURSOR.execute("SELECT modal FROM modais")
    modais = [mod[0] for mod in CURSOR.fetchall()]
    return sorted(modais)


def queryRenda():
    """
    FAZ A QUERY DE TODAS AS LINHAS DA TABELA RENDA E RETORNA UM DICIONARIO COM OS VALORES
    """
    CURSOR.execute("SELECT id, valor, categoria, data, obs FROM renda")
    dados = {renda[0]: {"valor": renda[1], "categoria": renda[2], "data": ajustadata(renda[3]), "obs": renda[4]} for renda in CURSOR.fetchall()}
    return dados


def queryRendaUnica(ID):
    """
    FAZ A QUERY DA LINHA DO ID SELECIONADO
    """
    CURSOR.execute(f"SELECT id, valor, categoria, data, obs FROM renda WHERE id = {ID}")
    dados = {valor[0]: {"valor": valor[1], "categoria": valor[2], "data": ajustadata(valor[3]), "obs": valor[4]} for valor in CURSOR.fetchall()}
    return dados


def queryRendaMesAtual():
    """
    FAZ A QUERY E RETORNA A SOMA DE TODAS AS RENDAS NO MES ATUAL
    """
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(f"SELECT strftime('%Y-%m', data) AS mes, round(total(valor),2) AS soma FROM renda WHERE mes = '{ANO}-{MES}' GROUP BY mes ORDER BY mes")
    dados = CURSOR.fetchall()
    if dados:
        dados = dados[0][1]
    else:
        dados = 0
    return dados


def queryRendaPorDiaNoMes():
    """
    FAZ A QUERY E RETORNA A SOMATORIA DE TODOS AS RENDAS DO MES ATUAL SEPARADO POR DIA
    """
    ANO = str(datetime.now().year)
    MES = str(datetime.now().month).zfill(2)
    CURSOR.execute(f"SELECT strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM renda WHERE strftime('%Y-%m', data) = '{ANO}-{MES}'GROUP BY dia ORDER BY dia")
    rendadia = CURSOR.fetchall()
    rendadia = {int(dia[0]): dia[1] for dia in rendadia}
    dados = [0 for x in range(1, 32)]
    for dia in rendadia:
        dados[dia - 1] = rendadia[dia]
    return dados


def queryRendaPorCategoria():
    """
    RETORNA A SOMATORIA DE RENDAS POR CATEGORIA NO ANO ATUAL
    """
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT categoria, round(total(valor),2) FROM renda WHERE strftime('%Y', data) = '{ANO}' GROUP BY categoria ORDER BY categoria")
    dados = CURSOR.fetchall()
    categorias = [c[0] for c in dados]
    valores = [v[1] for v in dados]

    return dict(zip(categorias, valores))


def queryRendaPorMes():
    """
    RETORNA A SOMATORIA DE GASTOS POR MES NO ANO ATUAL
    """
    ANO = str(datetime.now().year)
    CURSOR.execute(f"SELECT strftime('%m', data) as mes, round(total(valor),2) FROM renda WHERE strftime('%Y', data) = '{ANO}' GROUP BY mes ORDER BY mes")
    valores = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dados = {int(d[0]): d[1] for d in CURSOR.fetchall()}
    for mes in dados:
        valores[mes - 1] = dados[mes]
    return valores


def querySaldo():
    """
    RETORNA O SALDO EQUIVALENTE A SOMATORIA DE RENDAS MENOS A SOMATORIA DE GASTOS
    """
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


def queryPoupaca():
    """
    RETORNA O SALDO TOTAL DA POUPANÇA
    """

    poupanca = 0

    CURSOR.execute("SELECT total(valor) FROM gastos WHERE categoria = 'Poupança'")
    try:
        poupanca = CURSOR.fetchall()[0][0]
    except ValueError:
        poupanca = 0

    CONCLUIDOS = []
    CURSOR.execute("SELECT nome FROM sonhos WHERE status = 'CONCLUIDO'")
    for row in CURSOR:
        try:
            CONCLUIDOS.append(row[0])
        except ValueError:
            pass

    valorconcluido = 0
    for C in CONCLUIDOS:
        CURSOR.execute(f"SELECT total(valor) FROM aplicacoes WHERE nome = '{C}'")
        for row in CURSOR:
            try:
                valorconcluido += row[0]
            except ValueError:
                pass

    return poupanca - valorconcluido


def queryAplicacoes():
    """
    RETORNA O TOTAL APLICADO
    """

    CURSOR.execute("SELECT nome FROM sonhos WHERE status = 'ABERTO'")
    NOMES = []
    for row in CURSOR.fetchall():
        NOMES.append(row[0])

    VALORAPLICADO = 0

    if NOMES:
        for N in NOMES:
            CURSOR.execute(f"SELECT total(valor) FROM aplicacoes WHERE nome = '{N}'")
            try:
                VALOR = CURSOR.fetchall()[0][0]
            except ValueError:
                VALOR = 0

            VALORAPLICADO += VALOR

    return VALORAPLICADO


def queryAplicacoesSonho(nome):
    """
    RETORNA AS APLICACOES DE UM SONHO ESPECIFICO
    """

    CURSOR.execute(f"SELECT total(valor), strftime('%m/%Y', data) as periodo FROM aplicacoes WHERE nome = '{nome}' GROUP BY periodo ORDER BY periodo")
    valores = []
    periodos = []
    acumulado = 0
    for row in CURSOR.fetchall():
        acumulado +=row[0]
        valores.append(acumulado)
        periodos.append(row[1])
        
    return (valores, periodos)
    
    

def queryPoupancaCards():
    """
    RETORNA OS CARDS PARA A PAGINA DE SONHOS
    """

    CURSOR.execute("SELECT nome, meta, obs, status FROM sonhos WHERE status = 'ABERTO'")
    cards = {c[0].replace(" ", "_"): {"meta": c[1], "obs": c[2], "status": c[3]} for c in CURSOR.fetchall()}
    for c in cards:
        nome = c.replace("_", " ")
        CURSOR.execute(f"SELECT total(valor) FROM aplicacoes WHERE nome = '{nome}'")
        valor = CURSOR.fetchall()[0][0] if c[0] else 0
        cards[c]["aplicado"] = valor

    return cards


def queryUmSonho(nome):
    """
    RETORNA AS INFORMACOES DO SONHO SELECIONADO
    """
    CURSOR.execute(f"SELECT id, nome, meta, obs, status FROM sonhos WHERE nome = '{nome}'")
    infos = {card[0]: {"nome": card[1], "meta": card[2], "obs": card[3], "status": card[4]} for card in CURSOR.fetchall()}

    return infos


def adicionaCategoria(categoria):
    """
    ADICIONA A CATEGORIA NA TABELA CATEGORIAS
    """
    if categoria in [None, "", " "]:
        flash(f"Erro ao adicionar a categoria '{categoria}' à lista.")
        return False
    else:
        CURSOR.execute(f"INSERT INTO categorias (categoria) VALUES (?)", (categoria,))
        DB.commit()
        flash(f"Categoria '{categoria}' adicionada com sucesso.")
        return True


def deletaCategoria(categoria):
    """
    DELETA A CATEGORIA DA TABELA CATEGORIAS
    """
    if categoria in [None, "", " "]:
        flash(f"Erro ao remover a categoria '{categoria}' da lista.")
        return False
    else:
        CURSOR.execute(f"DELETE FROM categorias WHERE categoria = '{categoria}'")
        DB.commit()
        flash(f"Categoria '{categoria}' removida com sucesso.")
        return True


def adicionaModal(modal):
    """
    ADICIONA MODAL NA TABELA MODAIS
    """
    if modal in [None, "", " "]:
        flash(f"Erro ao adicionar o modal '{modal}' à lista.")
        return False
    else:
        CURSOR.execute(f"INSERT INTO modais (modal) VALUES (?)", (modal,))
        DB.commit()
        flash(f"Modal '{modal}' adicionado com sucesso.")
        return True


def deletaModal(modal):
    """
    DELETA MODAL DA TABELA MODAIS
    """
    if modal in [None, "", " "]:
        flash(f"Erro ao remover o modal '{modal}' da lista.")
        return False
    else:
        CURSOR.execute(f"DELETE FROM modais WHERE modal = '{modal}'")
        DB.commit()
        flash(f"Modal '{modal}' removido com sucesso.")
        return True


def adicionaGasto(valor, categoria, modal, data, obs):
    """
    ADEQUA E ADICIONA UM GASTO NOVO NA TABELA GASTOS
    """
    VALOR = valor
    CATEGORIA = categoria
    MODAL = modal
    DATA = data
    OBS = obs
    try:
        VALOR = float(valor)
        if OBS in [None, "", " "]:
            OBS = ""

        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{DATA} {HORA}"

        CURSOR.execute(
            f"INSERT INTO gastos (valor, categoria, modal, data, obs) VALUES (?, ?, ?, ?, ?)",
            (
                VALOR,
                CATEGORIA,
                MODAL,
                DATA,
                OBS,
            ),
        )
        DB.commit()
        flash(f"Novo gasto inserido na tabela com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao inserir novo gasto na tabela: '{e}'")
        return False


def deletaGasto(id):
    """
    DELETA O GASTO SELECIONADO DA TABELA GASTOS
    """
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


def editaGasto(id, valor, categoria, modal, data, obs):
    """
    EDITA O GASTO SELECIONADO
    """

    try:
        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{data} {HORA}"
        CURSOR.execute(f"UPDATE gastos SET valor = {valor}, categoria = '{categoria}', modal = '{modal}', data = '{DATA}', obs = '{obs}' WHERE id = {id}")
        DB.commit()
        flash(f"Gasto editado com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao editar gasto: '{e}'")
        return False


def adicionaRenda(valor, categoria, data, obs):
    """
    ADEQUA E ADICIONA UMA RENDA NOVA NA TABELA RENDAS
    """
    VALOR = valor
    CATEGORIA = categoria
    DATA = data
    OBS = obs
    try:
        VALOR = float(valor)
        if OBS in [None, "", " "]:
            OBS = ""

        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{DATA} {HORA}"

        CURSOR.execute(
            f"INSERT INTO renda (valor, categoria, data, obs) VALUES (?, ?, ?, ?)",
            (
                VALOR,
                CATEGORIA,
                DATA,
                OBS,
            ),
        )
        DB.commit()
        flash(f"Nova renda inserida na tabela com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao inserir nova renda na tabela: '{e}'")
        return False


def deletaRenda(id):
    """
    DELETA A RENDA SELECIONADA DA TABELA RENDAS
    """
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


def editaRenda(id, valor, categoria, data, obs):
    """
    EDITA A RENDA SELECIONADO
    """

    try:
        HORA = datetime.now().strftime("%H:%M:%S")
        DATA = f"{data} {HORA}"
        CURSOR.execute(f"UPDATE renda SET valor = {valor}, categoria = '{categoria}', data = '{DATA}', obs = '{obs}' WHERE id = {id}")
        DB.commit()
        flash(f"Renda editada com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao editar renda: '{e}'")
        return False


def exporta_gastos():
    memoria = StringIO()
    CSV = csv.writer(memoria)
    CURSOR.execute("SELECT * FROM gastos")
    valores = CURSOR.fetchall()
    CSV.writerow([i[0] for i in CURSOR.description])
    CSV.writerows(valores)

    resposta = make_response(memoria.getvalue())
    resposta.headers["Content-Disposition"] = "attachment; filename=Gastos.csv"
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
    resposta.headers["Content-Disposition"] = "attachment; filename=Renda.csv"
    resposta.headers["Content-type"] = "text/csv"

    return resposta


def adiciona_sonho(nome, meta, obs, status):
    """
    ADEQUA E ADICIONA UM SONHO NOVO NA TABELA SONHOS
    """
    NOME = nome
    META = meta
    OBS = obs
    STATUS = status
    try:
        META = float(META)
        if OBS in [None, "", " "]:
            OBS = ""

        CURSOR.execute(
            f"INSERT INTO sonhos (nome, meta, obs, status) VALUES (?, ?, ?, ?)",
            (
                NOME,
                META,
                OBS,
                STATUS,
            ),
        )
        DB.commit()
        flash(f"Novo sonho adicionado com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao inserir novo sonho: '{e}'")
        return False


def aplica_sonho(nome, valor):
    """
    ADEQUA E ADICIONA UMA APLICACAO A UM SONHO NA TABELA APLICACOES
    """
    NOME = nome
    VALOR = valor
    DATA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    DISPONIVEL = queryPoupaca() - queryAplicacoes()
    try:
        VALOR = float(VALOR)
        if VALOR > DISPONIVEL:
            flash(f"Erro ao aplicar em {NOME}: você não possui saldo suficiente.")
            return False
        else:
            CURSOR.execute(
                f"INSERT INTO aplicacoes (nome, valor, data) VALUES (?, ?, ?)",
                (
                    NOME,
                    VALOR,
                    DATA,
                ),
            )
            DB.commit()
            flash(f"R${VALOR} aplicado a {NOME} com sucesso.")
            return True

    except Exception as e:
        print(e)
        flash(f"Erro ao aplicar em {NOME}: '{e}'")
        return False


def exclui_sonho(nome):
    """
    MARCA UM SONHO NA TABELA SONHOS COMO EXCLUIDO
    """

    NOME = nome

    try:
        CURSOR.execute(f"UPDATE sonhos SET status = 'EXCLUIDO' WHERE nome = '{NOME}'")
        DB.commit()
        flash(f"{NOME} excluído com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao excluir {NOME}: '{e}'")
        return False


def conclui_sonho(nome):
    """
    MARCA UM SONHO NA TABELA SONHOS COMO CONCLUIDO
    """

    NOME = nome

    try:
        CURSOR.execute(f"UPDATE sonhos SET status = 'CONCLUIDO' WHERE nome = '{NOME}'")
        DB.commit()
        flash(f"{NOME} concluído com sucesso.")
        return True

    except Exception as e:
        print(e)
        flash(f"Erro ao concluir {NOME}: '{e}'")
        return False


def editaSonho(id, nome, meta, obs):
    """
    EDITA O SONHO SELECIONADO
    """

    ID = id
    NOME_NOVO = nome
    META_NOVA = meta
    OBS_NOVA = obs

    CURSOR.execute(f"SELECT nome FROM sonhos WHERE id = {ID}")

    NOME_ANTIGO = CURSOR.fetchall()[0][0]

    try:
        CURSOR.execute(f"UPDATE sonhos SET nome = '{NOME_NOVO}', meta = {META_NOVA}, obs = '{OBS_NOVA}' WHERE id = '{ID}'")
        CURSOR.execute(f"UPDATE aplicacoes SET nome = '{NOME_NOVO}' WHERE nome = '{NOME_ANTIGO}'")
        DB.commit()
        flash(f"Edição concluída com sucesso.")

    except Exception as e:
        print(e)
        flash(f"Erro ao editar {NOME_ANTIGO}: '{e}'")
        return False


@APP.route("/")
def index():
    """
    RETORNA A PAGINA PRINCIPAL QUE CONTEM APENAS O MENU LATERAL
    """
    return render_template("index.html")


@APP.errorhandler(404)
def erro404(e):
    """
    RETORNA PARA A PAGINA RESUMO EM CASO DE PAGINA NAO ENCONTRADA
    """
    return redirect(url_for("index"))


@APP.route("/resumo")
def resumo():
    """
    RETORNA A PAGINA RESUMO COM TODOS OS DADOS NECESSARIOS
    """
    gastostotal = queryGastos()
    gastostotalmes = queryGastosMesAtual()
    gastodia = queryGastosPorDiaNoMes()
    rendatotal = queryRenda()
    rendatotalmes = queryRendaMesAtual()
    rendadia = queryRendaPorDiaNoMes()
    saldo = querySaldo()

    return render_template("resumo.html", gastos=gastostotal, renda=rendatotal, gastomes=gastostotalmes, rendames=rendatotalmes, gastodia=gastodia, rendadia=rendadia, saldo=saldo)


@APP.route("/gastos", methods=["GET", "POST"])
def gastos():
    """
    RETORNA A PAGINA GASTOS COM TODOS OS DADOS NECESSARIOS
    """
    categorias = listaCategorias()
    modais = listaModais()
    gastos = queryGastos()
    categoriasGraficoGastosPorCat = queryGastosPorCategoria()
    gastospormes = queryGastosPorMes()

    return render_template("gastos.html", categorias=categorias, modais=modais, gastos=gastos, catsGrafGpC=categoriasGraficoGastosPorCat, GrafGpM=gastospormes)


@APP.route("/gastos_add", methods=["POST"])
def gastos_add():
    """
    PROCESSA O FORMULARIO DE ADICAO DE GASTO E ATUALIZA A PAGINA GASTOS
    """
    valor = request.form["valor"]
    categoria = request.form["categoria"]
    modal = request.form["modal"]
    data = request.form["data"]
    obs = request.form["obs"]
    adicionaGasto(valor, categoria, modal, data, obs)

    return redirect(url_for("gastos"))


@APP.route("/gastos_del", methods=["POST"])
def gastos_del():
    """
    PROCESSA O FORMULARIO DE EXCLUSAO DE GASTO E ATUALIZA A PAGINA GASTOS
    """
    ID = request.form["ID"]
    deletaGasto(ID)

    return redirect(url_for("gastos"))


@APP.route("/gastos_edit", methods=["POST"])
def gastos_edit():
    """
    APRESENTA A PAGINA DE EDICAO PARA O ID SELECIONADO
    """
    ID = request.form["ID"]
    VALORES = queryGastoUnico(ID)
    categorias = listaCategorias()
    modais = listaModais()

    return render_template("gastos_edit.html", valores=VALORES, categorias=categorias, modais=modais)


@APP.route("/save_gasto_edit", methods=["POST"])
def save_gasto_edit():
    """
    ENVIA A EDICAO PARA O BANCO E RETORNA PARA A PAGINA GASTOS
    """

    id = request.form["id"]
    valor = request.form["valor"]
    categoria = request.form["categoria"]
    modal = request.form["modal"]
    data = request.form["data"]
    obs = request.form["obs"]
    editaGasto(id, valor, categoria, modal, data, obs)

    return redirect(url_for("gastos"))


@APP.route("/renda", methods=["GET", "POST"])
def renda():
    """
    RETORNA A PAGINA RENDA COM TODOS OS DADOS NECESSARIOS
    """

    categorias = listaCategorias()
    rendas = queryRenda()
    categoriasGraficoRendaPorCat = queryRendaPorCategoria()
    rendapormes = queryRendaPorMes()

    return render_template("renda.html", categorias=categorias, rendas=rendas, catsGrafRpC=categoriasGraficoRendaPorCat, GrafRpM=rendapormes)


@APP.route("/renda_add", methods=["POST"])
def renda_add():
    """
    PROCESSA O FORMULARIO DE ADICAO DE RENDA E ATUALIZA A PAGINA RENDA
    """
    valor = request.form["valor"]
    categoria = request.form["categoria"]
    data = request.form["data"]
    obs = request.form["obs"]
    adicionaRenda(valor, categoria, data, obs)

    return redirect(url_for("renda"))


@APP.route("/renda_del", methods=["POST"])
def renda_del():
    """
    PROCESSA O FORMULARIO DE EXCLUSAO DE RENDA E ATUALIZA A PAGINA RENDA
    """
    ID = request.form["ID"]
    deletaRenda(ID)

    return redirect(url_for("renda"))


@APP.route("/renda_edit", methods=["POST"])
def renda_edit():
    """
    APRESENTA A PAGINA DE EDICAO PARA O ID SELECIONADO
    """
    ID = request.form["ID"]
    VALORES = queryRendaUnica(ID)
    categorias = listaCategorias()

    return render_template("renda_edit.html", valores=VALORES, categorias=categorias)


@APP.route("/save_renda_edit", methods=["POST"])
def save_renda_edit():
    """
    ENVIA A EDICAO PARA O BANCO E RETORNA PARA A PAGINA RENDA
    """

    id = request.form["id"]
    valor = request.form["valor"]
    categoria = request.form["categoria"]
    data = request.form["data"]
    obs = request.form["obs"]
    editaRenda(id, valor, categoria, data, obs)

    return redirect(url_for("renda"))


@APP.route("/sonhos", methods=["GET", "POST"])
def sonhos():
    """
    RETORNA A PAGINA SONHOS COM TODOS OS DADOS NECESSARIOS
    """

    poupanca = queryPoupaca()
    aplicacoes = queryAplicacoes()
    aplicacaodisponivel = poupanca - aplicacoes
    cards = queryPoupancaCards()

    return render_template("sonhos.html", poupanca=poupanca, cards=cards, aplicacaodisponivel=aplicacaodisponivel)


@APP.route("/sonhos_add", methods=["GET", "POST"])
def sonhos_add():
    """
    PROCESSA O FORMULARIO DE ADICAO DE SONHO E ATUALIZA A PAGINA SONHOS
    """
    NOME = request.form["nome"]
    META = request.form["meta"]
    OBS = request.form["obs"]
    STATUS = "ABERTO"

    adiciona_sonho(NOME, META, OBS, STATUS)

    return redirect(url_for("sonhos"))


@APP.route("/sonhos_del", methods=["GET", "POST"])
def sonhos_del():
    """
    PROCESSA O FORMULARIO DE EXCLUSAO DE SONHO E ATUALIZA A PAGINA SONHOS
    """
    NOME = request.form["nome"].replace("_", " ")
    exclui_sonho(NOME)

    return redirect(url_for("sonhos"))


@APP.route("/aplica_sonhos", methods=["GET", "POST"])
def aplica_sonhos():
    """
    PROCESSA O FORMULARIO DE APLICACAO DE SONHO E ATUALIZA A PAGINA SONHOS
    """
    NOME = request.form["nome"].replace("_", " ")
    VALOR = request.form["valor"]

    aplica_sonho(NOME, VALOR)

    return redirect(url_for("sonhos"))


@APP.route("/conclui_sonhos", methods=["GET", "POST"])
def conclui_sonhos():
    """
    PROCESSA O FORMULARIO DE CONCLUSAO DE SONHO E ATUALIZA A PAGINA SONHOS
    """
    NOME = request.form["nome"].replace("_", " ")
    conclui_sonho(NOME)

    return redirect(url_for("sonhos"))


@APP.route("/edita_sonhos", methods=["POST"])
def edita_sonhos():
    """
    APRESENTA A PAGINA DE EDICAO DE SONHO PARA O SONHO SELECIONADO
    """
    NOME = request.form["nome"].replace("_", " ")
    INFOS = queryUmSonho(NOME)

    return render_template("sonhos_edit.html", infos=INFOS)


@APP.route("/save_sonho_edit", methods=["POST"])
def save_sonho_edit():
    """
    ENVIA A EDICAO PARA O BANCO E RETORNA PARA A PAGINA SONHOS
    """

    id = request.form["id"]
    nome = request.form["nome"]
    meta = request.form["meta"]
    obs = request.form["obs"]
    editaSonho(id, nome, meta, obs)

    return redirect(url_for("sonhos"))


@APP.route("/abre_grafico_sonhos", methods=["POST"])
def abre_grafico_sonhos():
    """
    ENVIA A EDICAO PARA O BANCO E RETORNA PARA A PAGINA SONHOS
    """

    NOME = request.form["nome"].replace("_", " ")
    INFOS = queryAplicacoesSonho(NOME)
    VALORES = INFOS[0]
    PERIODOS = INFOS[1]

    return render_template("sonhos_grafico.html", valores=VALORES, periodos=PERIODOS, nome=NOME)


@APP.route("/config", methods=["GET", "POST"])
def config():
    """
    RETORNA A PAGINA DE CONFIGURACOES COM TODOS OS DADOS NECESSARIOS
    """
    categorias = listaCategorias()
    modais = listaModais()

    return render_template("config.html", categorias=categorias, modais=modais)


@APP.route("/config_add_categoria", methods=["POST"])
def config_add_categoria():
    """
    PROCESSA O FORMULARIO DE ADICAO DE CATEGORIA E ATUALIZA A PAGINA CONFIGURACOES
    """
    categoria = request.form["add_categoria"]
    adicionaCategoria(categoria)

    return redirect(url_for("config"))


@APP.route("/config_del_categoria", methods=["POST"])
def config_del_categoria():
    """
    PROCESSA O FORMULARIO DE EXCLUSAO DE CATEGORIA E ATUALIZA A PAGINA CONFIGURACOES
    """
    categoria = request.form["del_categoria"]
    deletaCategoria(categoria)

    return redirect(url_for("config"))


@APP.route("/config_add_modal", methods=["POST"])
def config_add_modal():
    """
    PROCESSA O FORMULARIO DE ADICAO DE MODAL E ATUALIZA A PAGINA CONFIGURACOES
    """
    modal = request.form["add_modal"]
    adicionaModal(modal)

    return redirect(url_for("config"))


@APP.route("/config_del_modal", methods=["POST"])
def config_del_modal():
    """
    PROCESSA O FORMULARIO DE EXCLUSAO DE MODAL E ATUALIZA A PAGINA CONFIGURACOES
    """
    modal = request.form["del_modal"]
    deletaModal(modal)

    return redirect(url_for("config"))


@APP.route("/exportar_gastos", methods=["GET"])
def config_exportar_gastos():
    """
    ENVIA O CSV DA TABELA DE GASTOS
    """
    resposta = exporta_gastos()

    return resposta


@APP.route("/exportar_renda", methods=["GET"])
def config_exportar_renda():
    """
    ENVIA O CSV DA TABELA DE RENDA
    """
    resposta = exporta_renda()

    return resposta


@APP.route("/info")
def info():
    """
    RETORNA A PAGINA INFORMACOES COM TODOS OS DADOS NECESSARIOS
    """

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
    # webbrowser.open('http://localhost:8080', new=2)
    # serve(APP, host='0.0.0.0', port=8080)
    APP.run(host="0.0.0.0", port=8080, debug=True)
