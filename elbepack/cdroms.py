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
from elbepack.rpcaptcache import get_rpcaptcache
from elbepack.repomanager import CdromSrcRepo
from elbepack.repomanager import CdromBinRepo
from elbepack.aptpkgutils import XMLPackage

CDROM_SIZE = 640*1000*1000

def mk_source_cdrom(rfs, arch, codename, target, log):

    rfs.mkdir_p( '/var/cache/elbe/sources' )

    cache = get_rpcaptcache( rfs, "aptcache.log", arch )

    pkglist = cache.get_installed_pkgs()

    for pkg in pkglist:
        try:
            cache.download_source( pkg.name, '/var/cache/elbe/sources' )
        except ValueError as ve:
            log.printo( "No sources for Package " + pkg.name + "-" + pkg.installed_version )
        except FetchError as fe:
            log.printo( "Source for Package " + pkg.name + "-" + pkg.installed_version + " could not be downloaded" )

    repo = CdromSrcRepo(codename, os.path.join(target, "srcrepo" ), log, CDROM_SIZE )

    for dsc in rfs.glob('var/cache/elbe/sources/*.dsc'):
        repo.includedsc(dsc)

    repo.buildiso( os.path.join( target, "src-cdrom.iso" ) )

def mk_binary_cdrom(rfs, arch, codename, xml, target, log):

    rfs.mkdir_p( '/var/cache/elbe/binaries/added' )
    rfs.mkdir_p( '/var/cache/elbe/binaries/main' )

    cache = get_rpcaptcache( rfs, "aptcache.log", arch )

    pkglist = cache.get_installed_pkgs()

    for pkg in pkglist:
        try:
            cache.download_binary( pkg.name, '/var/cache/elbe/binaries/added', pkg.installed_version )
        except ValueError as ve:
            log.printo( "No Package " + pkg.name + "-" + pkg.installed_version )
        except FetchError as fe:
            log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " could not be downloaded" )
        except TypeError as te:
            log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " missing name or version" )

    if not xml is None:
        for p in xml.node("debootstrappkgs"):
            pkg = XMLPackage(p, arch)
            try:
                cache.download_binary( pkg.name, '/var/cache/elbe/binaries/main', pkg.installed_version )
            except ValueError as ve:
                log.printo( "No Package " + pkg.name + "-" + pkg.installed_version )
            except FetchError as fe:
                log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " could not be downloaded" )
            except TypeError as te:
                log.printo( "Package " + pkg.name + "-" + pkg.installed_version + " missing name or version" )

    repo = CdromBinRepo(xml, os.path.join( target, "binrepo" ), log, CDROM_SIZE )

    for deb in rfs.glob('var/cache/elbe/binaries/added/*.deb'):
        repo.includedeb(deb, 'added')

    for deb in rfs.glob('var/cache/elbe/binaries/main/*.deb'):
        repo.includedeb(deb, 'main')

    repo.buildiso( os.path.join( target, "bin-cdrom.iso" ) )
