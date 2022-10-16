#please install oracledb and sshtunnel, input below 2 lines in termial
#pip install oracledb
#pip install sshtunnel

from datetime import date
import logging
import oracledb
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
dsn = oracledb.makedsn(local_ip, local_port, sid=db_sid)
db_host = "studora.comp.polyu.edu.hk"
db_port = 1521
db_user = r'"21089537d"'
db_password = 'xisbpecl'

def run(username="21089537d", password=""):
    """Main program"""
    initLogger()
    initSSHTunnel(username, password)
    logging.getLogger('SSHClient').info("Currnent user is " + ssh_user)
    isAdminUser, userStatus = checkCurrentUser(username)
    if isAdminUser:
        run_query("select * from emp")
        #runSQLfile("initData.sql")
        #3 Records of books checked out as well as placed on hold (i.e. “reserved” by a patron to make sure the book is there when he/she gets to the library to check it out).
    else:
        if userStatus == False:
            print("Your account is deactivated since you have expired books: ")
            #2 The ability to deactivate a patron’s account if he/she does not return books after a specific period of time passes
        else:
            print("Welcome: ")
            #4 Notifications when the desired book becomes available and reminders that a book should be returned to the library. Both could be sent by email and/or when patron logs in to the LMS.


def searchByTitle(Title):
    #TO-DO please change this function
    data = run_query("select * from book where Title=" + Title)
    for row in data:
        # print ("ISBN: ",row[0], ', -', row[1])
        print (row)

def searchByAuthor(Author):
    #TO-DO please change this function
    data = run_query("select * from book where Author Name=" + Author)
    for row in data:
        print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    

def searchByCategory(bookName):
    #TO-DO please change this function
    data = run_query("select * from book where bookname=" + bookName)
    for row in data:
        print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    

def checkCurrentUser(userName):
    #TO-DO please change this function
    # Deactivate a patron’s account if he/she does not return books after a specific period of time passes.
    isAdmin = True
    userStatus = False
    return isAdmin, userStatus

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
        
def initDatabase():
    """Create dummy data for testing and demo use"""
    books = [
        ('9781784975692', '001', 'The paper menagerie', 'Ken Liu', 'short-story', 89.9),
    ]
    publisher = [
        ('001', 'Head of zeus'),
    ]
    librarian = [
        ('Jane', date(2005, 2, 12)),
    ]
    reader = [
        ('Joe', date(2006, 5, 23)),
        ('John', date(2010, 10, 3)),
    ]
    loan_record = [
        ('Joe', date(2006, 5, 23)),
    ]
    reserve_record = [
        ('John', date(2010, 10, 3)),
    ]
    record_system = [
        ('Joe', date(2006, 5, 23)),
        ('John', date(2010, 10, 3)),
    ]

    try:
        with cx_Oracle.connect(db_user, db_password, dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""begin
                                    execute immediate 'drop table books';
                                    exception when others then
                                    if sqlcode != -942 then
                                        raise;
                                    end if;
                                end;""")
                cursor.execute("""create table books (ISBN char(15) not null, PUBLISHER_ID char(3) not null, Title char(30), Author char(30), Category char(30), Price number(10))""")
                #TO_DO modify this function:
                # cursor.executemany("insert into BOOK(ISBN, data) values (:1, :2)", books, batcherrors = True)
                # cursor.executemany("insert into PUBLISHER(PUBLISHER_ID, data) values (:1, :2)", publisher, batcherrors = True)
                # cursor.executemany("insert into LIBRARIAN(LIBRARIAN_ID, data) values (:1, :2)", librarian, batcherrors = True)
                # cursor.executemany("insert into READER(READER_ID, data) values (:1, :2)", reader, batcherrors = True)
                # cursor.executemany("insert into LOAN_RECORD(LOAN_RECORD_ID, data) values (:1, :2)", loan_record, batcherrors = True)
                # cursor.executemany("insert into RESERVE_RECORD(RESERVE_RECORD_ID, data) values (:1, :2)", reserve_record, batcherrors = True)
                # cursor.executemany("insert into RECORD_SYSTEM(RECORD_SYSTEM, data) values (:1, :2)", record_system, batcherrors = True)
                connection.commit()        
                print("Database initize success")      
                for error in cursor.getbatcherrors():
                    print("Error", error.message.rstrip(), "at row offset", error.offset)

    except cx_Oracle.Error as err:
        print(str(err))
        logging.getLogger('SSHClient').info("Error query: " + str(err))
        # sys.exit(1)


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
        with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()
                data = cursor.fetchall()
                print(data)
                logging.getLogger('SSHClient').info(query + " result is:" + str(data))
                
    except oracledb.Error as err:
        print(str(err))
        logging.getLogger('SSHClient').info("Error query: " + str(err))
        # sys.exit(1)

def run_queryList(querys):
  with tunnel() as _:
    try:
        with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
            with connection.cursor() as cursor:
                for query in querys:
                    currQuery = query.strip('\n')
                    cursor.execute(currQuery)
                    data = cursor.fetchall()
                    logging.getLogger('SSHClient').info(currQuery + " execute result is:" + str(data))
                connection.commit()
                
    except oracledb.Error as err:
        print(str(err))
        logging.getLogger('SSHClient').info("Error query: " + str(err))
        # sys.exit(1)

def runSQLfile(fileName):
    f = open(fileName)
    full_sql = f.read()
    sql_commands = full_sql.split(';')
    if len(sql_commands) == 1:
        run_query(sql_commands[0])
    else:
        run_queryList(sql_commands)

if __name__ == '__main__':
    """Main function of the program, if running in terimal, it will take first argument as user name, 
        second argument as password for connecting to the department server via ssh"""
    from sys import argv
    
    if len(argv) == 3:
        run(username=str(argv[1]), password=str(argv[2]))
    else:
        print ("Please enter your comp intranet id and pw!")