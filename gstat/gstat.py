#!/usr/bin/env python
#
# Send metrics to a graphite host without causing exceptions or
# otherwise preventing the caller from continuing.
#
# Configuration
# -------------
#
# Use environment variables to control where metrics are sent:
#
#   CARBON_HOST:  if not set, logs metrics instead of sending to a host
#                 (useful during development, etc)
#   CARBON_PORT:  defaults to 2003
#
import logging
import os
import socket
import sys
import time


logger = logging.getLogger("gstat")


def gstat(metric, value, ts=None):
    """
    send the given metric value to graphite
    use udp to "fire and forget".  minimizes errors that could cause
    problems for the caller (eg, carbon host is unreachable, etc).
    """

    # host running graphite's carbon-cache listener
    CARBON_HOST = os.environ.get('CARBON_HOST')
    CARBON_PORT = os.environ.get('CARBON_PORT', 2003)

    if ts is None:
        ts = time.time()

    try:
        msg = "%s %s %d" % (metric, value, int(ts))
    except (ValueError, TypeError):
        logger.exception(
                "gstat('%s', '%s', '%s') failed. ignoring..." % (
                    metric, value, ts
                    ))
        return None

    if not CARBON_HOST:
        # dont send metrics from local development environments
        logger.info("gstat (debug): %s" % msg)
        return "(debug) " + msg

    try:
        s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        s.sendto( msg+'\n', (CARBON_HOST, CARBON_PORT) )
        # sent.  did it get there?  we dont care!
        logger.debug("gstat sent: %s" % msg)
    except socket.error:
        logger.exception("gstat failed for '%s'. ignoring..." % msg)
        return None
    finally:
        try: s.close()
        except (NameError, UnboundLocalError): pass

    return msg


def gstats(metrics, ts=None):
    """send the given list of (metric, value) tuples to graphite"""

    if ts is None:
        # use the same timestamp for all metrics
        ts = time.time()

    try:
        return [ gstat(m, v, ts) for m, v in metrics ]
    except (TypeError, ValueError):
        # metrics not iterable?
        logger.exception(
                "gstats('%s', '%s') failed. ignoring..." % (metrics, ts)
                )
        return None


def gstat_elapsed(metric):
    """
    decorator that logs the elapsed time spent in the decorated method
    """
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            start_time = time.time()
            ret = f(*args, **kwargs)
            gstat(metric, time.time() - start_time)
            return ret
        return wrapped_f
    return wrap


def gstat_event(metric, ts=None):
    """send a one-time event metric to graphite"""
    return gstat(metric, 1, ts)


if __name__ == "__main__":
    fmt = '%(asctime)s %(levelname)s %(funcName)s:%(lineno)s: %(message)s'
    logging.basicConfig(level=logging.WARNING, format=fmt)
    print gstat(*sys.argv[1:4])
