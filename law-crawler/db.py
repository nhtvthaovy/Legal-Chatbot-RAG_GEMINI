from peewee import MySQLDatabase

DATABASE = 'mysql://root:123456@localhost:3306/law'
db = MySQLDatabase(database='law', user='root', password='123456')