#!/usr/bin/python

from os import environ

# We need a database to test against.

# The connection parameters are taken from the usual PG* environment
# variables and can be overridden with PYGRESQL_* environment variables
# or values specified in the file .LOCAL_PyGreSQL or LOCAL_PyGreSQL.py.

# The tests should be run with various PostgreSQL versions and databases
# created with different encodings and locales.  Particularly, make sure the
# tests are running against databases created with both SQL_ASCII and UTF8.

# The current user must have create schema privilege on the database.

get = environ.get

dbname = get('PYGRESQL_DB', get('PGDATABASE'))
dbhost = get('PYGRESQL_HOST', get('PGHOST'))
dbport = get('PYGRESQL_PORT', get('PGPORT'))
dbuser = get('PYGRESQL_USER', get('PGUSER'))
dbpasswd = get('PYGRESQL_PASSWD', get('PGPASSWORD'))

if dbport:
    dbport = int(dbport)

try:
    from .LOCAL_PyGreSQL import *  # noqa: F401
except (ImportError, ValueError):
    try:
        from LOCAL_PyGreSQL import *  # noqa: F401
    except ImportError:
        pass
