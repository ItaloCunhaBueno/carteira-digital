##############################################################################
#
#               ESTE ARQUIVO SERVE APENAS PARA TESTAR QUERIES
#
#
##############################################################################

import sqlite3
from pathlib import Path
from datetime import datetime
from pprint import pprint

HOMEDIR = Path(__file__).parent.absolute()
db = sqlite3.connect(f"{HOMEDIR}/banco/carteira.db")
CURSOR = db.cursor()

ANO = str(datetime.now().year)
CURSOR.execute(f"SELECT strftime('%m', data) AS mes, strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM gastos WHERE NOT categoria = 'Poupança' AND strftime('%Y', data) = '{ANO}' GROUP BY mes, dia ORDER BY mes, dia")
gastos = CURSOR.fetchall()
gastosmeses = {}
for g in gastos:
    mes = int(g[0])
    dia = int(g[1])
    valor = int(g[2])
    if mes not in gastosmeses:
        gastosmeses[mes] = {}
    if dia not in gastosmeses[mes]:
        gastosmeses[mes][dia] = valor
    
for mes in range(1, 13):
    valorAcumulado = 0
    for dia in range(1, 32):
        if mes not in gastosmeses:
            gastosmeses[mes] = {}
        if dia not in gastosmeses[mes]:
            gastosmeses[mes][dia] = valorAcumulado
        else:
            valorAcumulado += gastosmeses[mes][dia]
            gastosmeses[mes][dia] = valorAcumulado

gastosmeses = {mes:sorted([(str(dia), gastosmeses[mes][dia]) for dia in gastosmeses[mes]]) for mes in gastosmeses}
pprint(gastosmeses)