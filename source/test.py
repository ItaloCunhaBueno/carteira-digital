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
cursor.execute(f"SELECT strftime('%d', data) AS dia, round(total(valor),2) AS soma FROM gastos WHERE strftime('%Y-%m', data) = '{ANO}-{MES}' and categoria = 'Poupança' GROUP BY dia ORDER BY dia")

for row in cursor.fetchall():
    print(row)

