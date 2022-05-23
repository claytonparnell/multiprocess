#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Copyright (c) 2008-2016 California Institute of Technology.
# Copyright (c) 2016-2022 The Uncertainty Quantification Foundation.
# License: 3-clause BSD.  The full license text is available at:
#  - https://github.com/uqfoundation/multiprocess/blob/master/LICENSE
#
# original code modified from processing/setup.py
# original: Copyright (c) 2006-2008, R Oudkerk
# original: Licence 3-clause BSD.  The full license text is available at:
# - https://github.com/uqfoundation/multiprocess/blob/master/COPYING.txt

import re
import os
import sys
import glob
# drop support for older python
unsupported = None
if sys.version_info < (2, 7):
    unsupported = 'Versions of Python before 2.7 are not supported'
elif (3, 0) <= sys.version_info < (3, 7):
    unsupported = 'Versions of Python before 3.7 are not supported'
if unsupported:
    raise ValueError(unsupported)

is_jython = sys.platform.startswith('java')
is_pypy = hasattr(sys, 'pypy_version_info')
is_py3k = sys.version_info[0] == 3
lt_py33 = sys.version_info < (3, 3)

# the code is version-specific, so get the appropriate root directory
root = 'pypy' if is_pypy else 'py'
pymajor,pyminor = sys.version_info[:2]
pkgdir = '%s%s.%s' % (root,pymajor,pyminor)
pkgname = 'multiprocess'
# if sys.version is higher than explicitly supported, try the latest version
HERE = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(HERE,'%s%s.%s' % (root,pymajor,pyminor))):
    pyminor -= 1
    if pyminor < 0:
        unsupported = 'Python %s is not supported' % pkgdir[len(root):]
        raise ValueError(unsupported)
if '%s%s.%s' % (root,pymajor,pyminor) != pkgdir:
    msg = 'Warning: Python %s is not currently supported, reverting to %s.%s'
    print(msg % (pkgdir[len(root):],pymajor,pyminor))
    pkgdir = '%s%s.%s' % (root,pymajor,pyminor)
srcdir = '%s/Modules/_%s' % (pkgdir, pkgname)
libdir = '%s/%s' % (pkgdir, pkgname)

# -*- Distribution Meta -*-
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, '%s/__init__.py' % libdir))
try:
    meta = {}
    for line in meta_fh:
        if line.startswith('__version__'):
            VERSION = line.split()[-1].strip("'").strip('"')
            break
    meta['VERSION'] = VERSION
    for line in meta_fh:
        if line.startswith('__author__'):
            AUTHOR = line.split(' = ')[-1].strip().strip("'").strip('"')
            break
    meta['AUTHOR'] = AUTHOR
    LONG_DOC = ""
    DOC_STOP = "FAKE_STOP_12345"
    for line in meta_fh:
        if LONG_DOC:
            if line.startswith(DOC_STOP):
                LONG_DOC = LONG_DOC.strip().strip("'").strip('"').lstrip()
                break
            else:
                LONG_DOC += line
        elif line.startswith('__doc__'):
            DOC_STOP = line.split(' = ')[-1]
            LONG_DOC = "\n"
    meta['LONG_DOC'] = LONG_DOC
finally:
    meta_fh.close()

# get version numbers, long_description, etc
AUTHOR = meta['AUTHOR']
VERSION = meta['VERSION']
LONG_DOC = meta['LONG_DOC'] #FIXME: near-duplicate of README.md
#LICENSE = meta['LICENSE'] #FIXME: duplicate of LICENSE
AUTHOR_EMAIL = 'mmckerns@uqfoundation.org'

# check if setuptools is available
try:
    from setuptools import setup, Extension, find_packages
    from setuptools.dist import Distribution
    has_setuptools = True
except ImportError:
    from distutils.core import setup, Extension  # noqa
    Distribution = object
    find_packages = lambda **kwds: [pkgname, pkgname+'.dummy', pkgname+'.tests']
    has_setuptools = False
