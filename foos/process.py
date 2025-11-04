"""Utilities for executing subprocesses with consistent logging."""

import subprocess
import logging

logger = logging.getLogger(__name__)


def call_and_log(*args, **kwargs):
    """Execute a command and log the captured output.

    Args:
        *args: Positional arguments passed directly to
            :class:`subprocess.Popen`.
        **kwargs: Keyword arguments forwarded to :class:`subprocess.Popen`.

    Returns:
        Completed :class:`subprocess.Popen` instance.  The return value mirrors
        :func:`subprocess.Popen` to aid callers that need command metadata.
    """

    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout, stderr = p.communicate()
    if len(stdout) > 0:
        logger.info(stdout.decode("utf-8").strip())
    if len(stderr) > 0:
        logger.error(stderr.decode("utf-8").strip())
    if p.returncode != 0:
        logger.error("{} returned {}".format(p.args, p.returncode))
    return p


def long_running(*args, **kwargs):
    """Stream process output to the log as it is produced.

    The function is optimized for commands that run for a significant amount of
    time.  Output is consumed line-by-line to avoid buffering delays while still
    capturing a non-zero exit status for diagnostics.

    Args:
        *args: Positional arguments forwarded to :class:`subprocess.Popen`.
        **kwargs: Keyword arguments forwarded to :class:`subprocess.Popen`.

    Returns:
        Completed :class:`subprocess.Popen` instance for the executed command.
    """

    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, **kwargs)
    with p.stdout:
        for line in iter(p.stdout.readline, b''):
            logger.error(line.decode("utf-8").strip())

    p.wait()
    if p.returncode != 0:
        logger.error("{} returned {}".format(p.args, p.returncode))
    return p
