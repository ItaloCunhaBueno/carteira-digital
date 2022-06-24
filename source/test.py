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

cursor.execute("UPDATE gastos SET valor = 1.11, categoria = 'Italo', modal = 'Débito', data = '2022-06-23 22:17:07', obs = 'Teste 2' WHERE id = 91")
db.commit()
print('OK')