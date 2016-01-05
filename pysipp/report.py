'''
reporting for writing SIPp log files to the console
'''
import time
from os import path
from collections import OrderedDict
import utils

log = utils.get_logger()

ERRCODES = {
    # 0: "All calls were successful"
    1: "At least one call failed",
    15: "Process was terminated",
    97: "Exit on internal command. Calls may have been processed",
    99: "Normal exit without calls processed",
    -1: "Fatal error",
    -2: "Fatal error binding a socket",
    -10: "Signalled to stop with SIGUSR1",
    254: "Connection Error: socket already in use",
    255: "Command or syntax error: check stderr output",
}


def raise_on_nz(agents2procs):
    """Raise an error detailing failed SIPp agent exit codes
    """
    name2ec = OrderedDict()
    # gather all exit codes
    for ua, proc in agents2procs.items():
        name2ec[ua.name] = proc.returncode

    if any(name2ec.values()):
        # raise a detailed error
        msg = "Some SIPp agents failed\n"
        msg += '\n'.join("'{}' with exit code '{}' -> {}".format(
            name, rc, ERRCODES.get(rc, "unknown exit code"))
            for name, rc in name2ec.items()
        )
        raise RuntimeError(msg)


def emit_logfiles(agents2procs, level='warn', max_lines=50):
    """Log all available SIPp log-file contents
    """
    emit = getattr(log, level)
    for ua, proc in agents2procs.items():

        # print stderr
        emit("stderr for '{}'\n{}\n".format(ua.name, proc.streams.stderr))

        # print log file contents
        for name, fpath in ua.iter_logfile_items():
            if fpath and path.isfile(fpath):
                with open(fpath, 'r') as lf:
                    lines = lf.readlines()
                    llen = len(lines)

                    # truncate long log files
                    if llen > max_lines:
                        toolong = (
                            "...\nOutput has been truncated to {} lines - "
                            "see '{}' for full details\n"
                        ).format(max_lines, fpath)
                        output = ''.join(lines[:max_lines]) + toolong
                    else:
                        output = ''.join(lines)
                    # log it
                    emit("'{}' contents for {} @ socket {}:\n{}".format(
                        name, ua.name, ua.sockaddr, output))