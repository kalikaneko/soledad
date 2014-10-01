# -*- coding: utf-8 -*-
# use_api.py
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
Example of use of the soledad api.
"""
import os

from leap.soledad.client import sqlcipher
from leap.soledad.client.sqlcipher import SQLCipherOptions

folder = os.environ.get("TMPDIR", "tmp")
times = int(os.environ.get("TIMES", "1000"))
tmpdb = os.path.join(folder, "test.soledad")

print "[+] db path:", tmpdb
print "[+] times", times

if os.path.isfile(tmpdb):
    print "[+] Removing existing db file..."
    os.remove(tmpdb)

opts = SQLCipherOptions(tmpdb, "secret", create=True)
db = sqlcipher.SQLCipherDatabase(None, opts)


def allDone():
    print "ALLDONE"


for i in range(times):
    doc = {"number": i,
           "payload": open('manifest.phk').read()}
    d = db.create_doc(doc)
    print d.doc_id, d.content['number']

print "Count", len(db.get_all_docs()[1])

allDone()
