import functools

from twisted.internet import reactor

from leap.soledad.client import adbapi
from leap.soledad.client import sqlcipher
from leap.soledad.client.sqlcipher import SQLCipherOptions

opts = SQLCipherOptions('/tmp/test.soledad', "secret", create=True)
#openfun = functools.partial(sqlcipher.init_crypto, opts=opts)
dbpool = adbapi.getConnectionPool(opts)  # , openfun=openfun)


def createDoc(doc):
    return dbpool.runU1DBQuery("create_doc", doc)


def getAllDocs():
    return dbpool.runU1DBQuery("get_all_docs")


def printResult(r):
    print r


for i in range(1000):
    doc = {"number": i}
    createDoc(doc).addCallbacks(printResult, lambda e: e.printTraceback())

reactor.run()
