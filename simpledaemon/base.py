"""
Provides a simple Daemon class to ease the process of forking a
python application on Unix systems.
"""
import os
import pwd
import sys
import grp
import time
import errno
import signal
import logging
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


VERSION = (1, 4, 1)


class Daemon(object):
    """Daemon base class"""

    def __init__(self):
        """Override to change where the daemon looks for config information.

        By default we use the 'daemon' section of a file with the same name
        as the python module holding the subclass, ending in .conf
        instead of .py.
        """
        self.create_parsers()
        self.add_arguments()
        
        if not hasattr(self, 'default_conf'):
            # Grabs the filename that the Daemon subclass resides in...
            self.daemon_file = sys.modules[self.__class__.__module__].__file__
            self.default_conf = self.daemon_file.rpartition('.')[0] + '.conf'
        if not hasattr(self, 'section'):
            self.section = 'daemon'

    def setup_root(self):
        """Override to perform setup tasks with root privileges.

        When this is called, logging has been initialized, but the
        terminal has not been detached and the pid of the long-running
        process is not yet known.
        """

    def setup_user(self):
        """Override to perform setup tasks with user privileges.

        Like setup_root, the terminal is still attached and the pid is
        temporary.  However, the process has dropped root privileges.
        """

    def run(self):
        """Override.

        The terminal has been detached at this point.
        """

    def main(self):
        """Read the command line and either start or stop the daemon"""
        self.args = self.parser.parse_args()
        self.read_basic_config()      
        try:
            self.args.func()
        except AttributeError:
            self.parser.error('Must specify a command, start, stop, etc. See --help for more info.')

    def create_parsers(self):
        self.parser = argparse.ArgumentParser()

        subparsers = self.parser.add_subparsers()

        self.start_parser   = subparsers.add_parser('start',   help='Start the daemon')
        self.start_parser.set_defaults(func=self.start)

        self.stop_parser    = subparsers.add_parser('stop',    help='Stop the daemon')
        self.stop_parser.set_defaults(func=self.stop)

        self.restart_parser = subparsers.add_parser('restart', help='Restart the daemon')
        self.restart_parser.set_defaults(func=self.restart)

        self.status_parser  = subparsers.add_parser('status',  help='Get status of the daemon')
        self.status_parser.set_defaults(func=self.status)


    def add_arguments(self):
        """Parse the command line"""
        nodaemon_arg = self.start_parser.add_argument(
            '-n', '--nodaemon', dest='daemonize',
            action='store_false', default=True,
            help='Run in the foreground'
        )
        
        self.parser.add_argument(
            '-c', '--configfile', default=self.default_conf,
            type=argparse.FileType('r'),
            help='Specify alternate configuration file name'
        )
    
        self.restart_parser._add_action(nodaemon_arg)

    def read_basic_config(self):
        """Read basic options from the daemon config file"""
        cp = configparser.ConfigParser(defaults={
            'logmaxmb': '0',
            'logbackups': '0',
            'loglevel': 'info',
            'uid': str(os.getuid()),
            'gid': str(os.getgid()),
        })
        cp.readfp(self.args.configfile)
        self.config_parser = cp

        try:
            self.uid, self.gid = map(int, get_uid_gid(cp, self.section))
        except ValueError as e:
            sys.exit(str(e))

        self.logmaxmb = int(cp.get(self.section, 'logmaxmb'))
        self.logbackups = int(cp.get(self.section, 'logbackups'))
        self.pidfile = cp.get(self.section, 'pidfile')
        self.logfile = cp.get(self.section, 'logfile')
        self.loglevel = cp.get(self.section, 'loglevel')

    def on_sigterm(self, signalnum, frame):
        """Handle segterm by treating as a keyboard interrupt"""
        raise KeyboardInterrupt('SIGTERM')

    def add_signal_handlers(self):
        """Register the sigterm handler"""
        signal.signal(signal.SIGTERM, self.on_sigterm)

    def start(self):
        """Initialize and run the daemon"""
        # The order of the steps below is chosen carefully.
        # - don't proceed if another instance is already running.
        self.check_pid()
        # - start handling signals
        self.add_signal_handlers()
        # - create log file and pid file directories if they don't exist
        self.prepare_dirs()

        # - start_logging must come after check_pid so that two
        # processes don't write to the same log file, but before
        # setup_root so that work done with root privileges can be
        # logged.
        self.start_logging()
        try:
            # - set up with root privileges
            self.setup_root()
            # - drop privileges
            self.set_uid()
            # - check_pid_writable must come after set_uid in order to
            # detect whether the daemon user can write to the pidfile
            self.check_pid_writable()
            # - set up with user privileges before daemonizing, so that
            # startup failures can appear on the console
            self.setup_user()

            # - daemonize
            if self.args.daemonize:
                daemonize()
        except:
            logging.exception("failed to start due to an exception")
            raise

        # - write_pid must come after daemonizing since the pid of the
        # long running process is known only after daemonizing
        self.write_pid()
        try:
            logging.info("started")
            try:
                self.run()
            except (KeyboardInterrupt, SystemExit):
                pass
            except:
                logging.exception("stopping with an exception")
                raise
        finally:
            self.remove_pid()
            logging.info("stopped")

    def stop(self):
        """Stop the running process"""
        if self.running():
            pid = int(open(self.pidfile).read())
            os.kill(pid, signal.SIGTERM)
            # wait for a moment to see if the process dies
            for n in range(10):
                time.sleep(0.25)
                try:
                    # poll the process state
                    os.kill(pid, 0)
                except OSError as why:
                    if why.errno == errno.ESRCH:
                        # process has died
                        break
                    else:
                        raise
            else:
                sys.exit("pid %d did not die" % pid)
        else:
            sys.exit("not running")
            
    def restart(self):
        self.stop()
        self.start()


    def status(self):
        print('The daemon is {status}'.format(
            status=self.get_status()
        ))

    def get_status(self):
        if self.running():
            return 'running'
        return 'stopped'

    def running(self):
        return self.pidfile and os.path.exists(self.pidfile)

    def prepare_dirs(self):
        """Ensure the log and pid file directories exist and are writable"""
        for fn in (self.pidfile, self.logfile):
            if not fn:
                continue
            parent = os.path.dirname(fn)
            if not os.path.exists(parent):
                os.makedirs(parent)
                self.chown(parent)

    def set_uid(self):
        """Drop root privileges"""
        if self.gid:
            try:
                os.setgid(self.gid)
            except OSError as err:
                sys.exit(
                    "can't setgid(%d): %s, %s" %
                    (self.gid, err.errno, err.strerror)
                )
        if self.uid:
            try:
                os.setuid(self.uid)
            except OSError as err:
                sys.exit(
                    "can't setuid(%d): %s, %s" %
                    (self.uid, err.errno, err.strerror)
                )

    def chown(self, fn):
        """Change the ownership of a file to match the daemon uid/gid"""
        if self.uid or self.gid:
            uid = self.uid
            if not uid:
                uid = os.stat(fn).st_uid
            gid = self.gid
            if not gid:
                gid = os.stat(fn).st_gid
            try:
                os.chown(fn, uid, gid)
            except OSError as err:
                sys.exit(
                    "can't chown(%s, %d, %d): %s, %s" %
                    (repr(fn), uid, gid, err.errno, err.strerror)
                )

    def start_logging(self):
        """Configure the logging module"""
        try:
            level = int(self.loglevel)
        except ValueError:
            try:
                level = int(logging.getLevelName(self.loglevel.upper()))
            except ValueError:
                level = getattr(logging, self.loglevel.upper(), logging.ERROR)

        handlers = []
        if self.logfile:
            if not self.logmaxmb:
                handlers.append(logging.FileHandler(self.logfile))
            else:
                from logging.handlers import RotatingFileHandler
                handlers.append(
                    RotatingFileHandler(
                        self.logfile,
                        maxBytes=self.logmaxmb * 1024 * 1024,
                        backupCount=self.logbackups
                    )
                )
            self.chown(self.logfile)
        if not self.args.daemonize:
            # also log to stderr
            handlers.append(logging.StreamHandler())

        log = logging.getLogger()
        log.setLevel(level)
        for h in handlers:
            h.setFormatter(logging.Formatter(
                "%(asctime)s %(process)d %(levelname)s %(message)s"))
            log.addHandler(h)

    def check_pid(self):
        """Check the pid file.

        Stop using sys.exit() if another instance is already running.
        If the pid file exists but no other instance is running,
        delete the pid file.
        """
        if not self.pidfile:
            return
        # based on twisted/scripts/twistd.py
        if os.path.exists(self.pidfile):
            try:
                pid = int(
                    open(self.pidfile, 'rb').read().decode('utf-8').strip()
                )
            except ValueError:
                msg = 'pidfile %s contains a non-integer value' % self.pidfile
                sys.exit(msg)
            try:
                os.kill(pid, 0)
            except OSError as err:
                if err.errno == errno.ESRCH:
                    # The pid doesn't exist, so remove the stale pidfile.
                    os.remove(self.pidfile)
                else:
                    msg = (
                        "failed to check status of process %s "
                        "from pidfile %s: %s" %
                        (pid, self.pidfile, err.strerror)
                    )
                    sys.exit(msg)
            else:
                msg = ('another instance seems to be running (pid %s), '
                       'exiting' % pid)
                sys.exit(msg)

    def check_pid_writable(self):
        """Verify the user has access to write to the pid file.

        Note that the eventual process ID isn't known until after
        daemonize(), so it's not possible to write the PID here.
        """
        if not self.pidfile:
            return
        if os.path.exists(self.pidfile):
            check = self.pidfile
        else:
            check = os.path.dirname(self.pidfile)
        if not os.access(check, os.W_OK):
            msg = 'unable to write to pidfile %s' % self.pidfile
            sys.exit(msg)

    def write_pid(self):
        """Write to the pid file"""
        if self.pidfile:
            open(self.pidfile, 'wb').write(str(os.getpid()).encode('utf-8'))

    def remove_pid(self):
        """Delete the pid file"""
        if self.pidfile and os.path.exists(self.pidfile):
            os.remove(self.pidfile)


def get_uid_gid(cp, section):
    """Get a numeric uid/gid from a configuration file.

    May return an empty uid and gid.
    """
    uid = cp.get(section, 'uid')
    if uid:
        try:
            uid = int(uid)
        except ValueError:
            # convert user name to uid
            try:
                uid = pwd.getpwnam(uid)[2]
            except KeyError:
                raise ValueError("user is not in password database: %s" % uid)

    gid = cp.get(section, 'gid')
    if gid:
        try:
            gid = int(gid)
        except ValueError:
            # convert group name to gid
            try:
                gid = grp.getgrnam(gid)[2]
            except KeyError:
                raise ValueError("group is not in group database: %s" % gid)

    return uid, gid


def daemonize():
    """Detach from the terminal and continue as a daemon"""
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0)  # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0)  # kill off parent again.
    os.umask(63)  # 077 in octal
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)
