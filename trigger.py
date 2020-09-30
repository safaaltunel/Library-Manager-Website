from flask import Flask, render_template, url_for, request, redirect
import sqlite3
from datetime import datetime


app = Flask(__name__)

def fourteenDaysLater(date):
	y = int(date[6:])
	m = int(date[3:5])
	d = int(date[0:2])
	if d <= 16:
		return datetime(y,m,d+14).strftime("%d-%m-%Y")
	elif m <= 11:
		newDay = (d+14)%30
		return datetime(y,m+1,newDay).strftime("%d-%m-%Y")
	else:
		return(y+1,1,(d+14)%30).strftime("%d-%m-%Y")


class Borrower():
	def __init__(self, tc_number, number_of_books_borrowed):
		self.tc_number = tc_number
		self.number_of_books_borrowed = number_of_books_borrowed

	def __repr__(self):
		return f"Borrower('{ self.tc_number }', '{ self.number_of_books_borrowed }')"

class Book():
	def __init__(self, isbn, title, author, is_borrowed):
		self.isbn = isbn
		self.title = title
		self.author = author
		self.is_borrowed = is_borrowed
	

	def __repr__(self):
		return f"Book('{self.isbn}', '{self.title}', '{self.author}', 'is_borrowed: {self.is_borrowed}')"

class Borrower_borrowed_book():
	def __init__(self, borrower_tc, book_isbn):
		self.borrower_tc = borrower_tc
		self.book_isbn = book_isbn
		self.begin_date =  datetime.now().strftime("%d-%m-%Y")
		self.end_date = fourteenDaysLater(datetime.now().strftime("%d-%m-%Y"))

	def __repr__(self):
		return f"Borrower_borrowed_book('{self.borrower_tc}', {self.book_isbn}, {self.begin_date}, {self.end_date}"

conn = sqlite3.connect('database.db',check_same_thread=False)

c = conn.cursor()

def create_table():
    conn = sqlite3.connect('database.db')

    c = conn.cursor()
    c.execute("""CREATE TABLE borrower (
            tc_number integer PRIMARY KEY,
            number_of_books_borrowed integer
            )""")
    c.execute("""CREATE TABLE book (
            isbn integer PRIMARY KEY,
            title text,
            author text,
            is_borrowed integer
            )""")
    c.execute("""CREATE TABLE borrower_borrowed_book (
            borrower_tc integer,
            book_isbn integer,
            begin_date text,
            end_date text,
            PRIMARY KEY (borrower_tc, book_isbn)
            FOREIGN KEY (borrower_tc) REFERENCES borrower (tc_number),
            FOREIGN KEY (book_isbn) REFERENCES book (isbn)
            )""")
    conn.commit()

def create_trigger():
	c.execute('''CREATE TRIGGER borrow_book
             AFTER INSERT ON borrower_borrowed_book
             BEGIN
                 UPDATE book SET is_borrowed = 1 WHERE isbn = NEW.book_isbn; 
             END
             ;
             ''')
	conn.commit()



def insert_borrower(borrower):
    with conn:
        c.execute("INSERT INTO borrower VALUES (:tc_number, :number_of_books_borrowed)", {'tc_number': borrower.tc_number, 'number_of_books_borrowed': borrower.number_of_books_borrowed})

def insert_book(book):
    with conn:
        c.execute("INSERT INTO book VALUES (:isbn, :title, :author, :is_borrowed)", {'isbn': book.isbn, 'title': book.title, 'author': book.author, 'is_borrowed': book.is_borrowed})

def insert_borrower_borrowed_book(borrower_borrowed_book):
    with conn:
        c.execute("INSERT INTO borrower_borrowed_book VALUES (:borrower_tc, :book_isbn, :begin_date, :end_date)", {'borrower_tc': borrower_borrowed_book.borrower_tc, 'book_isbn': borrower_borrowed_book.book_isbn, 'begin_date': borrower_borrowed_book.begin_date, 'end_date': borrower_borrowed_book.end_date})

def get_all_borrowers():
	c.execute("SELECT * FROM borrower")
	return c.fetchall()

def get_all_books():
	c.execute("SELECT * FROM book")
	return c.fetchall()

def get_all_borrower_borrowed_books():
	c.execute("SELECT * FROM borrower_borrowed_book")
	return c.fetchall()

