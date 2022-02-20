from datetime import datetime
import psycopg2
import credentials

class save_to_db():
    def __init__(self, listOutput, table):
        self.listOutput = listOutput
        self.table = table
    def insert_data(self):
        columns = " "
        allKeys = list(self.listOutput[0].keys())
        columns = ', '.join([str(elem)  for elem in allKeys]) 
        values =  ', '.join(["%("+str(elem) + ")s" for elem in allKeys]) 
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        
        cursor = conn.cursor()
        postgreSQL_select_Query = "INSERT INTO "+ self.table + " (" + columns +") VALUES (" + values+ ");"
        cursor.executemany(postgreSQL_select_Query, self.listOutput)
        conn.commit()
        conn.close()
        print("commit at ", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))