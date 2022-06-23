##############################################################################
#
#               THIS FILE IS INTENDED TO TEST QUERIES
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

cursor.execute(f"SELECT strftime('%m', data) as mes, sum(valor) FROM gastos WHERE strftime('%Y', data) = '{ANO}' GROUP BY mes ORDER BY mes")
for data in cursor.fetchall():
    print(data)