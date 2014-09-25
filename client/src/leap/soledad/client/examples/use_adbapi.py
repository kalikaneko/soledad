# -*- coding: utf-8 -*-
# use_adbapi.py
# Copyright (C) 2014 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Example of use of the asynchronous soledad api.
"""
from twisted.internet import defer, reactor

from leap.soledad.client import adbapi
from leap.soledad.client.sqlcipher import SQLCipherOptions

opts = SQLCipherOptions('/tmp/test.soledad', "secret", create=True)
dbpool = adbapi.getConnectionPool(opts)


def createDoc(doc):
    return dbpool.runU1DBQuery("create_doc", doc)


def getAllDocs():
    return dbpool.runU1DBQuery("get_all_docs")


def printResult(r):
    print r.doc_id, r.content['number']


def allDone(_):
    print "ALLDONE"
    reactor.stop()

deferreds = []

NUM = 10000

for i in range(NUM):
    doc = {"number": i,
           "payload": open('manifest.phk').read()}
    d = createDoc(doc)
    d.addCallbacks(printResult, lambda e: e.printTraceback())
    deferreds.append(d)


all_done = defer.gatherResults(deferreds, consumeErrors=True)
all_done.addCallback(allDone)

reactor.run()
