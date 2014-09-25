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
from leap.soledad.client import sqlcipher
from leap.soledad.client.sqlcipher import SQLCipherOptions

opts = SQLCipherOptions('/tmp/test.soledad', "secret", create=True)

db = sqlcipher.SQLCipherDatabase(None, opts)


def allDone():
    print "ALLDONE"


NUM = 10000

for i in range(NUM):
    doc = {"number": i,
           "payload": open('manifest.phk').read()}
    d = db.create_doc(doc)
    print d.doc_id, d.content['number']

allDone()