from distutils import sysconfig
from distutils.errors import CCompilerError, DistutilsExecError, \
                                             DistutilsPlatformError

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32' and sys.version_info >= (2, 6):
    # distutils.msvc9compiler can raise IOError if the compiler is missing
    ext_errors += (IOError, )

BUILD_WARNING = """

-----------------------------------------------------------------------
WARNING: The C extensions could not be compiled
-----------------------------------------------------------------------

Maybe you do not have a C compiler installed on this system?
The reason was:
%s

This is just a warning as most of the functionality will work even
without the updated C extension.  It will simply fallback to the
built-in _multiprocessing module.  Most notably you will not be able to use
FORCE_EXECV on POSIX systems.  If this is a problem for you then please
install a C compiler or fix the error(s) above.
-----------------------------------------------------------------------

"""
#
# Macros and libraries
#
#   The `macros` dict determines the macros that will be defined when
#   the C extension is compiled.  Each value should be either 0 or 1.
#   (An undefined macro is assumed to have value 0.)  `macros` is only
#   used on Unix platforms.
#
#   The `libraries` dict determines the libraries to which the C
#   extension will be linked.  This should probably be either `['rt']`
#   if you need `librt` or else `[]`.
#
# Meaning of macros
#
#   HAVE_SEM_OPEN
#     Set this to 1 if you have `sem_open()`.  This enables the use of
#     posix named semaphores which are necessary for the
#     implementation of the synchronization primitives on Unix.  If
#     set to 0 then the only way to create synchronization primitives
#     will be via a manager (e.g. "m = Manager(); lock = m.Lock()").
#     
#   HAVE_SEM_TIMEDWAIT
#     Set this to 1 if you have `sem_timedwait()`.  Otherwise polling
#     will be necessary when waiting on a semaphore using a timeout.
#     
#   HAVE_FD_TRANSFER
#     Set this to 1 to compile functions for transferring file
#     descriptors between processes over an AF_UNIX socket using a
#     control message with type SCM_RIGHTS.  On Unix the pickling of 
#     of socket and connection objects depends on this feature.
#
#     If you get errors about missing CMSG_* macros then you should
#     set this to 0.
# 
#   HAVE_BROKEN_SEM_GETVALUE
#     Set to 1 if `sem_getvalue()` does not work or is unavailable.
#     On Mac OSX it seems to return -1 with message "[Errno 78]
#     Function not implemented".
#
#   HAVE_BROKEN_SEM_UNLINK
#     Set to 1 if `sem_unlink()` is unnecessary.  For some reason this
#     seems to be the case on Cygwin where `sem_unlink()` is missing
#     from semaphore.h.
#

if sys.platform == 'win32':  # Windows
    macros = dict()
    libraries = ['ws2_32']
elif sys.platform.startswith('darwin'):  # Mac OSX
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        HAVE_BROKEN_SEM_GETVALUE=1
        )
    libraries = []
elif sys.platform.startswith('cygwin'):  # Cygwin
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=0,
        HAVE_BROKEN_SEM_UNLINK=1
        )
    libraries = []
elif sys.platform in ('freebsd4', 'freebsd5', 'freebsd6'):
    # FreeBSD's P1003.1b semaphore support is very experimental
    # and has many known problems. (as of June 2008)
    macros = dict(                  # FreeBSD 4-6
        HAVE_SEM_OPEN=0,
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        )
    libraries = []
elif re.match('^(gnukfreebsd(8|9|10|11)|freebsd(7|8|9|10))', sys.platform):
    macros = dict(                  # FreeBSD 7+ and GNU/kFreeBSD 8+
        HAVE_SEM_OPEN=bool(
            sysconfig.get_config_var('HAVE_SEM_OPEN') and not
            bool(sysconfig.get_config_var('POSIX_SEMAPHORES_NOT_ENABLED'))
        ),
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=1,
    )
    libraries = []
elif sys.platform.startswith('openbsd'):
    macros = dict(                  # OpenBSD
        HAVE_SEM_OPEN=0,            # Not implemented
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
    )
    libraries = []
