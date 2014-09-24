# -*- coding: utf-8 -*-
# sqlcipher.py
# Copyright (C) 2013, 2014 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
An asyncrhonous interface to soledad using sqlcipher backend.
It uses twisted.enterprise.adbapi.
"""
import os
import sys

from twisted.enterprise import adbapi
from twisted.python import log


DEBUG_SQL = os.environ.get("LEAP_DEBUG_SQL")
if DEBUG_SQL:
    log.startLogging(sys.stdout)


def getConnectionPool(opts, openfun=None):
    return adbapi.ConnectionPool(
        "pysqlcipher.dbapi2", database=opts.path, key=opts.key,
        check_same_thread=False, openfun=openfun)


# XXX work in progress --------------------------------------------


class U1DBSqliteWrapper(sqlite_backend.SQLitePartialExpandDatabase):

    def __init__(self, conn):
        self._db_handle = conn
        self._real_replica_uid = None
        self._ensure_schema()
        self._factory = u1db.Document


class U1DBConnection(adbapi.Connection):

    def __init__(self, *args):
        adbapi.Connection.__init__(self, *args)

    def reconnect(self):
        if self._connection is not None:
            self._pool.disconnect(self._connection)
        self._connection = self._pool.connect()
        self._u1db = U1DBSqliteWrapper(self._connection)

    def __getattr__(self, name):
        if name.startswith('u1db_'):
            return getattr(self._u1db, name.strip('u1db_'))
        else:
            return getattr(self._connection, name)


class U1DBTransaction(adbapi.Transaction):

    def __getattr__(self, name):
        preffix = "u1db_"
        if name.startswith(preffix):
            return getattr(self._connection._u1db, name.strip(preffix))
        else:
            return getattr(self._cursor, name)


class U1DBConnectionPool(adbapi.ConnectionPool):

    connectionFactory = U1DBConnection
    transactionFactory = U1DBTransaction

    def runU1DBQuery(self, meth, *args, **kw):
        meth = "u1db_%s" % meth
        return self.runInteraction(self._runU1DBQuery, meth, *args, **kw)

    def _runU1DBQuery(self, trans, meth, *args, **kw):
        meth = getattr(trans, meth)
        return meth(*args, **kw)
