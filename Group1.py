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
    """Main program, the first and second parameter is your studentId and password for loging in to comp intranet """
    initLogger()
    initSSHTunnel(username, password)
    initDatabase()
    isAdminUser, userStatus = checkCurrentUser(username)
    
    if isAdminUser:
        var = input("Welcome admin, plese enter your checking option\n(1 for checked-out records,2 for reserved records, 3 for book holdings, q for quit):")
        while var != "q":
            if (var == "1"):
                query_Result = run_query("select * from RESERVE_RECORDS")
                for row in query_Result:
                    print ("RESERVE_RECORD_ID: ",row[0], ',data', row[1])
            elif (var == "2"):
                query_Result = run_query("select * from LOAN_RECORDS")
                for row in query_Result:
                    print ("RESERVE_RECORD_ID: ",row[0], ',data', row[1])
            elif (var == "3"):
                query_Result = run_query("select * from RECORD_SYSTEM")
                for row in query_Result:
                    print ("RESERVE_RECORD_ID: ",row[0], ',data', row[1])
            else:
                print("Invaild input!")
            var = input("plese enter your checking option\n(1 for checked-out records,2 for reserved records, 3 for book holdings, q for quit):")

        #3 Records of books checked out as well as placed on hold (i.e. “reserved” by a patron to make sure the book is there when he/she gets to the library to check it out).
    else:
        if userStatus == False:
            print("Your account is deactivated since you have expired books: ")
            #2 The ability to deactivate a patron’s account if he/she does not return books after a specific period of time passes
        else:
            print("Welcome: ")
            #4 Notifications when the desired book becomes available and reminders that a book should be returned to the library. Both could be sent by email and/or when patron logs in to the LMS.


    def searchByTitle(Title):
        #TO-DO please update this function
        data = run_query("select * from book where Title=" + Title)
        for row in data:
            print ("ISBN: ",row[0], ', -', row[1])

    def searchByAuthor(Author):
        #TO-DO please update this function
        data = run_query("select * from book where Author Name=" + Author)
        for row in data:
            print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    

    def searchByCategory(bookName):
        #TO-DO please update this function
        data = run_query("select * from book where bookname=" + bookName)
        for row in data:
            print (row[0], '-', row[1]) # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.    

def checkCurrentUser(userName):
    # Deactivate a patron’s account if he/she does not return books after a specific period of time passes.
    isAdmin = False
    userStatus = True
    # query_Result = run_query("select * from LIBRARIANS")
    query_Result = run_query("select LIBRARIAN_ID, password from LIBRARIANS")
    for row in query_Result:
        # print("LIBRARIAN_ID: ",row[0], ', name: ', row[1] ,', password: ', row[2])
        print("LIBRARIAN_ID:",row[0], ', password:', row[1])
        if (row[0] == userName):
            isAdmin = True
            return isAdmin, userStatus

    query_Result = run_query("select READERS.READER_ID, LOAN_RECORDS.LoanDate from READERS INNER JOIN LOAN_RECORDS ON LOAN_RECORDS.READER_ID=LOAN_RECORDS.READER_ID")
    for row in query_Result:
        if (row[0] == userName):
            return isAdmin, userStatus
    
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
    logging.getLogger("paramiko").setLevel(logging.WARNING)

def initSSHTunnel(username, password):
    """Initialize the ssh tunnel with credentials of current user"""
    global ssh_user
    ssh_user = username
    global ssh_pw
    ssh_pw = password
    logging.getLogger('SSHClient').info("Currnent user is " + ssh_user)
        