else:                                   # Linux and other unices
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=1,
    )
    libraries = ['rt']

if sys.platform == 'win32':
    multiprocessing_srcs = [
        '%s/%s.c' % (srcdir, pkgname),
        '%s/semaphore.c' % srcdir,
    ]
    if lt_py33:
        multiprocessing_srcs += [
            '%s/pipe_connection.c' % srcdir,
            '%s/socket_connection.c' % srcdir,
            '%s/win32_functions.c' % srcdir,
        ]
else:
    multiprocessing_srcs = [ '%s/%s.c' % (srcdir, pkgname) ]
    if lt_py33:
        multiprocessing_srcs.append('%s/socket_connection.c' % srcdir)

    if macros.get('HAVE_SEM_OPEN', False):
        multiprocessing_srcs.append('%s/semaphore.c' % srcdir)

#meta['long_doc'] = open(os.path.join(HERE, 'README.md')).read()
#if not is_py3k:
#    meta['long_doc'] = meta['long_doc'].encode('ascii', 'replace')

# -*- Installation -*-
def _is_build_command(argv=sys.argv, cmds=('install', 'build', 'bdist')):
    for arg in argv:
        if arg.startswith(cmds):
            return arg

# force python-, abi-, and platform-specific naming of bdist_wheel
class BinaryDistribution(Distribution):
    """Distribution which forces a binary package with platform name"""
    def has_ext_modules(foo):
        return True

# define dependencies
dill_version = 'dill>=0.3.5.1'

def run_setup(with_extensions=True):
    extensions = []
    if with_extensions:
        extensions = [
            Extension(
                '_%s' % pkgname,
                sources=multiprocessing_srcs,
                define_macros=list(macros.items()),
                libraries=libraries,
                include_dirs=[srcdir],
                depends=glob.glob('%s/*.h' % srcdir) + ['setup.py'],
            ),
        ]
    packages = find_packages(
        where=pkgdir,
        exclude=['ez_setup', 'examples', 'doc',],
        )
    # build the 'setup' call
    setup_kwds = dict(
        name='multiprocess',
        version=VERSION,
        description=('better multiprocessing and multithreading in python'),
        long_description=LONG_DOC,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=AUTHOR,
        maintainer_email=AUTHOR_EMAIL,
        license='3-clause BSD',
        platforms = ['Linux', 'Windows', 'Mac'],
        url='https://github.com/uqfoundation/multiprocess',
        download_url = 'https://pypi.org/project/multiprocess/#files',
        project_urls = {
            'Documentation':'http://multiprocess.rtfd.io',
            'Source Code':'https://github.com/uqfoundation/multiprocess',
            'Bug Tracker':'https://github.com/uqfoundation/multiprocess/issues',
        },
        python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: Scientific/Engineering',
            'Topic :: Software Development',
        ],
        packages=packages,
        package_dir={'': pkgdir},
        ext_modules=extensions,
    )
    # add dependencies
    depend = [dill_version]
    extras = {'dill': [dill_version]}
    # update setup kwds
    if has_setuptools:
        setup_kwds.update(
            zip_safe=False,
            distclass=BinaryDistribution,
            install_requires=depend,
            # extras_require=extras,
        )
    # call setup
    setup(**setup_kwds)

try:
    run_setup(not (is_jython or is_pypy) and lt_py33)
except BaseException:
    if _is_build_command(sys.argv): #XXX: skip WARNING if is_pypy?
        import traceback
        msg = BUILD_WARNING % '\n'.join(traceback.format_stack())
        if not is_py3k:
            exec('print >> sys.stderr, msg')
        else:
            exec('print(msg, file=sys.stderr)')
        run_setup(False)
    else:
        raise

# if dependencies are missing, print a warning
try:
    import dill
except ImportError:
    print("\n***********************************************************")
    print("WARNING: One of the following dependencies is unresolved:")
    print("    %s" % dill_version)
    print("***********************************************************\n")


if __name__=='__main__':
    pass

# end of file
