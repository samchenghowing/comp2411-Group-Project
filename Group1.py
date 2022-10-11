# install Oracle and ssh clients
#pip install cx_Oracle
#pip install sshtunnel

from datetime import date
import sys, logging
import cx_Oracle
from sshtunnel import SSHTunnelForwarder

# SSH config
ssh_host = "csdoor.comp.polyu.edu.hk"
ssh_user = ""
ssh_pw = ""
ssh_port = 22
local_ip = "127.0.0.1"
local_port = 3000

# DB config
db_sid = 'DBMS'
dsn = cx_Oracle.makedsn(local_ip, local_port, sid=db_sid)
db_host = "studora.comp.polyu.edu.hk"
db_port = 1521
db_user = r'"21089537d"'
db_password = 'xisbpecl'

#local oracle-client-library location:
local_lib_dir = r"/Users/howingcheng/Downloads/instantclient_19_8"

def run(username="21089537d", password=""):
    """Main program"""
    initLogger()
    initSSHTunnel(username, password)
    logging.getLogger('SSHClient').info("Currnent user is " + ssh_user)
    runSQLfile("initData.sql")

    # data = run_query("select * from emp")
    # for row in data:
    #     print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    


def initLogger():
    """Create a logger and log file named with today's day + connectionLog.txt """ 
    today = date.today()
    logging.basicConfig(filename=(today.strftime("%d%m%y")+"connectionLog.txt"),
                                filemode='a',
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)
    logging.getLogger('SSHClient').info("The logger is initialized")

def initSSHTunnel(username, password):
    global ssh_user
    ssh_user = username
    global ssh_pw
    ssh_pw = password
    cx_Oracle.init_oracle_client(lib_dir=local_lib_dir)
        
def tunnel():
  return SSHTunnelForwarder(
    ssh_host,
    ssh_username=ssh_user,
    ssh_password=ssh_pw,
    remote_bind_address=(db_host, db_port),
    local_bind_address=('0.0.0.0', local_port)
  )

def run_query(query):
  with tunnel() as _:
    logging.getLogger('SSHClient').info("run_query, query is: " + query)
    try:
        with cx_Oracle.connect(db_user, db_password, dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()
                data = cursor.fetchall()
                print(data)
                logging.getLogger('SSHClient').info(query + " result is:" + str(data))
                
    except cx_Oracle.Error as err:
        print(str(err))
        logging.getLogger('SSHClient').info("Error query: " + str(err))
        # sys.exit(1)

def run_queryList(querys):
  with tunnel() as _:
    logging.getLogger('SSHClient').info("run_queryList, querys are: " + str(querys))
    try:
        with cx_Oracle.connect(db_user, db_password, dsn) as connection:
            with connection.cursor() as cursor:
                for query in querys:
                    currQuery = query.strip('\n')
                    cursor.execute(currQuery)
                    data = cursor.fetchall()
                    print(data)
                    logging.getLogger('SSHClient').info(currQuery + " result is:" + str(data))
                connection.commit()
                
    except cx_Oracle.Error as err:
        print(str(err))
        logging.getLogger('SSHClient').info("Error query: " + str(err))
        # sys.exit(1)

def runSQLfile(fileName):
    f = open(fileName)
    full_sql = f.read()
    sql_commands = full_sql.split(';')
    run_queryList(sql_commands)
    
if __name__ == '__main__':
    """Main function of the program, if running in terimal, it will take first argument as user name, 
        second argument as password for connecting to the department server via ssh"""
    from sys import argv
    
    if len(argv) == 3:
        run(username=str(argv[1]), password=str(argv[2]))
    else:
        print ("Please enter your comp intranet id and pw!")