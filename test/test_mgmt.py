#
# Copyright (c) 2008 Daniel Truemper truemped@googlemail.com
#
# test_mgmt.py 10-Jan-2011
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# under the License.
#
#

import unittest

import time

import zmq
from zmq.eventloop.ioloop import IOLoop

from spyder.core.mgmt import ZmqMgmt
from spyder.core.constants import *


class ManagementIntegrationTest(unittest.TestCase):


    def setUp(self):
        self._context = zmq.Context(1)

        self._master_pub = self._context.socket(zmq.PUB)
        self._master_pub.bind( 'inproc://master/worker/coordination' )

        self._worker_sub = self._context.socket(zmq.SUB)
        self._worker_sub.connect( 'inproc://master/worker/coordination' )

        self._worker_pub = self._context.socket(zmq.PUB)
        self._worker_pub.bind( 'inproc://worker/master/coordination' )

        self._master_sub = self._context.socket(zmq.SUB)
        self._master_sub.connect( 'inproc://worker/master/coordination' )
        self._master_sub.setsockopt(zmq.SUBSCRIBE, "")

        self._ioloop = IOLoop.instance()
        self._topic = ZMQ_SPYDER_MGMT_WORKER + 'testtopic'

    def tearDown(self):
        self._master_pub.close()
        self._worker_sub.close()
        self._worker_pub.close()
        self._master_sub.close()
        self._context.term()

    def call_me(self, msg):
        self.assertEqual( [ self._topic, 'test' ], msg )
        self._master_pub.send_multipart(ZMQ_SPYDER_MGMT_WORKER_QUIT)


    def on_end(self, msg):
        self.assertEqual(ZMQ_SPYDER_MGMT_WORKER_QUIT, msg)
        self._ioloop.stop()


    def test_simple_mgmg_session(self):
        
        mgmt = ZmqMgmt( self._worker_sub, self._worker_pub, ioloop=self._ioloop)
        mgmt.start()

        self.assertRaises(ValueError, mgmt.add_callback, "test", "test")

        mgmt.add_callback(self._topic, self.call_me)
        mgmt.add_callback(ZMQ_SPYDER_MGMT_WORKER, self.on_end)

        self._master_pub.send_multipart( [ self._topic, 'test'.encode() ] )

        self._ioloop.start()

        self.assertEqual(ZMQ_SPYDER_MGMT_WORKER_QUIT_ACK, self._master_sub.recv_multipart())
        mgmt.remove_callback(self._topic, self.call_me)
        mgmt.remove_callback(ZMQ_SPYDER_MGMT_WORKER, self.on_end)
        self.assertEqual({}, mgmt._callbacks)
        mgmt.stop()


if __name__ == '__main__':
    unittest.main()
