# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

import os
import sys


# region Daemonize (Linux)

# DERIVED FROM: http://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/

# This module is used to fork the current process into a daemon.
# Almost none of this is necessary (or advisable) if your daemon
# is being started by inetd. In that case, stdin, stdout and stderr are
# all set up for you to refer to the network connection, and the fork()s
# and session manipulation should not be done (to avoid confusing inetd).
# Only the chdir() and umask() steps remain as useful.
# References:
#     UNIX Programming FAQ
#         1.7 How do I get my program to act like a daemon?
#             http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
#
#     Advanced Programming in the Unix Environment
#         W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.


def daemonize_linux(stdin='/dev/null', stdout='/dev/null', stderr=None, pid_file=None, working_dir=None):
    """
    This forks the current process into a daemon.

    The stdin, stdout, and stderr arguments are file names that will be opened and be used to replace
    the standard file descriptors in `sys.stdin`, `sys.stdout`, and `sys.stderr`.

    These arguments are optional and default to /dev/null. Note that stderr is opened unbuffered, so
    if it shares a file with stdout then interleaved output may not appear in the order that you expect.

    :param stdin:
    :param stdout:
    :param stderr:
    :param pid_file:
    :param working_dir:
    """

    # Because you're not reaping your dead children, many of these resources are held open longer than they should.
    # Your second children are being properly handled by init(8) -- their parent is dead, so they are re-parented
    # to init(8), and init(8) will clean up after them (wait(2)) when they die.
    #
    # However, your program is responsible for cleaning up after the first set of children. C programs typically
    # install a signal(7) handler for SIGCHLD that calls wait(2) or waitpid(2) to reap the children's exit status
    # and thus remove its entries from the kernel's memory.
    #
    # But signal handling in a script is a bit annoying. If you can set the SIGCHLD signal disposition to SIG_IGN
    # explicitly, the kernel will know that you are not interested in the exit status and will reap the children
    # for you_.
    import signal
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    # Do first fork.
    try:
        # sys.stdout.write("attempting first fork, pid=")
        pid = os.fork()
        if pid > 0:
            # sys.stdout.write("%s\n" % pid)
            sys.exit(0)  # Exit first parent.
    except OSError as e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    # sys.stdout.write("attempting to separate from the parent environment\n")
    os.chdir('/')
    os.umask(0)
    os.setsid()

    # Do second fork.
    try:
        # sys.stdout.write("attempting second fork, pid=")
        pid = os.fork()
        if pid > 0:
            # sys.stdout.write("%s\n" % pid)
            sys.exit(0)  # Exit second parent.
    except OSError as e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # sys.stdout.write("\nI am now a daemon -- redirecting stdin, stdout, stderr now -- goodbye terminal\n")

    # Redirect standard file descriptors.
    if not stderr:
        stderr = stdout
    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'a+', 0)
    # this might be a good time to write a PID message to the starting user?
    if pid_file:
        with open(pid_file, 'w+') as f:  # online references don't close this -- is it bad if we do?
            f.write('%s\n' % pid)
    # flush anything that is in the current stdout/stderr
    sys.stdout.flush()
    sys.stderr.flush()
    # close file descriptors for stdin, stdout, and stderr
    os.close(sys.stdin.fileno())
    os.close(sys.stdout.fileno())
    os.close(sys.stderr.fileno())
    # reassign file descriptors for stdin, stdout, and stderr
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    if working_dir:
        os.chdir(working_dir)

# ## Why 2 forks?
# The first fork accomplishes two things - allow the shell to return, and allow you to do a setsid().
#
# The setsid() removes yourself from your controlling terminal.
# You see, before, you were still listed as a job of your previous process, and therefore the user might
# accidentally send you a signal. setsid() gives you a new session, and removes the existing controlling terminal.
#
# The problem is, you are now a session leader. As a session leader, if you open a file descriptor that is a terminal,
# it will become your controlling terminal (oops!). Therefore, the second fork makes you NOT be a session leader.
# Only session leaders can acquire a controlling terminal, so you can open up any file you wish without worrying
# that it will make you a controlling terminal.
#
# So - first fork - allow shell to return, and permit you to call setsid()
#
# Second fork - prevent you from accidentally reacquiring a controlling terminal.

# endregion
