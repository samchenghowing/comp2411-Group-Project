# install Oracle clients
#pip install cx_Oracle
#https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html
#https://stackoverflow.com/questions/56119490/cx-oracle-error-dpi-1047-cannot-locate-a-64-bit-oracle-client-library

# install ssh clients
#pip install paramiko
#pip install sshtunnel
#https://medium.com/@cueball45/connecting-to-oracle-rds-using-python-d019436025d4
#https://sshtunnel.readthedocs.io/en/latest/

from datetime import date
import sys, logging
import cx_Oracle
from sshtunnel import SSHTunnelForwarder

# SSH config
ssh_host = "csdoor.comp.polyu.edu.hk"
ssh_user = ""
ssh_pw = ""
ssh_port = 22
local_port = 3000  # any random value

# DB config
sid = 'DBMS'
dsn = cx_Oracle.makedsn("127.0.0.1", local_port, sid=sid)
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
    data = run_query("select * from emp")
    for row in data:
        print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    

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
    try:
        cx_Oracle.init_oracle_client(lib_dir=local_lib_dir)
        # https://intranet.comp.polyu.edu.hk/TechServices/TechnicalTips/122 (Connect Oracle via php when running on lab pc)
        # dsn_tns = "(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(Host = studora.comp.polyu.edu.hk)(Port = 1521))) (CONNECT_DATA = (SID=DBMS)))"
        # conn = cx_Oracle.connect(db_user=r'"21089537d"@dbms', db_password='xisbpecl', dsn=dsn_tns) 
        conn = cx_Oracle.connect(db_user, db_password, dsn)
        logging.getLogger('SSHClient').info(str(conn) + "Connection successful")
        cursor = conn.cursor()
        cursor.execute(query)
        logging.getLogger('SSHClient').info(query + "Query executed succesfully,")
        data = cursor.fetchall()
        conn.close()
        logging.getLogger('SSHClient').info("\nquery result is:\n" + str(data))
        return data
    except Exception as err:
        logging.getLogger('SSHClient').info("Error connecting: cx_Oracle.init_oracle_client()" + str(err))
        sys.exit(1)

if __name__ == '__main__':
    """Main function of the program, if running in terimal, it will take first argument as user name, 
        second argument as password for connecting to the department server via ssh"""
    from sys import argv
    
    if len(argv) == 3:
        run(username=str(argv[1]), password=str(argv[2]))
    else:
        print ("Please enter your comp intranet id and pw!")