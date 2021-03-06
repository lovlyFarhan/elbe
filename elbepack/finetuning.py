# ELBE - Debian Based Embedded Rootfilesystem Builder
# Copyright (C) 2013  Linutronix GmbH
#
# This file is part of ELBE.
#
# ELBE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ELBE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ELBE.  If not, see <http://www.gnu.org/licenses/>.

import os

from apt.package import FetchError
from shutil import rmtree

from elbepack.aptpkgutils import XMLPackage
from elbepack.filesystem import ChRootFilesystem
from elbepack.repomanager import UpdateRepo
from elbepack.rpcaptcache import get_rpcaptcache
from elbepack.shellhelper import CommandError

class FinetuningAction(object):

    actiondict = {}

    @classmethod
    def register(cls, action):
        cls.actiondict[action.tag] = action

    def __new__(cls, node):
        action = cls.actiondict[node.tag]
        return object.__new__(action, node)

    def __init__(self, node):
        self.node = node


class RmAction(FinetuningAction):

    tag = 'rm'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "rm -rvf " + target.fname( self.node.et.text ) )

FinetuningAction.register( RmAction )


class MkdirAction(FinetuningAction):

    tag = 'mkdir'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "mkdir -p " + target.fname( self.node.et.text ) )

FinetuningAction.register( MkdirAction )

class MknodAction(FinetuningAction):

    tag = 'mknod'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "mknod " + target.fname( self.node.et.text ) + " " + self.node.et.attrib['opts'] )

FinetuningAction.register( MknodAction )

class BuildenvMkdirAction(FinetuningAction):

    tag = 'buildenv_mkdir'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "mkdir -p " + buildenv.fname( self.node.et.text ) )

FinetuningAction.register( BuildenvMkdirAction )


class CpAction(FinetuningAction):

    tag = 'cp'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "cp -av " + target.fname( self.node.et.attrib['path'] ) + " " + target.fname( self.node.et.text ) )

FinetuningAction.register( CpAction )

class BuildenvCpAction(FinetuningAction):

    tag = 'buildenv_cp'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "cp -av " + buildenv.fname( self.node.et.attrib['path'] ) + " " + buildenv.fname( self.node.et.text ) )

FinetuningAction.register( BuildenvCpAction )

class B2TCpAction(FinetuningAction):

    tag = 'b2t_cp'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "cp -av " + buildenv.fname( self.node.et.attrib['path'] ) + " " + target.fname( self.node.et.text ) )

FinetuningAction.register( B2TCpAction )

class T2BCpAction(FinetuningAction):

    tag = 't2b_cp'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "cp -av " + target.fname( self.node.et.attrib['path'] ) + " " + buildenv.fname( self.node.et.text ) )

FinetuningAction.register( T2BCpAction )

class MvAction(FinetuningAction):

    tag = 'mv'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "mv -v " + target.fname( self.node.et.attrib['path'] ) + " " + target.fname( self.node.et.text ) )

FinetuningAction.register( MvAction )

class LnAction(FinetuningAction):

    tag = 'ln'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.chroot (target.path, "ln -s %s %s" % (self.node.et.attrib['path'],
                                                  self.node.et.text))

FinetuningAction.register( LnAction )


class BuildenvMvAction(FinetuningAction):

    tag = 'buildenv_mv'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        log.do( "mv -v " + buildenv.fname( self.node.et.attrib['path'] ) + " " + buildenv.fname( self.node.et.text ) )

FinetuningAction.register( BuildenvMvAction )


class AddUserAction(FinetuningAction):

    tag = 'adduser'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
      with target:
        if 'groups' in self.node.et.attrib:
          log.chroot (target.path, "/usr/sbin/useradd -U -m -G %s -s %s %s" % (
                self.node.et.attrib['groups'],
                self.node.et.attrib['shell'],
                self.node.et.text))
        else:
          log.chroot (target.path, "/usr/sbin/useradd -U -m -s %s %s" % (
                self.node.et.attrib['shell'], self.node.et.text))

        log.chroot( target.path,
             """/bin/sh -c 'echo "%s\\n%s\\n" | passwd %s'""" % (
                           self.node.et.attrib['passwd'],
                           self.node.et.attrib['passwd'],
                           self.node.et.text))

FinetuningAction.register( AddUserAction )


class AddGroupAction(FinetuningAction):

    tag = 'addgroup'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
      with target:
        log.chroot (target.path, "/usr/sbin/groupadd -f %s" % (
            self.node.et.text))

FinetuningAction.register( AddGroupAction )

class RawCmdAction(FinetuningAction):

    tag = 'raw_cmd'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        with target:
            log.chroot (target.path, self.node.et.text)

FinetuningAction.register( RawCmdAction )

class CmdAction(FinetuningAction):

    tag = 'command'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        with target:
            log.chroot (target.path, "/bin/sh", input=self.node.et.text)

FinetuningAction.register( CmdAction )

class BuildenvCmdAction(FinetuningAction):

    tag = 'buildenv_command'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        with buildenv:
            log.chroot (buildenv.path, "/bin/sh", input=self.node.et.text)

FinetuningAction.register( BuildenvCmdAction )

class PurgeAction(FinetuningAction):

    tag = 'purge'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):
        with target:
            log.chroot (target.path, "dpkg --purge " + self.node.et.text)

FinetuningAction.register( PurgeAction )

class UpdatedAction(FinetuningAction):

    tag = 'updated'

    def __init__(self, node):
        FinetuningAction.__init__(self, node)

    def execute(self, log, buildenv, target):

        log.printo( "generate base repo")
        arch = target.xml.text ("project/arch", key="arch")
        rfs = ChRootFilesystem (target.path)
        with rfs:
            rfs.mkdir_p ('/tmp/pkgs')
            cache = get_rpcaptcache (rfs, "updated-repo.log", arch)
            for p in target.xml.node ("fullpkgs"):
                pkg = XMLPackage (p, arch)
                print pkg
                try:
                    cache.download_binary (pkg.name, '/tmp/pkgs',
                            pkg.installed_version)
                except ValueError as ve:
                    log.printo( "No Package " + pkg.name + "-" + pkg.installed_version )
                except FetchError as fe:
                    log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " could not be downloaded" )
                except TypeError as te:
                    log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " missing name or version" )

            r = UpdateRepo (target.xml,
                  target.path + '/var/cache/elbe/repos/base',
                  log)

            for d in target.glob ('tmp/pkgs/*.deb'):
                r.includedeb (d, 'main')

            slist = target.path + '/etc/apt/sources.list.d/base.list'
            slist_txt = 'deb file:///var/cache/elbe/repos/base '
            slist_txt += target.xml.text ("/project/suite")
            slist_txt += " main"
            with open (slist, 'w') as apt_source:
                apt_source.write (slist_txt)

            rmtree (target.path + '/tmp/pkgs')


FinetuningAction.register( UpdatedAction )


def do_finetuning(xml, log, buildenv, target):

    if not xml.has('target/finetuning'):
        return

    for i in xml.node('target/finetuning'):
        try:
            action = FinetuningAction( i )
            action.execute(log, buildenv, target)
        except KeyError:
            print "Unimplemented finetuning action " + i.et.tag
        except CommandError:
            log.printo( "Finetuning Error, trying to continue anyways" )
