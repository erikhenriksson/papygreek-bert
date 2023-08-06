import MySQLdb
from dotenv import dotenv_values

class Db:
    def __init__(self, save=0):
        self.debug = 1 - save
        config = dotenv_values(".env")
        self.db = MySQLdb.connect(
            user=config['DB_USER'],
            passwd=config['DB_PASSWORD'],
            db=config['DB_NAME'],
        )
        self.db.autocommit(True)
        self.cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    def print_error(self, function, error, sql, params):
        print(f'Error in {function}: {error} \n Sql: {sql} \n Params: {params}')

    def close_exit(self, msg=None):
        if msg: print(f'Exit: {msg}')
        self.cursor.close()
        self.db.close()
        exit()

    def fetch_all(self, sql, params=None):
        try:
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except (MySQLdb.Error, MySQLdb.Warning) as error:
            self.print_error('fetch_all', error, sql, params)
            self.close_exit()

    def fetch_one(self, sql, params):
        try:
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()
        except (MySQLdb.Error, MySQLdb.Warning) as error:
            self.print_error('fetch_one', error, sql, params)
            self.close_exit()

    def fetch_first(self, sql, params):
        try:
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            if results:
                return results[0]
        except (MySQLdb.Error, MySQLdb.Warning) as error:
            self.print_error('fetch_first', error, sql, params)
            self.close_exit()

    def insert(self, sql, params):
        try:
            self.cursor.execute(sql, params)
            return self.cursor.lastrowid
        except (MySQLdb.Error, MySQLdb.Warning) as error:
            self.print_error('insert', error, sql, params)
            self.close_exit()

    def execute(self, sql, params):
        try:
            self.cursor.execute(sql, params)
        except (MySQLdb.Error, MySQLdb.Warning) as error:
            self.print_error('execute', error, sql, params)
            self.close_exit()

    def get_annotated_texts(self):
        return self.fetch_all('''
            SELECT * FROM text WHERE (orig_status > 0 OR reg_status > 0);
        ''')

    def get_db_text_tokens(self, text_id):
        return self.fetch_all('''
            SELECT * FROM token WHERE text_id=%s
            ORDER BY sentence_n, n
        ''', (text_id,))