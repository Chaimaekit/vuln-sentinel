#!/usr/bin/env python3
import sqlite3

def vulnerable_login(username, password):
    """VULNERABLE: SQL injection through string concatenation"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Direct string concatenation - SQL injection vulnerability
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    cursor.execute(query)
    
    return cursor.fetchone()

def vulnerable_search(search_term):
    """VULNERABLE: User input directly in query"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
    cursor.execute(query)
    
    return cursor.fetchall()

def main():
    # Example of vulnerable use
    username = input("Username: ")
    password = input("Password: ")
    
    user = vulnerable_login(username, password)
    if user:
        print(f"Welcome {user}")

if __name__ == "__main__":
    main()
