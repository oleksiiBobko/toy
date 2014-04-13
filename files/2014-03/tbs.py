import __main__
import argparse
import glob
import json
import os.path
import platform
import subprocess
import sys

VERBOSE_CHOICES = range(0, 4)
VERBOSE_DEFAULT = 2

if hasattr(__main__, '__file__'):
    ENV_FILENAME = '.%s.env' % os.path.basename(__main__.__file__)
else:
    ENV_FILENAME = '.tbs.env'


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()


if sys.version_info[0] == 3:
    def is_str(obj): return isinstance(obj, str)
else:
    def is_str(obj): return isinstance(obj, basestring)


def add_arg(command, name, **args):
    if 'default' in args and 'help' in args:
        args['help'] += " [default: '%s']" % args['default']
    p = command.__arg_parser__ if command else parser
    p.add_argument(name, **args)


add_arg(None, '-v', dest='verbose', type=int, choices=VERBOSE_CHOICES,
        default=VERBOSE_DEFAULT, help='verbose level')


def command(func):
    func.__arg_parser__ = \
        subparsers.add_parser(func.__name__, help=func.__doc__)
    func.__arg_parser__.set_defaults(func=func)
    return func


def log(severity, message):
    if severity <= args.verbose:
        print(log_templates[severity] % message)


ERROR, WARNING, INFO, NOTICE = 0, 1, 2, 3


if platform.system() in ('Linux', 'Darwin'):
    log_templates = [ '\033[91m%s\033[0m', '\033[93m%s\033[0m',
                      '\033[92m%s\033[0m', '\033[95m%s\033[0m' ]
else:
    log_templates = [ '%s', '%s', '%s', '%s' ]


class Env(dict):
    def __init__(self, filename=ENV_FILENAME):
        self.filename = filename
        self.load()

    def load(self):
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as f:
                dict.__init__(self, json.load(f))
        log(NOTICE, 'Loaded env: %s' % self)

    def save(self):
        if self:
            with open(self.filename, 'w+') as f:
                json.dump(self, f)
        elif os.path.isfile(self.filename):
            os.remove(self.filename)
        log(NOTICE, 'Saved env: %s' % self)


def shell(target, command, raise_error=True, log_stdout=True, log_stderr=True):
    log(NOTICE, "%s: executing '%s'" % (target, command))
    p = subprocess.Popen(command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = list(map(lambda s: s.decode('utf-8').strip(), p.communicate()))
    if out[0] and log_stdout:
        log(NOTICE, out[0])
    if out[1] and log_stderr:
        log(WARNING, out[1])
    if p.returncode and raise_error:
        raise TbsError('%s: failed' % target)
    return (p.returncode, out[0], out[1])


def need(commands, mandatory=True):
    if is_str(commands):
        commands = [commands]
    for command in commands:
        if shell('need', 'which %s' % command, False)[0]:
            message = "need: '%s' is not found" % command
            if mandatory:
                raise TbsError(message)
            log(WARNING, message)
        else:
            log(INFO, "need: '%s' is found" % command)


class TbsError(Exception):
    pass


class Builder:
    targets = {}

    def __init__(self, target, action=None, sources=[], env=None):
        self.target = target
        self.env = env if env else _env
        self.action = action.format(**self.env) if is_str(action) else action
        self.sources = [sources] if is_str(sources) else sources
        for s in self.sources:
            if s not in Builder.targets:
                Builder(s)
        Builder.targets[target] = self

    def build_sources(self):
        return list(map(lambda s: Builder.targets[s](), self.sources))

    def __call__(self):
        if not self.action:
            if not os.path.isfile(self.target):
                raise TbsError("%s: file not found" % self.target)
            return os.path.getmtime(self.target)
        elif not self.sources:
            rebuild = True
        else:
            stamps = self.build_sources()
            rebuild = not os.path.isfile(self.target)
            if not rebuild:
                mtime = os.path.getmtime(self.target)
                for s in stamps:
                    if s > mtime:
                        rebuild = True
                        break

        if rebuild:
            if callable(self.action):
                log(NOTICE, "%s: calling '%s'" %
                    (self.target, self.action.__name__))
                self.action(self.target, self.sources, self.env)
                log(INFO, '%s: success' % self.target)
            elif is_str(self.action):
                shell(self.target, self.action)
                log(INFO, '%s: success' % self.target)
            else:
                raise TbsError('%s: no action provided' % self.target)
            return os.path.getmtime(self.target)
        else:
            log(NOTICE, '%s: up to date' % self.target)
            return mtime


def add_rule(target, action=None, sources=[], env=None):
    Builder(target, action, sources, env)


def build(target):
    if target not in Builder.targets:
        raise TbsError('%s: unknown target' % target)
    Builder.targets[target]()


def files(incl_masks, excl_masks=[]):
    def file_set(masks):
        if is_str(masks):
            masks = [masks]
        files = set()
        for mask in masks:
            files |= set(glob.glob(mask))
        return files

    return list(file_set(incl_masks) - file_set(excl_masks))


def process():
    global args, _env
    args = parser.parse_args()
    _env = Env()
    try:
        args.func(args, _env)
        log(INFO, '%s: succeeded' % args.func.__name__)
    except TbsError as e:
        log(ERROR, str(e))
        log(ERROR, '%s: failed' % args.func.__name__)
