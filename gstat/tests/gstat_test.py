#!/usr/bin/env python
import os
import socket
import unittest

from ..gstat import gstat, gstats, gstat_event, gstat_elapsed


class MockSocket(object):
    def __init__(self, *args, **kwargs):
        self._sendto_msg = []
        self._closed = False

    def sendto(self, msg, hostport):
        sent = { 'msg': msg }
        sent.update(zip( ('host', 'port'), hostport ))
        sent.update(zip( ('metric', 'value', 'ts'), msg.split() ))
        self._sendto_msg.append(sent)

        if "socket_error" in sent['msg']:
            raise socket.error

    def close(self):
        self._closed = True


class GstatTestCase(unittest.TestCase):
    def setUp(self):
        super(GstatTestCase, self).setUp()
        self._orig_socket = socket.socket
        socket.socket = self._fake_socket
        self._orig_host = os.environ.get('CARBON_HOST')
        os.environ['CARBON_HOST'] = "localhost"
        self._socket = MockSocket()

    def tearDown(self):
        super(GstatTestCase, self).tearDown()
        socket.socket = self._orig_socket
        if self._orig_host:
            os.environ['CARBON_HOST'] = self._orig_host
        else:
            try:
                del os.environ['CARBON_HOST']
            except KeyError:
                pass

    def _fake_socket(self, *args, **kwargs):
        return self._socket

    def metric_sent(self):
        return [ m['metric'] for m in self._socket._sendto_msg ]

    def value_sent(self):
        return [ m['value'] for m in self._socket._sendto_msg ]

    def ts_sent(self):
        return [ m['ts'] for m in self._socket._sendto_msg ]


class GstatDebugTestCase(GstatTestCase):
    """gstat called in a development environment doesn't send stats"""
    def setUp(self):
        super(GstatDebugTestCase, self).setUp()
        try:
            del os.environ["CARBON_HOST"]
        except KeyError:
            pass

    def test_gstat_no_network_traffic(self):
        gstat("test.gstat.testcase", 1)
        self.assertEqual(len(self._socket._sendto_msg), 0)

    def test_gstat_metric_value(self):
        g = gstat("test.gstat.testcase", 657)
        self.assertNotEqual(g, None)
        self.assertEquals(g.split()[0], '(debug)')
        self.assertEquals(g.split()[1], 'test.gstat.testcase')
        self.assertEquals(g.split()[2], '657')

    def test_gstat_metric_value_ts(self):
        g = gstat("test.gstat.testcase", 1, 789)
        self.assertEquals(g.split()[3], "789")

    def test_gstat_not_enough_params(self):
        self.assertRaises(TypeError, gstat)
        self.assertRaises(TypeError, gstat, "test.gstat.testcase")

    def test_gstat_bad_parms(self):
        """test that gstat doesnt raise exceptions for bad values"""
        self.assertEqual(gstat(1,"a","a"), None)

    def test_gstats_not_iterable_dont_kill_caller(self):
        self.assertEqual(gstats(7), None)


class GstatProdTestCase(GstatTestCase):
    """
    gstat called in a production environment uses socket to send stats
    """
    def tearDown(self):
        super(GstatProdTestCase, self).tearDown()
        self.assertTrue(self._socket._closed)

    def test_gstat_used_socket(self):
        gstat("test.gstat.testcase", 1)
        self.assertNotEqual(self._socket._sendto_msg, None)

    def test_gstat_metric_value_ts(self):
        gstat("test.gstat.testcase", 647.3, 789)

        self.assertEqual(self.metric_sent()[0], "test.gstat.testcase")
        self.assertEqual(self.value_sent()[0], "647.3")
        self.assertEquals(self.ts_sent()[0], "789")

    def test_gstats(self):
        stats = (
                ("test.gstat.testcase.one", 1),
                ("test.gstat.testcase.two", 2),
                ("test.gstat.testcase.three", 3),
                )
        g = gstats(stats)
        self.assertEqual(len(g), len(stats))
        g = gstats([])
        self.assertEqual(len(g), 0)

        # graphite expects a trailing newline at the end of a sent stat
        self.assertTrue(len(self._socket._sendto_msg) > 0)
        for sent in self._socket._sendto_msg:
            self.assertTrue(sent['msg'].endswith('\n'))

        # mocked socket keeps track of multiple gstat calls in the order
        # sent
        self.assertEqual(self.metric_sent()[-1], stats[-1][0])

    def test_gstat_event(self):
        """gstat_event creates a metric with a "1" value"""
        gstat_event("test.gstat.testcase.event")
        self.assertEqual(self.value_sent()[0], "1")

    def test_socket_errors_dont_kill_caller(self):
        gstat("test.gstat.socket_error", 1)
        self.assertNotEqual(self._socket._sendto_msg, None)

    def test_elapsed_decorator(self):
        method_arg = "xyzzy"
        kw_arg = "plugh"
        metric_name = "test.gstat.elapsed_decorator"

        @gstat_elapsed(metric_name)
        def measure_elapsed(arg, k=None):
            self.assertEqual(arg, method_arg)
            return k

        ret = measure_elapsed(method_arg, k=kw_arg)

        # test that our metric was logged by the decorator
        self.assertEqual(self.metric_sent()[0], metric_name)

        # test that the decorator returns the method's return value
        self.assertEqual(ret, kw_arg)
