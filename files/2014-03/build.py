#! /usr/bin/env python

import argparse
import sys
import tbs

ARCH_CHOICES = ['x86_64']
ARCH_DEFAULT = ARCH_CHOICES[0]

CXX_CHOICES = ['clang++', 'g++']
CXX_DEFAULT = CXX_CHOICES[0]

OPT_CHOICES = ['0', '1', '3']
OPT_DEFAULT = OPT_CHOICES[2]

KERNEL, IMAGE = 'build/toy.bin', None
TARGET_DEFAULT = 'image'

SMP_DEFAULT = '2:2:2'


@tbs.command
def configure(args, env):
    """Configures build environment."""

    distclean(args, env, save_env=False)

    tbs.need([args.cxx, 'cpp', 'ld'])
    tbs.need('screen', False)

    env.update({'arch': args.arch, 'cxx': args.cxx, 'linker': 'ld'})

    flags = '-std=c++0x -Wall -Wextra -Wno-missing-field-initializers ' \
        '-ffreestanding -O%s -DARCH=%s -isystem src/std -Isrc ' % \
        (args.opt, args.arch)
    if args.debug:
        flags += '-DDEBUG '
    if args.arch == 'x86_64':
        env['cxx_flags_boot32'] = flags + '-m32'
        flags += '-m64'
    env['cxx_flags'] = flags

    env['linker_flags'] = '-z max-page-size=0x1'

    if args.arch == 'x86_64':
        env['emulator'] = 'qemu-system-x86_64'
        #tbs.need(['xorriso', 'grub-mkrescue'])
        tbs.need(env['emulator'], False)

    env.save()


tbs.add_arg(configure, '-a', dest='arch', choices=ARCH_CHOICES,
            default=ARCH_DEFAULT, help='CPU architecture')
tbs.add_arg(configure, '-c', dest='cxx', choices=CXX_CHOICES,
            default=CXX_DEFAULT, help='C++ compiler')
tbs.add_arg(configure, '-d', dest='debug', action='store_true',
            default=False, help='build binaries for debugging')
tbs.add_arg(configure, '-o', dest='opt', choices=OPT_CHOICES,
            default=OPT_DEFAULT, help='code optimization level')


@tbs.command
def distclean(args, env, save_env=True):
    """Cleans build environment and temporary files."""

    tbs.shell('distclean', 'rm -rf build')
    env.clear();
    if save_env:
        env.save()


def cdep(env, source):
    cmd = 'cpp %s -M -MT _ %s' % (env['cxx_flags'], source)
    out = tbs.shell('cdep', cmd, log_stdout=False)
    lst = out[1].replace('\\\n', '').split()[1:]
    tbs.log(tbs.NOTICE, 'cdep: %s' % lst)
    return lst


def build_objs_x86_64(env, srcs, objs):
    tbs.shell('build', 'mkdir -p build/src/%s' % env['arch'])
    boot32 = 'src/x86_64/boot32.cc'
    boot32_o32 = 'build/%s.32.o' % boot32
    boot32_o64 = 'build/%s.64.o' % boot32
    action = '{cxx} {cxx_flags_boot32} -c %s -o %s' % (boot32, boot32_o32)
    tbs.add_rule(boot32_o32, action, cdep(env, boot32))
    action = 'objcopy -O elf64-x86-64 %s %s' % (boot32_o32, boot32_o64)
    tbs.add_rule(boot32_o64, action, boot32_o32)
    objs.append(boot32_o64)
    srcs += tbs.files('src/%s/*.cc' % env['arch'], boot32)


def build_objs(env, srcs, objs):
    action = '{cxx} {cxx_flags} -c %s -o %s'
    for src in srcs:
        src_o = 'build/%s.o' % src
        tbs.add_rule(src_o, action % (src, src_o), cdep(env, src))
        objs.append(src_o)


def build_kernel(env, objs):
    lds, objs2 = 'src/%s/kernel.lds' % env['arch'], ' '.join(objs)
    action = '{linker} {linker_flags} -T%s %s -o %s' % (lds, objs2, KERNEL)
    tbs.add_rule(KERNEL, action, objs+[lds])


def build_img_x86_64(env):
    boot_dir = 'build/iso/boot'
    grub_dir = '%s/grub' % boot_dir
    tbs.shell('build', 'mkdir -p %s' % grub_dir)
    grub_cfg = 'src/x86_64/grub.cfg'

    def img_x86_64_action(target, sources, env):
        tbs.shell(target, 'cp %s %s/' % (grub_cfg, grub_dir))
        tbs.shell(target, 'cp %s %s/' % (KERNEL, boot_dir))
        tbs.shell(target, 'grub-mkrescue -o %s --diet build/iso 2>&1' % IMAGE)

    tbs.add_rule(IMAGE, img_x86_64_action, [grub_cfg, KERNEL])


@tbs.command
def build(args, env):
    """Builds project with configured environment."""

    if not env:
        tbs.log(tbs.ERROR, 'build: not configured')
        return

    global IMAGE
    srcs, objs = [], []
    if env['arch'] == 'x86_64':
        IMAGE = 'build/toy.iso'
        build_objs_x86_64(env, srcs, objs)
        build_img_x86_64(env)

    build_objs(env, srcs, objs)
    build_kernel(env, objs)

    tbs.build(args.target if args.target != TARGET_DEFAULT else IMAGE)


tbs.add_arg(build, '-t', dest='target', default=TARGET_DEFAULT,
            help='build target')


@tbs.command
def clean(args, env):
    """Cleans build temporary files."""
    tbs.shell('clean', 'rm -rf build')


@tbs.command
def run(args, env):
    """Runs built image on emulator."""

    args.target = TARGET_DEFAULT
    build(args, env)

    graphic = '' if args.graphic else '-curses '
    kvm = '' if args.kvm else '-no-kvm '
    smp = '-smp sockets=%s,cores=%s,threads=%s' % tuple(args.smp.split(':'))
    emulator = '%s%s' % ('' if args.graphic else 'screen ', env['emulator'])

    if env['arch'] == 'x86_64':
        success = tbs.shell('run', '%s -cdrom %s -boot d %s%s%s' %
                            (emulator, IMAGE, graphic, kvm, smp), False)


class SMPArgAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        message = "use format: 'sockets:cores:threads'"
        lst = values.split(':')
        if len(lst) != 3:
            raise argparse.ArgumentError(self, message)
        for e in lst:
            if not e.isdigit() or int(e) <= 0 or int(e) > 255:
                raise argparse.ArgumentError(self, message)
        setattr(namespace, 'smp', values)


tbs.add_arg(run, '-g', dest='graphic', action='store_true', default=False,
            help="use graphical mode")
tbs.add_arg(run, '--kvm', dest='kvm', action='store_true',
            default=False, help='use KVM for acceleration')
tbs.add_arg(run, '--smp', dest='smp', action=SMPArgAction, default=SMP_DEFAULT,
            help="SMP sockets, cores and threads")


tbs.process()