def initDatabase():
    """Create sample table and data for testing and demo use"""
    tableNames = ["BOOKS", "PUBLISHERS", "LIBRARIANS", "READERS", "LOAN_RECORDS", "RESERVE_RECORDS", "RECORD_SYSTEM"]
    createQuerys = ["""create table BOOKS (ISBN VARCHAR(13) not null, Title VARCHAR(30), Author VARCHAR(30), Category VARCHAR(30), Price NUMBER(3, 1), PUBLISHER_ID VARCHAR(3) not null)""", 
                    """create table PUBLISHERS (PUBLISHER_ID VARCHAR(3) not null, Name VARCHAR(30))""", 
                    """create table LIBRARIANS (LIBRARIAN_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30))""",
                    """create table READERS (READER_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30), email VARCHAR(50))""",
                    """create table LOAN_RECORDS (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Loan_date DATE)""",
                    """create table RESERVE_RECORDS  (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Reserve_date DATE)""",
                    """create table RECORD_SYSTEM (ISBN VARCHAR(13) not null, Holdings NUMBER(2) not null, Expire_Period NUMBER(2), Daily_Charge NUMBER(3, 2))"""]
    books = [
        ('9781784975692', 'The paper menagerie', 'Ken Liu', 'short-story', 89.9, '001'),
        ('9781800240346', 'The Grace of Kings', 'Ken Liu', 'short-story', 96.3, '001')
    ]
    publishers = [
        ('001', 'Head of Zeus press'),
        ('002', 'I love polyu')
    ]
    librarians = [
        ('21089537d', 'Sam', 'pw1'),
    ]
    readers = [
        ('12345678d', 'Reader1', 'pw2', '12345678d@connect.polyu.hk')
    ]
    loan_records = [
        ('12345678d', '9781784975692', date(2022, 10, 23))
    ]
    reserve_records = [
        ('12345678d', '9781800240346', date(2010, 10, 13))
    ]
    record_system = [
        ('9781784975692', 5, 30, 1.5),
        ('9781800240346', 1, 14, 1.0)
    ]
    with tunnel() as _:
        for table in tableNames:
            try:
                with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                    with connection.cursor() as cursor:
                        query = "drop table " + table
                        cursor.execute(query)
                        connection.commit()        
            except oracledb.Error as err:
                logging.getLogger('SSHClient').info("Error while deleting " + table + ": " + str(err))
        
        for query in createQuerys:
            try:
                with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        connection.commit()        
            except oracledb.Error as err:
                logging.getLogger('SSHClient').info("Error: " + query + ": " + str(err))
        
        try:
            with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.executemany("insert into BOOKS values (:1, :2, :3, :4, :5, :6)", books)
                    cursor.executemany("insert into PUBLISHERS values (:1, :2)", publishers)
                    cursor.executemany("insert into LIBRARIANS values (:1, :2, :3)", librarians)
                    cursor.executemany("insert into READERS values (:1, :2, :3, :4)", readers)
                    cursor.executemany("insert into LOAN_RECORDS values (:1, :2, :3)", loan_records)
                    cursor.executemany("insert into RESERVE_RECORDS values (:1, :2, :3)", reserve_records)
                    cursor.executemany("insert into RECORD_SYSTEM values (:1, :2, :3, :4)", record_system)
                    connection.commit()        
                    logging.getLogger('SSHClient').info("Database initize success")    
        except oracledb.Error as err:
            logging.getLogger('SSHClient').info("Error: " + str(err))

def tunnel():
    """SSH Tunnel for connecting to polyu comp intranet"""
    return SSHTunnelForwarder(
        ssh_host,
        ssh_username=ssh_user,
        ssh_password=ssh_pw,
        remote_bind_address=(db_host, db_port),
        local_bind_address=('0.0.0.0', local_port)
    )

def run_query(query):
    """Return a query list of current query. e.g: query=(selcet * from emp) will return all elements from table emp"""
    with tunnel() as _:
        logging.getLogger('SSHClient').info("run_query, query is: " + query)
        try:
            with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    connection.commit()
                    data = cursor.fetchall()
                    logging.getLogger('SSHClient').info(query + " result is:" + str(data))
                    return data
                    
        except oracledb.Error as err:
            print(str(err))
            logging.getLogger('SSHClient').info("Error query: " + str(err))

def run_queryList(querys):
    """Testing use only"""
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

def runSQLfile(fileName):
    """Testing use only"""
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