def get_borrower_by_tc_number(tc_number):
    c.execute("SELECT * FROM borrower WHERE tc_number=:tc_number", {'tc_number': tc_number})
    return c.fetchall()

def get_book_by_isbn(isbn):
    c.execute("SELECT * FROM book WHERE isbn=:isbn", {'isbn': isbn})
    return c.fetchall()

def get_book_by_title(title):
    c.execute("SELECT * FROM book WHERE title=:title", {'title': title})
    return c.fetchall()

def get_book_by_author(author):
    c.execute("SELECT * FROM book WHERE author=:author", {'author': author})
    return c.fetchall()

def get_borrower_borrowed_book_by_isbn(isbn):
    c.execute("SELECT * FROM borrower_borrowed_book WHERE book_isbn=:isbn", {'isbn': isbn})
    return c.fetchall()


def update_borrower(borrower, new_number_of_books_borrowed):
    with conn:
        c.execute("""UPDATE borrower SET number_of_books_borrowed = :new_number_of_books_borrowed
                    WHERE tc_number = :tc_number""",
                  {'new_number_of_books_borrowed': new_number_of_books_borrowed, 'tc_number': borrower[0]})

def update_book_is_borrowed(book, old_is_borrowed):
    with conn:
        if old_is_borrowed == 1:
            c.execute("""UPDATE book SET is_borrowed = :is_borrowed
                        WHERE isbn = :isbn""",
                      {'is_borrowed': 0, 'isbn': book[0]})
        else:
            c.execute("""UPDATE book SET is_borrowed = :is_borrowed
                        WHERE isbn = :isbn""",
                      {'is_borrowed': 1, 'isbn': book[0]})



def remove_book(book):
    with conn:
        c.execute("DELETE from book WHERE isbn = :isbn",
                  {'isbn': book[0]})

def remove_borrower_book(borrower_book):
    with conn:
        c.execute("DELETE from borrower_borrowed_book WHERE book_isbn = :isbn",
                  {'isbn': borrower_book[1]})



@app.route('/', methods = ['POST', 'GET'])
def index():
	if request.method == "POST":
		if len(request.form) == 1:
			if "isbn" in request.form.keys():
				book = get_book_by_isbn(request.form["isbn"])[0]
				return render_template("isbn.html", book = book)
			elif "title" in request.form.keys():
				books = get_book_by_title(request.form["title"])
				return render_template("title.html", books = books)
			elif "author" in request.form.keys():
				books = get_book_by_author(request.form["author"])
				return render_template("author.html", books = books)
			else:
				tc_number = request.form["tc_number"]
				new_borrower = Borrower(tc_number,0)
				insert_borrower(new_borrower)
				return redirect("/")
		else:
			isbn = request.form["isbn"]
			title = request.form["title"]
			author = request.form["author"]
			new_book = Book(int(isbn),title,author,0)

			try:
				insert_book(new_book)
				return redirect("/")
			except:
				return "there was an issue while adding new book"

	else:
		books = get_all_books()
		borrowers = get_all_borrowers()
		borrower_book = get_all_borrower_borrowed_books()
		return render_template("index.html",books = books, borrowers = borrowers, borrower_book = borrower_book)


@app.route("/delete/<int:isbn>")
def delete(isbn):
	book_to_delete = get_book_by_isbn(isbn)[0]
	borrower_books = get_borrower_borrowed_book_by_isbn(book_to_delete[0])
	for borrower_book in borrower_books:
		borrower = get_borrower_by_tc_number(borrower_book[0])[0]
		update_borrower(borrower, borrower[1]-1)
		remove_borrower_book(borrower_book)

	remove_book(book_to_delete)
	return redirect("/")


@app.route("/borrow/<int:isbn>", methods = ["POST","GET"])
def borrow(isbn):
	book_to_borrow = get_book_by_isbn(isbn)[0]
	if request.method == "POST":
		borrower_tc_number = request.form["tc_number"]
		borrower = get_borrower_by_tc_number(borrower_tc_number)[0]
		if borrower[1] > 7:
			return "borrower may borrow at most 8 books "
		update_borrower(borrower, borrower[1]+1)
		borrower_book = Borrower_borrowed_book(borrower_tc_number,book_to_borrow[0])
		insert_borrower_borrowed_book(borrower_book)
		return redirect("/")
	else:
		return render_template("borrow.html",book = book_to_borrow)

if __name__ =="__main__":
	#create_table()
	#create_trigger()
	app.run(debug = True)