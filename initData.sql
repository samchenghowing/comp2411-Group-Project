DROP TABLE BOOK;
DROP TABLE LIBARY_HOLDINGS;
DROP TABLE PUBLISHER;
DROP TABLE STUDENT;
CREATE TABLE BOOK (ISBN CHAR(10) NOT NULL UNIQUE, BOOK_NAME CHAR(20) NOT NULL, AUTHORS CHAR(20), CATEGORY CHAR(20), PUBLISHER_ID CHAR(20));
CREATE TABLE LIBARY_HOLDINGS (ISBN CHAR(10) NOT NULL, STOCK_NUMBER NUMBER(10), LOANED NUMBER(10), RESERVED NUMBER(10), EXPIRE_DAY NUMBER(2));
CREATE TABLE PUBLISHER (ISBN CHAR(10) NOT NULL, PUBLISHER_ID CHAR(20) NOT NULL, PUBLISHER_NAME CHAR(4));
CREATE TABLE STUDENT (STUDENT_ID CHAR(10) NOT NULL UNIQUE, LOAN_ISBN CHAR(10));
