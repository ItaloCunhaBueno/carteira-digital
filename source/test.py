##############################################################################
#
#               ESTE ARQUIVO SERVE APENAS PARA TESTAR QUERIES
#
#
##############################################################################

import sqlite3
from pathlib import Path
from datetime import datetime

ANO = str(datetime.now().year)
MES = str(datetime.now().month).zfill(2)
HOMEDIR = Path(__file__).parent.absolute()
db = sqlite3.connect(f"{HOMEDIR}/banco/carteira.db")
cursor = db.cursor()
nome = 'Roupas Novas'
cursor.execute(f"SELECT total(valor), strftime('%m/%Y', data) as periodo FROM aplicacoes WHERE nome = '{nome}' GROUP BY periodo ORDER BY periodo")

valores = []
periodos = []
for row in cursor.fetchall():
    valores.append(row[0])
    periodos.append(row[1])

print(valores)
print(periodos)
