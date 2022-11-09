#please install oracledb and sshtunnel, input below 2 lines in termial
#pip install oracledb
#pip install sshtunnel

from datetime import date, timedelta
from getpass import getpass
import logging
import os
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
    # initDatabase() #uncomment this function for first time use (testing only). 
    isAdminUser, userStatus = checkCurrentUser(userID)
    
    if isAdminUser:
        var = input("""Welcome admin, plese enter your option\n1 for search books, 2 for checking records, 3 for initialize Database, q for quit: """)
        while var != "q":
            if (var == "1"):
                searchBy = input("plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                if (searchBy == "1"): searchByTitle()
                elif (searchBy == "2"): searchByAuthor()
                elif (searchBy == "3"): searchByCategory()
            elif (var == "2"):
                #3 Records of books checked out as well as placed on hold
                #TO-DO change the code to a fuction
                query_Result = run_query("select * from LOAN_RECORDS")
                print("Loan records:")
                for row in query_Result:
                    print("READER_ID: ",row[0], ',data', row[1])

                query_Result = run_query("select * from RESERVE_RECORDS")
                print("Reserve records:")
                for row in query_Result:
                    print("READER_ID: ",row[0], ',data', row[1])
                
                #TO-DO display the number of books on hold by library
            elif (var == "3"):
                isInit = input("Warning! All current changes will be discard from database and database will restore to original version, are you sure? Y/N")
                if (isInit == 'y' or isInit == 'Y'):
                    initDatabase()
            else:
                print("Invaild input!")
            var = input("""plese enter your your option\n1 for search books, 2 for checking records, 3 for initialize Database, q for quit: """)
    else:
        if userStatus == False:
            #2 Deactivate a patron’s account if he/she does not return books after a specific period of time passes
            print("Your account is deactivated since you have not return your expired book(s) listed:")
            loanedBooks = run_query("""select BOOKS.Title, LOAN_RECORDS.Loan_date, RECORD_SYSTEM.Expire_Period, BOOKS.ISBN, RECORD_SYSTEM.Daily_Charge
                                        from LOAN_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=LOAN_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                        where READER_ID=\'""" + userID +"\'")
            for row in loanedBooks:
                expireDay = row[1].date() + timedelta(days=int(row[2]))
                today = date.today()
                diff = today - expireDay
                expirefee = float(row[4]) * int(diff.days)
                print("ISBN:",row[3],"Title:", row[0], ", expire at:", str(expireDay), "Expire fee:", str(expirefee))
            print("Please return the book(s) and pay the expire fee in-person to reactivate your account!")
        else:
            name = run_query("select name from READERS where READER_ID=\'" + userID +"\'")
            print("Welcome:", str(name[0]).strip(",()'"))
            loanedBooks = run_query("""select BOOKS.Title, LOAN_RECORDS.Loan_date, RECORD_SYSTEM.Expire_Period, BOOKS.ISBN 
                                from LOAN_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=LOAN_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                where READER_ID=\'""" + userID +"\'")
            if len(loanedBooks) > 0:
                print("Your loaned book(s) will be expired at:")
                for row in loanedBooks:
                    expireDay = row[1].date() + timedelta(days=int(row[2]))
                    print("ISBN:",row[3],"Title:", row[0], ", expire at:",str(expireDay))

            var = input("plese enter your option\n(1 for search books, 2 for return books, 3 for loan book, 4 for reserve books, q for quit):")
            while var != "q":
                if (var == "1"):
                    searchBy = input("plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                    if (searchBy == "1"): searchByTitle()
                    elif (searchBy == "2"): searchByAuthor()
                    elif (searchBy == "3"): searchByCategory()
                elif (var == "2"):
                    if len(loanedBooks) > 0:
                        print("Your loaned book(s):")
                        for row in loanedBooks:
                            expireDay = row[1].date() + timedelta(days=int(row[2]))
                            print("ISBN:",row[3],"Title:", row[0], ", expire at:",str(expireDay))

                        ISBN = input("Enter the book ISBN you want to return: ")
                        isVaildISBN = False
                        for row in loanedBooks:
                            if ISBN == row[3]:
                                isVaildISBN = True
                                break
                        #TO-DO add else, if is not vaild ISBN (not loaned by the user)
                        if isVaildISBN:
                            run_query("""delete from LOAN_RECORDS where ISBN=\'""" + ISBN +"""\' """)
                            query_Result = run_query("select * from LOAN_RECORDS where READER_ID=\'" +userID +"\'")
                            print("Your loaned book(s):")
                            loanedBooks = run_query("""select BOOKS.Title, LOAN_RECORDS.Loan_date, RECORD_SYSTEM.Expire_Period, BOOKS.ISBN 
                                                        from LOAN_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=LOAN_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                                        where READER_ID=\'""" + userID +"\'")
                            for row in loanedBooks:
                                expireDay = row[1].date() + timedelta(days=int(row[2]))
                                print("ISBN:",row[3],"Title:", row[0], ", expire at:",str(expireDay))
                        else:
                            print("You input ISBN is not vaild/ you did not load that book")
                    else:
                        print("You don't have loaned books!")
                elif (var == "3"):
                    if len(loanedBooks) <= 6:
                        ISBN = input("Enter the book ISBN you want to loan: ")
                        #TO-DO (Optional) check is loan/reserved first to make sure user will not occupy more than one same book,
                        #TO-DO check the book is holded by the library first, (is ISBN vaild?)
                        holdings = run_query("""select Holdings
                                            from RECORD_SYSTEM
                                            where ISBN=\'""" + ISBN +"""\' """)
                        loaned = run_query("""select count(*)
                                            from LOAN_RECORDS
                                            where ISBN=\'""" + ISBN +"""\' """)
                        holdingsNum = str(holdings[0]).strip(",()'")
                        loanedNum = str(loaned[0]).strip(",()'")
                        availableBooks = int(holdingsNum[0]) - int(loanedNum[0])
                        if availableBooks > 0:
                            today = date.today().strftime("%m/%d/%Y")
                            run_query("insert into LOAN_RECORDS values (\'" + userID + "\', " + ISBN + ", TO_DATE(\'" + today + "\', 'MM/DD/YYYY'))")
                            print("Loan success!, Your current loan books are:")
                            query_Result = run_query("select * from LOAN_RECORDS where READER_ID=\'" +userID +"\'")
                            for row in query_Result:
                                print ("READER_ID: ",row[0], ', ISBN:', row[1], ", reserved date:" , row[2])
                        else:
                            print("The library holding of selected book is currently out of stock, please check again later.")
                    else:
                        print("your loan quota is exceeded!")
                elif (var == "4"):
                    if len(loanedBooks) <= 6:
                        ISBN = input("Enter the book ISBN you want to reserve: ")
                        #TO-DO (Optional) check is loan/reserved first to make sure user will not occupy more than one same book
                        holdings = run_query("""select Holdings
                                            from RECORD_SYSTEM
                                            where ISBN=\'""" + ISBN +"""\' """)
                        loaned = run_query("""select count(*)
                                            from LOAN_RECORDS
                                            where ISBN=\'""" + ISBN +"""\' """)
                        holdingsNum = str(holdings[0]).strip(",()'")
                        loanedNum = str(loaned[0]).strip(",()'")
                        availableBooks = int(holdingsNum[0]) - int(loanedNum[0])
                        if availableBooks > 0:
                            today = date.today().strftime("%m/%d/%Y")
                            run_query("insert into RESERVE_RECORDS values (\'" + userID + "\', " + ISBN + ", TO_DATE(\'" + today + "\', 'MM/DD/YYYY'))")
                            print("Reserve success!, Your current reserved books are:")
                            query_Result = run_query("select * from RESERVE_RECORDS where READER_ID=\'" +userID +"\'")
                            for row in query_Result:
                                print ("READER_ID: ",row[0], ', ISBN:', row[1], ", reserved date:" , row[2])
                        else:
                            print("The library holding of selected book is currently out of stock, please check again later.")
                    else:
                        print("your reserve quota is exceeded!")
                else:
                    print("Invaild input!")
                var = input("plese enter your option\n(1 for search books, 2 for retrun books, 3 for loan book, 4 for reserve books, q for quit):")

def searchByTitle():
    title = input("plese enter the title to search: ")
    searchBooks(title, 1)

def searchByAuthor():
    Author = input("plese enter the Author to search: ")
    searchBooks(Author, 2)

def searchByCategory():
    data = run_query("select distinct Category from books")
    print ("Listed Categories in libary system: ")
    for row in data:
        print(row[0])
    Categories = input("plese enter the Categories to search: ")
    searchBooks(Categories, 3)

def searchBooks(para, type):
    """Search book function to search book by the user input and search type (1:title, 2: author, 3: category) """
    print("Searching, please wait...")
    if type == 1:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Title) like LOWER(\'%""" + para + """%\') """) #lower for case insensitive compare 
    elif type == 2:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Author) like LOWER(\'%""" + para + """%\') """) 
    else:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Category) like LOWER(\'%""" + para + """%\') """) 
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

    isAdmin = False
    query_Result = run_query("""select LOAN_RECORDS.READER_ID, LOAN_RECORDS.Loan_date, LOAN_RECORDS.ISBN, RECORD_SYSTEM.Expire_Period 
                                from LOAN_RECORDS INNER JOIN RECORD_SYSTEM ON LOAN_RECORDS.ISBN=RECORD_SYSTEM.ISBN""")
    for row in query_Result:
        if (row[0] == userID):
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
    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    logging.basicConfig(filename=f'Logs/{today.strftime("%d%m%y")+"connectionLog.txt"}',
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
    #TO-DO add more data
    print("initializating...\n")
    tableNames = ["BOOKS", "PUBLISHERS", "LIBRARIANS", "READERS", "LOAN_RECORDS", "RESERVE_RECORDS", "RECORD_SYSTEM"]
    createQuerys = ["""create table BOOKS (ISBN VARCHAR(13) not null, Title VARCHAR(50), Author VARCHAR(50), Category VARCHAR(30), Price NUMBER(4, 1), PUBLISHER_ID VARCHAR(4) not null)""", 
                    """create table PUBLISHERS (PUBLISHER_ID VARCHAR(3) not null, Name VARCHAR(30))""", 
                    """create table LIBRARIANS (LIBRARIAN_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30))""",
                    """create table READERS (READER_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30), email VARCHAR(50))""",
                    """create table LOAN_RECORDS (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Loan_date DATE)""",
                    """create table RESERVE_RECORDS  (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Reserve_date DATE)""",
                    """create table RECORD_SYSTEM (ISBN VARCHAR(13) not null, Holdings NUMBER(2) not null, Expire_Period NUMBER(2), Daily_Charge NUMBER(3, 2))"""]
    books = [
        ('9781784975692', 'The paper menagerie', 'Ken Liu', 'short-story', 89.9, '001'),
        ('9781800240346', 'The Grace of Kings', 'Ken Liu', 'short-story', 96.3, '001'),
        ('9780134583006', 'C++ How to Program', 'Paul Deitel', 'textbook', 173.2, '002'),
        ('9780130402646', 'Database System Implementation', 'Hector Garcia-Molina', 'textbook', 140.9, '003')
    ]
    publishers = [
        ('001', 'Head of Zeus press'),
        ('002', 'Pearson'),
        ('003', 'Prentice Hall')
    ]
    librarians = [
        # ('21089537d', 'Sam', 'pw1'),
        ('21096414d', 'Holly', 'pw4'),
        ('21081251d', 'Tong', 'pw5')
    ]
    readers = [
        ('21089537d', 'Sam', 'pw1', '21094526d@connect.polyu.hk'),
        ('21094526d', 'Anya', 'pw2', '21094526d@connect.polyu.hk'),
        ('21106945d', 'Anshu', 'pw3', '21106945d@connect.polyu.hk')
        #, ('21096414d', 'Holly', 'pw4', '21096414d@connect.polyu.hk')
    ]
    loan_records = [
        ('21089537d', '9780130402646', date(2022, 9, 15)),
        ('21094526d', '9781784975692', date(2022, 10, 23)),
        ('21106945d', '9781800240346', date(2022, 10, 13)),
        ('21106945d', '9781784975692', date(2022, 10, 23))
    ]
    reserve_records = [
        ('21106945d', '9781800240346', date(2010, 10, 13))
    ]
    record_system = [
        ('9781784975692', 5, 30, 1.5),
        ('9781800240346', 1, 14, 1.0),
        ('9780134583006', 2, 30, 2),
        ('9780130402646', 2, 30, 1.5)
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
    #TO-DO (optional) check SQL injection in query=(selcet * from emp where username=(update/ insert/ delete ...))
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
