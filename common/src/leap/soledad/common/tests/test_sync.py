# -*- coding: utf-8 -*-
# test_sync.py
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
import json
import tempfile
import threading
import time

from urlparse import urljoin
from twisted.internet import defer

from testscenarios import TestWithScenarios

from leap.soledad.common import couch
from leap.soledad.client import sync

from leap.soledad.common.tests import u1db_tests as tests
from leap.soledad.common.tests.u1db_tests import TestCaseWithServer
from leap.soledad.common.tests.u1db_tests import simple_doc
from leap.soledad.common.tests.util import make_token_soledad_app
from leap.soledad.common.tests.util import make_soledad_document_for_test
from leap.soledad.common.tests.util import soledad_sync_target
from leap.soledad.common.tests.util import BaseSoledadTest
from leap.soledad.common.tests.util import SoledadWithCouchServerMixin
from leap.soledad.common.tests.test_couch import CouchDBTestCase


class InterruptableSyncTestCase(
        BaseSoledadTest, CouchDBTestCase, TestCaseWithServer):

    """
    Tests for encrypted sync using Soledad server backed by a couch database.
    """

    @staticmethod
    def make_app_with_state(state):
        return make_token_soledad_app(state)

    make_document_for_test = make_soledad_document_for_test

    sync_target = soledad_sync_target

    def make_app(self):
        self.request_state = couch.CouchServerState(self.couch_url)
        return self.make_app_with_state(self.request_state)

    def setUp(self):
        TestCaseWithServer.setUp(self)
        CouchDBTestCase.setUp(self)
        self.tempdir = tempfile.mkdtemp(prefix="leap_tests-")

    def tearDown(self):
        CouchDBTestCase.tearDown(self)
        TestCaseWithServer.tearDown(self)

    def test_interruptable_sync(self):
        """
        Test if Soledad can sync many smallfiles.
        """

        self.skipTest("Sync is currently not interruptable.")

        class _SyncInterruptor(threading.Thread):

            """
            A thread meant to interrupt the sync process.
            """

            def __init__(self, soledad, couchdb):
                self._soledad = soledad
                self._couchdb = couchdb
                threading.Thread.__init__(self)

            def run(self):
                while db._get_generation() < 2:
                    # print "WAITING %d" % db._get_generation()
                    time.sleep(0.1)
                self._soledad.stop_sync()
                time.sleep(1)

        number_of_docs = 10
        self.startServer()

        # instantiate soledad and create a document
        sol = self._soledad_instance(
            user='user-uuid', server_url=self.getURL())

        # ensure remote db exists before syncing
        db = couch.CouchDatabase.open_database(
            urljoin(self.couch_url, 'user-user-uuid'),
            create=True,
            ensure_ddocs=True)

        # create interruptor thread
        t = _SyncInterruptor(sol, db)
        t.start()

        d = sol.get_all_docs()
        d.addCallback(lambda results: self.assertEqual([], results[1]))

        def _create_docs(results):
            # create many small files
            deferreds = []
            for i in range(0, number_of_docs):
                deferreds.append(sol.create_doc(json.loads(simple_doc)))
            return defer.DeferredList(deferreds)

        # sync with server
        d.addCallback(_create_docs)
        d.addCallback(lambda _: sol.get_all_docs())
        d.addCallback(
            lambda results: self.assertEqual(number_of_docs, len(results[1])))
        d.addCallback(lambda _: sol.sync())
        d.addCallback(lambda _: t.join())
        d.addCallback(lambda _: db.get_all_docs())
        d.addCallback(
            lambda results: self.assertNotEqual(
                number_of_docs, len(results[1])))
        d.addCallback(lambda _: sol.sync())
        d.addCallback(lambda _: db.get_all_docs())
        d.addCallback(
            lambda results: self.assertEqual(number_of_docs, len(results[1])))

        def _tear_down(results):
            db.delete_database()
            db.close()
            sol.close()

        d.addCallback(_tear_down)
        return d


class TestSoledadDbSync(
        TestWithScenarios,
        SoledadWithCouchServerMixin,
        tests.TestCaseWithServer):

    """
    Test db.sync remote sync shortcut
    """

    scenarios = [
        ('py-token-http', {
            'make_app_with_state': make_token_soledad_app,
            'make_database_for_test': tests.make_memory_database_for_test,
            'token': True
        }),
    ]

    oauth = False
    token = False

    def setUp(self):
        """
        Need to explicitely invoke inicialization on all bases.
        """
        SoledadWithCouchServerMixin.setUp(self)
        self.startTwistedServer()
        self.db = self.make_database_for_test(self, 'test1')
        self.db2 = self.request_state._create_database(replica_uid='test')

    def tearDown(self):
        """
        Need to explicitely invoke destruction on all bases.
        """
        SoledadWithCouchServerMixin.tearDown(self)
        # tests.TestCaseWithServer.tearDown(self)

    def do_sync(self):
        """
        Perform sync using SoledadSynchronizer, SoledadSyncTarget
        and Token auth.
        """
        target = soledad_sync_target(
            self, self.db2._dbname,
            source_replica_uid=self._soledad._dbpool.replica_uid)
        self.addCleanup(target.close)
        return sync.SoledadSynchronizer(
            self.db,
            target).sync(defer_decryption=False)

    @defer.inlineCallbacks
    def test_db_sync(self):
        """
        Test sync.

        Adapted to check for encrypted content.
        """

        doc1 = self.db.create_doc_from_json(tests.simple_doc)
        doc2 = self.db2.create_doc_from_json(tests.nested_doc)

        local_gen_before_sync = yield self.do_sync()
        gen, _, changes = self.db.whats_changed(local_gen_before_sync)
        self.assertEqual(1, len(changes))
        self.assertEqual(doc2.doc_id, changes[0][0])
        self.assertEqual(1, gen - local_gen_before_sync)
        self.assertGetEncryptedDoc(
            self.db2, doc1.doc_id, doc1.rev, tests.simple_doc, False)
        self.assertGetEncryptedDoc(
            self.db, doc2.doc_id, doc2.rev, tests.nested_doc, False)

    # TODO: add u1db.tests.test_sync.TestRemoteSyncIntegration
