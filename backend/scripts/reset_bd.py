import pymysql

c = pymysql.connect(host="localhost", user="minimarket", password="minimarket", autocommit=True)
cur = c.cursor()
cur.execute("DROP DATABASE IF EXISTS minimarket")
cur.execute("CREATE DATABASE minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
print("base reiniciada")
