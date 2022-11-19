# please install oracledb and sshtunnel, input below 2 lines in termial
# pip install oracledb
# pip install sshtunnel

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


def run(compUserID="", compPassword=""):
    """Main program, the first and second parameter is the studentId and password for loging in to comp intranet """
    initLogger()
    successSSHLogin = initSSHTunnel(compUserID, compPassword)
    if (successSSHLogin):
        # initDatabase()
        userID = input("Welcome to Library management system, \nPlease input your userID: ")
        password = input("Please input your password: ")
        isAdminUser, vaildPassword, userStatus = checkCurrentUser(userID, password)

        if (not isAdminUser and not vaildPassword and not userStatus):
            print("User not exist!")
        else:
            if vaildPassword:
                if isAdminUser:
                    var = input("""Welcome admin, plese enter your option\n1 for search books, 2 for checking records, 3 for initialize Database, 4 for Change book fees/ expiry period, q for quit: """)
                    while var != "q":
                        if (var == "1"):
                            searchBy = input(
                                "plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                            if (searchBy == "1"):
                                searchByTitle()
                            elif (searchBy == "2"):
                                searchByAuthor()
                            elif (searchBy == "3"):
                                searchByCategory()
                        elif (var == "2"):
                            checkBy = input("plese enter your check option\n(1 for check loan record, 2 for check reserve record, 3 for check book status):")
                            if (checkBy == "1"): 
                                query_Result = run_query("""select READERS.Name, LOAN_RECORDS.ISBN ,LOAN_RECORDS.Loan_date
                                                            from LOAN_RECORDS INNER JOIN READERS ON LOAN_RECORDS.READER_ID=READERS.READER_ID""")
                                print("Loan records:")
                                for row in query_Result:
                                    print("READER: ",row[0], 'Loan book:', row[1], ',at:', row[2])
                            elif (checkBy == "2"): 
                                query_Result = run_query("""select READERS.Name, RESERVE_RECORDS.ISBN ,RESERVE_RECORDS.Reserve_date
                                                            from RESERVE_RECORDS INNER JOIN READERS ON RESERVE_RECORDS.READER_ID=READERS.READER_ID""")
                                print("Reserve records:")
                                for row in query_Result:
                                    print("READER_ID: ",row[0], 'reserve book:', row[1], ',at', row[2])
                            elif (checkBy == "3"): 
                                ISBN = input("Enter a ISBN of book to check it's current status in library:")
                                checkBookStatus(ISBN)
                        elif (var == "3"):
                            isInit = input("Warning! All current changes will be discard from database and database will restore to original version, are you sure? Y/N")
                            if (isInit == 'y' or isInit == 'Y'):
                                initDatabase()
                        elif (var == "4"):
                            ISBN = input("please input the ISBN of current book you to make changes: ")
                            checkBookStatus(ISBN)
                            fee = input("please input the new book fee: ")
                            expiryPeriod = input("please input the new expiry period: ")
                            updateBookStatus(ISBN, fee, expiryPeriod)
                        else:
                            print("Invaild input!")
                        var = input("""plese enter your your option\n1 for search books, 2 for checking records, 3 for initialize Database, 4 for Change book fees/ expiry period, q for quit: """)
                else:
                    if userStatus == False:
                        print("Your account is deactivated since you have not return your expired book(s) listed:")
                        loanedBooks = getLoanedBooks(userID)
                        print("Please return the book(s) and pay the expire fee in-person to reactivate your account!")
                    else:
                        name = run_query("select name from READERS where READER_ID=\'" + userID + "\'")
                        print("Welcome:", str(name[0]).strip(",()'"))
                        loanedBooks = getLoanedBooks(userID)
                        getReservedBooks(userID)
                        var = input(
                            "plese enter your option\n(1 for search books, 2 for return books, 3 for loan book, 4 for reserve books, q for quit):")
                        while var != "q":
                            if (var == "1"):
                                searchBy = input(
                                    "plese enter your search option\n(1 for search by title, 2 for search by Author, 3 for search by Category):")
                                if (searchBy == "1"):
                                    searchByTitle()
                                elif (searchBy == "2"):
                                    searchByAuthor()
                                elif (searchBy == "3"):
                                    searchByCategory()
                            elif (var == "2"):
                                if len(loanedBooks) > 0:
                                    ISBN = input("Enter the book ISBN you want to return: ")
                                    isVaildISBN = False
                                    for row in loanedBooks:
                                        if ISBN == row[3]:
                                            isVaildISBN = True
                                            break
                                    if isVaildISBN:
                                        run_query(
                                            """delete from LOAN_RECORDS where ISBN=\'""" + ISBN + """\' and READER_ID=\'""" + userID + """\'""",
                                            False)
                                        loanedBooks = getLoanedBooks(userID)
                                    else:
                                        print("You input ISBN is not vaild/ you did not load that book")
                                else:
                                    print("You don't have loaned books!")
                            elif (var == "3"):
                                if len(loanedBooks) <= 6:
                                    ISBN = input("Enter the book ISBN you want to loan: ")
                                    isReserved = False
                                    reservedBooks = getReservedBooks(userID)  # if it is Reserved by current user, remove the reserve record
                                    for row in reservedBooks:
                                        if ISBN in row[3]:
                                            isReserved = True
                                            break
                                    if isReserved:
                                        run_query(
                                            """delete from RESERVE_RECORDS where ISBN=\'""" + ISBN + """\' and READER_ID=\'""" + userID + """\'""",
                                            False)

                                    if getHoldings(ISBN) > 0:
                                        today = date.today().strftime("%m/%d/%Y")
                                        run_query(
                                            "insert into LOAN_RECORDS values (\'" + userID + "\', " + ISBN + ", TO_DATE(\'" + today + "\', 'MM/DD/YYYY'))", False)
                                        print("Loan success!")
                                        loanedBooks = getLoanedBooks(userID)
                                    else:
                                        isReserve = input("The library holding of selected book is currently out of stock, do you want to reserve it?Y/N")
                                        if isReserve =='Y' or isReserve =='y':
                                            reserveBook(ISBN, userID)
                                else:
                                    print("your loan quota is exceeded!")
                            elif (var == "4"):
                                if len(loanedBooks) <= 6:
                                    ISBN = input("Enter the book ISBN you want to reserve: ")
                                    reserveBook(ISBN, userID)
                                else:
                                    print("your reserve quota is exceeded!")
                            else:
                                print("Invaild input!")
                            var = input(
                                "plese enter your option\n(1 for search books, 2 for retrun books, 3 for loan book, 4 for reserve books, q for quit):")
            else:
                print("Your LMS username/password is not correct, please try again")
    else:
        print("Your comp intranet username/password is not correct, cannot connect to department server")

def reserveBook(ISBN, userID):
    today = date.today().strftime("%m/%d/%Y")
    run_query(
        "insert into RESERVE_RECORDS values (\'" + userID + "\', " + ISBN + ", TO_DATE(\'" + today + "\', 'MM/DD/YYYY'))", False)
    print("Reserve success!")
    getReservedBooks(userID)

def updateBookStatus(ISBN, fee, expiryPeriod):
    """Make use of the UPDATE sql keyword to update the attribute value in table RECORD_SYSTEM"""
    print("Updating...")
    run_query("""UPDATE RECORD_SYSTEM
                 SET Daily_Charge=\'""" + fee +"""\', Expire_Period=\'""" + expiryPeriod +"""\'
                 WHERE ISBN=\'""" + ISBN +"""\' """, False)
    checkBookStatus(ISBN)

def checkBookStatus(ISBN):
    """Check the book status with the given ISBN """
    status = run_query("""select BOOKS.ISBN, BOOKS.Title, RECORD_SYSTEM.Expire_Period, RECORD_SYSTEM.Daily_Charge
                            from BOOKS INNER JOIN RECORD_SYSTEM ON BOOKS.ISBN=RECORD_SYSTEM.ISBN 
                            where RECORD_SYSTEM.ISBN=\'""" + ISBN +"""\' """)
    holdings = getHoldings(ISBN)
    if len(status) > 0:
        print("the status of current book is:")
        for row in status:
            print("ISBN:",row[0]," Title:", row[1], " Expire_Period:",row[2] , " Daily_Charge:",row[3]," Holdings:", holdings )

def updateBookStatus(ISBN, fee, expiryPeriod):
    """Make use of the UPDATE sql keyword to update the attribute value in table RECORD_SYSTEM"""
    print("Updating...")
    run_query("""UPDATE RECORD_SYSTEM
                 SET Daily_Charge=\'""" + fee +"""\', Expire_Period=\'""" + expiryPeriod +"""\'
                 WHERE ISBN=\'""" + ISBN +"""\' """, False)
    checkBookStatus(ISBN)

def checkBookStatus(ISBN):
    """Check the book status with the given ISBN """
    status = run_query("""select BOOKS.ISBN, BOOKS.Title, RECORD_SYSTEM.Expire_Period, RECORD_SYSTEM.Daily_Charge
                            from BOOKS INNER JOIN RECORD_SYSTEM ON BOOKS.ISBN=RECORD_SYSTEM.ISBN 
                            where RECORD_SYSTEM.ISBN=\'""" + ISBN +"""\' """)
    holdings = getHoldings(ISBN)
    if len(status) > 0:
        print("the status of current book is:")
        for row in status:
            print("ISBN:",row[0]," Title:", row[1], " Expire_Period:",row[2] , " Daily_Charge:",row[3]," Holdings:", holdings )

def getReservedBooks(userID):
    """get the books reserved by current user (userID), it will display the record if (show) is true """
    reservedBooks = run_query("""select BOOKS.Title, RESERVE_RECORDS.Reserve_date, RECORD_SYSTEM.Expire_Period, BOOKS.ISBN
                                from RESERVE_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=RESERVE_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                where READER_ID=\'""" + userID + "\'")
    if len(reservedBooks) > 0:
        print("Your reserved book(s):")
        for row in reservedBooks:
            expireDay = row[1].date() + timedelta(days=int(row[2]))
            print("ISBN:", row[3], "Title:", row[0], " reserve period ends at:", str(expireDay))
            checkBookStatus(row[3])
    else:
        print("You don't have books reserved")
    return reservedBooks


def getLoanedBooks(userID, show=True):
    """get the books loaned by current user (userID), it will display the record if (show) is true """
    loanedBooks = run_query("""select BOOKS.Title, LOAN_RECORDS.Loan_date, RECORD_SYSTEM.Expire_Period, BOOKS.ISBN, RECORD_SYSTEM.Daily_Charge
                                from LOAN_RECORDS INNER JOIN BOOKS ON BOOKS.ISBN=LOAN_RECORDS.ISBN INNER JOIN RECORD_SYSTEM ON RECORD_SYSTEM.ISBN=BOOKS.ISBN
                                where READER_ID=\'""" + userID + "\'")
    if show:
        if len(loanedBooks) > 0:
            print("Your loaned book(s):")
            for row in loanedBooks:
                expireDay = row[1].date() + timedelta(days=int(row[2]))
                today = date.today()
                diff = today - expireDay
                expirefee = float(row[4]) * int(diff.days)
                if diff.days <= 0:
                    print("ISBN:", row[3], "Title:", row[0], "will expire at:", str(expireDay))
                else:
                    print("ISBN:", row[3], "Title:", row[0], "expired at:", str(expireDay), "Expire fee:",
                          str(expirefee))
        else:
            print("you don't have loaned books")
    return loanedBooks

def getHoldings(ISBN):
    """Return a number of books hold by the library (not loaned out)"""
    holdings = run_query("""select Holdings from RECORD_SYSTEM where ISBN=\'""" + ISBN + """\' """)
    if len(holdings) == 0:
        return -1  # book not exist (not holded by the library)
    loaned = run_query("""select count(*) from LOAN_RECORDS where ISBN=\'""" + ISBN + """\' """)
    holdingsNum = str(holdings[0]).strip(",()'")
    loanedNum = str(loaned[0]).strip(",()'")
    return (int(holdingsNum[0]) - int(loanedNum[0]))


def searchByTitle():
    """Search book by title"""
    title = input("plese enter the title to search: ")
    searchBooks(title, 1)


def searchByAuthor():
    """Search book by Author"""
    Author = input("plese enter the Author to search: ")
    searchBooks(Author, 2)


def searchByCategory():
    """Search book by Category"""
    data = run_query("select distinct Category from books")
    print("Listed Categories in libary system: ")
    for row in data:
        print(row[0])
    Categories = input("plese enter the Categories to search: ")
    searchBooks(Categories, 3)


def searchBooks(para, type):
    """Search book function to search book by the user input and search type (1:title, 2: author, 3: category) """
    print("Searching, please wait...")
    if type == 1:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Title) like LOWER(\'%""" + para + """%\') """)  # lower for case insensitive compare
    elif type == 2:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Author) like LOWER(\'%""" + para + """%\') """)
    else:
        data = run_query("""select ISBN, Title, Author, Category from books 
                            where LOWER(Category) like LOWER(\'%""" + para + """%\') """)
    if len(data) > 0:
        for row in data:
            print("ISBN:", row[0], "Title:", row[1], "Author:", row[2], "Category:", row[3])
    else:
        print("No match books where found!")


def checkCurrentUser(userID, password):
    """ Check the LMS user is a admin/ reader and is he exist in the database/ password is correct.
    Also deactivate a patron's account if he/she does not return books after a specific period of time passes."""
    print("logining in...")
    isAdmin = True
    vaildPassword = True
    userStatus = True
    query_Result = run_query("select LIBRARIAN_ID, password from LIBRARIANS where LIBRARIAN_ID=\'" + userID + "\'")
    if len(query_Result) > 0:
        for row in query_Result:
            if (row[0] == userID):
                if row[1] == password:
                    return isAdmin, vaildPassword, userStatus
                else:
                    vaildPassword = False
                    return isAdmin, vaildPassword, userStatus

    isAdmin = False
    query_Result = run_query("select READER_ID, password from READERS where READER_ID=\'" + userID + "\'")
    if len(query_Result) > 0:
        for row in query_Result:
            if (row[0] == userID):
                if row[1] == password:
                    query_Result = run_query("""select LOAN_RECORDS.READER_ID, LOAN_RECORDS.Loan_date, LOAN_RECORDS.ISBN, RECORD_SYSTEM.Expire_Period 
                                                from LOAN_RECORDS INNER JOIN RECORD_SYSTEM ON LOAN_RECORDS.ISBN=RECORD_SYSTEM.ISBN
                                                where READER_ID=\'""" + userID + "\'")
                    for row in query_Result:
                        if (row[0] == userID):
                            today = date.today()
                            diff = today - row[1].date()
                            strMaxDate = str(row[3]).strip(",()")
                            if diff.days > int(strMaxDate):
                                userStatus = False
                    return isAdmin, vaildPassword, userStatus
                else:
                    vaildPassword = False
                    return isAdmin, vaildPassword, userStatus
    return False, False, False


def initLogger():
    """Create a logger and log file named with today's day + connectionLog.txt """
    today = date.today()
    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    logging.basicConfig(filename=f'Logs/{today.strftime("%d%m%y") + "connectionLog.txt"}',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    logging.getLogger('SSHClient').info("The logger is initialized")
    logging.getLogger("paramiko").setLevel(logging.WARNING)


def initSSHTunnel(compUserID, compPassword):
    """Initialize the ssh tunnel with credentials of current user, 
        it will return false if the connection of ssh tunnel to department server fails.
        a major reason is username / password of comp intranet is not correct/ network problem. """
    global ssh_user
    ssh_user = compUserID
    global ssh_pw
    ssh_pw = compPassword
    print("Logging in to department server...")
    try:
        with tunnel() as _:
            with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("select * from books")
                    book = cursor.fetchone()
                    logging.getLogger('SSHClient').info("Testing query result is:" + str(book))
            return True
    except Exception as err:
        logging.getLogger('SSHClient').info("init SSH error: " + str(err))
        return False


def initDatabase():
    """Create sample table and data for testing and demo use"""
    print("initializating...\n")
    tableNames = ["BOOKS", "PUBLISHERS", "LIBRARIANS", "READERS", "LOAN_RECORDS", "RESERVE_RECORDS", "RECORD_SYSTEM"]
    createQuerys = [
        """create table BOOKS (ISBN VARCHAR(13) not null, Title VARCHAR(50), Author VARCHAR(50), Category VARCHAR(30), Price NUMBER(4, 1), PUBLISHER_ID VARCHAR(4) not null)""",
        """create table PUBLISHERS (PUBLISHER_ID VARCHAR(3) not null, Name VARCHAR(30))""",
        """create table LIBRARIANS (LIBRARIAN_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30))""",
        """create table READERS (READER_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30), email VARCHAR(50))""",
        """create table LOAN_RECORDS (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Loan_date DATE)""",
        """create table RESERVE_RECORDS  (READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Reserve_date DATE)""",
        """create table RECORD_SYSTEM (ISBN VARCHAR(13) not null, Holdings NUMBER(2) not null, Expire_Period NUMBER(2), Daily_Charge NUMBER(3, 2))"""]
    books = [
        # ISBN VARCHAR(13) not null, Title VARCHAR(50), Author VARCHAR(50), Category VARCHAR(30), Price NUMBER(4, 1), PUBLISHER_ID VARCHAR(4) not null
        ('9781784975692', 'The paper menagerie', 'Ken Liu', 'short-story', 89.9, '001'),
        ('9781800240346', 'The Grace of Kings', 'Ken Liu', 'short-story', 96.3, '001'),
        ('9780134583006', 'C++ How to Program', 'Paul Deitel', 'textbook', 173.2, '002'),
        ('9780130402646', 'Database System Implementation', 'Hector Garcia-Molina', 'textbook', 140.9, '003'),
        ('9780367184568',
         'How learning happens : educational psychology',
         'P Kirschner & C Hendrick', 'Non-fiction', 263, '003'),
        ('9780312425074', 'The world is flat', 'Thomas Friedman', 'Non-fiction', 388, '002'),
        ('0393975428', 'Jane Eyre', 'Charlotte Brontë', 'Fiction', 100, '001'),
        ('0521223407', 'Macbeth', 'William Shakespeare', 'Drama', 106, '002'),
        ('0521827957', 'Othello', 'William Shakespeare', 'Drama', 106, '002'),
        ('9782013235006', 'Les Misérable', 'Victor Hugo', 'Fiction', 398, '002')
    ]
    publishers = [
        # PUBLISHER_ID VARCHAR(3) not null, Name VARCHAR(30)
        ('001', 'Head of Zeus press'),
        ('002', 'Pearson'),
        ('003', 'Prentice Hall')
    ]
    librarians = [
        # LIBRARIAN_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30)
        ('samAdmin', 'Sam', 'pw1'),
        ('Holly', 'Holly', 'pw4'),
        ('21081251d', 'Tong', 'pw5')
    ]
    readers = [
        # READER_ID VARCHAR(9) not null, Name VARCHAR(30), Password VARCHAR(30), email VARCHAR(50)
        ('samReader', 'Sam', 'pw1', '21089537d@connect.polyu.hk'),
        ('AnyaYA', 'Anya', 'pw2', '21094526d@connect.polyu.hk'),
        ('21106945d', 'Anshu', 'pw3', '21106945d@connect.polyu.hk'),
        ('21096414d', 'Holly', 'pw4', '21096414d@connect.polyu.hk')
    ]
    loan_records = [
        # READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Loan_date DATE
        ('samReader', '9780130402646', date(2022, 10, 15)),
        ('AnyaYA', '9781784975692', date(2022, 11, 23)),
        ('AnyaYA', '9781800240346', date(2022, 12, 13)),
        ('AnyaYA', '0393975428', date(2022, 12, 13)),
        ('AnyaYA', '9782013235006', date(2022, 12, 13)),
        ('AnyaYA', '9780134583006', date(2022, 12, 13)),
        ('21106945d', '9781784975692', date(2022, 10, 23))
    ]
    reserve_records = [
        # READER_ID VARCHAR(9) not null, ISBN VARCHAR(13) not null, Reserve_date DATE
        ('21106945d', '9781800240346', date(2022, 11, 13))
    ]
    record_system = [
        # ISBN VARCHAR(13) not null, Holdings NUMBER(2) not null, Expire_Period NUMBER(2), Daily_Charge NUMBER(3, 2)
        ('9781784975692', 5, 30, 1.5),
        ('9781800240346', 1, 14, 1.0),
        ('9780134583006', 2, 30, 2),
        ('9780130402646', 2, 30, 1.5),
        ('9780367184568', 5, 30, 1.5),
        ('9780312425074', 5, 30, 1.5),
        ('0393975428', 6, 30, 1.5),
        ('0521223407', 7, 30, 1.5),
        ('0521827957', 8, 30, 1.5),
        ('9782013235006', 3, 30, 1.5)
    ]

    for table in tableNames:
        query = "drop table " + table
        run_query(query, False)
    for query in createQuerys:
        run_query(query, False)

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


def run_query(query, returnQuery=True):
    """Run the input query, if returnQuery==True, it will return the query result of current query. e.g: query=(selcet * from emp) will return all elements from table emp
       If returnQuery==False, it will not return the query result. not return is decided for the insert/ delete/ update sql types """
    with tunnel() as _:
        try:
            with oracledb.connect(user=db_user, password=db_password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    connection.commit()
                    if returnQuery:
                        data = cursor.fetchall()
                        logging.getLogger('SSHClient').info(query + " result is:" + str(data))
                        return data

        except oracledb.Error as err:
            logging.getLogger('SSHClient').info("Query:", query, str(err))


if __name__ == '__main__':
    """Main function of the program, if running in terimal, it will take first argument as user id, 
        second argument as password for connecting to the department server via ssh"""
    from sys import argv

    if len(argv) == 3:
        run(compUserID=str(argv[1]), compPassword=str(argv[2]))
    else:
        compUserID = input("Please enter comp intranet id: ")
        compPassword = getpass("Please enter comp intranet password: ")
        run(compUserID, compPassword)
