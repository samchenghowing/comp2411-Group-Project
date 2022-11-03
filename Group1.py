#please install oracledb and sshtunnel, input below 2 lines in termial
#pip install oracledb
#pip install sshtunnel

from datetime import date, timedelta
from getpass import getpass
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

# DB config, please also change db_user and db_password to use your own orcale Database for testing
db_sid = 'DBMS'
dsn = oracledb.makedsn(local_ip, local_port, sid=db_sid)
db_host = "studora.comp.polyu.edu.hk"
db_port = 1521
db_user = r'"21089537d"'
db_password = 'xisbpecl'

def run(userID="", password=""):
    """Main program, the first and second parameter is your studentId and password for loging in to comp intranet """
    initLogger()
    initSSHTunnel(userID, password)
    isAdminUser, userStatus = checkCurrentUser(userID)
    # initDatabase() #uncomment this function for first time use. 
    
    if isAdminUser:
        var = input("""Welcome admin, plese enter your option\n1 for search books, 2 for checking records, 3 for initialize Database, q for quit: """)
        while var != "q":
            if (var == "1"):
                searchBy = input("plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                if (searchBy == "1"): searchByTitle()
                elif (searchBy == "2"): searchByAuthor()
                elif (searchBy == "3"): searchByCategory()
            elif (var == "2"):
                #3 Records of books checked out as well as placed on hold (i.e. “reserved” by a patron to make sure the book is there when he/she gets to the library to check it out).
                query_Result = run_query("select * from LOAN_RECORDS")
                for row in query_Result:
                    print ("READER_ID: ",row[0], ',data', row[1])
            elif (var == "3"):
                initDatabase()
            else:
                print("Invaild input!")
            var = input("""plese enter your your option\n1 for search books, 2 for checking records, 3 for initialize Database, q for quit: """)
    else:
        if userStatus == False:
            #2 The ability to deactivate a patron’s account if he/she does not return books after a specific period of time passes
            print("Your account is deactivated since you have not return your expired book(s) listed,\n enter book ISBN you want to return or enter q to quit: ")
        else:
            name = run_query("select name from READERS where READER_ID=\'" + userID +"\'")
            print("Welcome:", str(name[0]).strip(",()"))
            data = run_query("""select BOOKS.Title, LOAN_RECORDS.Loan_date, RECORD_SYSTEM.Expire_Period 
                                from LOAN_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=LOAN_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                where READER_ID=\'""" + userID +"\'")
            if len(data) > 0:
                print("Your loaned book(s) will be expired at:")
                for row in data:
                    expireDay = row[1].date() + timedelta(days=int(row[2]))
                    print(row[0], ", expire at:",str(expireDay))

            var = input("plese enter your option\n(1 for search books, 2 for retrun books, 3 for loan book, 4 for check loaned/reserved books, q for quit):")
            while var != "q":
                if (var == "1"):
                    searchBy = input("plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                    if (searchBy == "1"): searchByTitle()
                    elif (searchBy == "2"): searchByAuthor()
                    elif (searchBy == "3"): searchByCategory()
                elif (var == "1"):
                    if len(data) > 0:
                        print("Enter the book ISBN you want to return: ")
                        #TO-DO return books
                    else:
                        print("You don't have loaned books!")
                else:
                    print("Invaild input!")
                var = input("plese enter your option\n(1 for search books, 2 for retrun books, 3 for loan book, 4 for check loaned/reserved books, q for quit):")

def searchByTitle():
    title = input("plese enter the title to search: ")
    searchBooks(title)

def searchByAuthor():
    Author = input("plese enter the Author to search: ")
    searchBooks(Author)

def searchByCategory():
    data = run_query("select distinct Category from books")
    print ("Listed Categories in libary system: ")
    for row in data:
        print(row[0])
    Categories = input("plese enter the Categories to search: ")
    searchBooks(Categories)

def searchBooks(Title):
    data = run_query("""select ISBN, Title, Author, Category from books 
                        where LOWER(Title) like LOWER(\'%""" + Title + """%\') OR 
                        LOWER(Author) like LOWER(\'%""" + Title + """%\') OR 
                        LOWER(Category) like LOWER(\'%""" + Title + """%\') """) #lower for case insensitive compare 
    if len(data) > 0:
        for row in data:
            print("ISBN:",row[0], "Title:", row[1], "Author:", row[2], "Category:", row[3])
    else:
        print("No match books where found!")

def checkCurrentUser(userID):
    """ Deactivate a patron’s account if he/she does not return books after a specific period of time passes."""
    print("logining in...")
    isAdmin = True
    userStatus = True
    query_Result = run_query("select LIBRARIAN_ID, password from LIBRARIANS")
    for row in query_Result:
        if (row[0] == userID):
            return isAdmin, userStatus

    query_Result = run_query("""select LOAN_RECORDS.READER_ID, LOAN_RECORDS.Loan_date, LOAN_RECORDS.ISBN, RECORD_SYSTEM.Expire_Period 
                                from LOAN_RECORDS INNER JOIN RECORD_SYSTEM ON LOAN_RECORDS.ISBN=RECORD_SYSTEM.ISBN""")
    for row in query_Result:
        if (row[0] == userID):
            isAdmin = False
            today = date.today()
            diff = today - row[1].date()
            strMaxDate = str(row[3]).strip(",()")
            if diff.days > int(strMaxDate):
                userStatus = False 
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
    print("initializating...\n")
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
        ('21094526d', 'Anya', 'pw2'),
        ('21106945d', 'Anshu', 'pw3'),
        ('21096414d', 'Holly', 'pw4'),
        ('21081251D', 'Tong', 'pw5')
    ]
    readers = [
        ('21089537d', 'Sam', 'pw1', '21089537d@connect.polyu.hk'), #for my testing use
        ('12345678d', 'Reader1', 'pw2', '12345678d@connect.polyu.hk')
    ]
    loan_records = [
        ('21089537d', '9781784975692', date(2022, 10, 23)),
        ('21089537d', '9781800240346', date(2022, 10, 13)),
        ('12345678d', '9781784975692', date(2022, 10, 23))
    ]
    reserve_records = [
        ('12345678d', '9781800240346', date(2010, 10, 13))
    ]
    record_system = [
        ('9781784975692', 5, 30, 1.5),
        ('9781800240346', 1, 14, 1.0)
    ]

    for table in tableNames:
        query = "drop table " + table
        run_query(query)
    for query in createQuerys:
        run_query(query)

    with tunnel() as _:
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
                    print("Database initialization complete!")    
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
    """Return the query result of current query. e.g: query=(selcet * from emp) will return all elements from table emp"""
    with tunnel() as _:
        try:
            with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    connection.commit()
                    data = cursor.fetchall()
                    logging.getLogger('SSHClient').info(query + " result is:" + str(data))
                    return data
                    
        except oracledb.Error as err:
            logging.getLogger('SSHClient').info("Error query: " + query + str(err))

if __name__ == '__main__':
    """Main function of the program, if running in terimal, it will take first argument as user name, 
        second argument as password for connecting to the department server via ssh"""
    from sys import argv
    
    if len(argv) == 3:
        run(userID=str(argv[1]), password=str(argv[2]))
    else:
        userID = input("Please enter comp intranet id: ")
        password = getpass("Please enter comp intranet password: ")
        run(userID, password)