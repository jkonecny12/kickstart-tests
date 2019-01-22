#!/usr/bin/python3

#
# Copyright (C) 2019  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Jiri Konecny <jkonecny@redhat.com>

from pylorax.mount import IsoMountpoint
from lib.utils import is_dry_run, disable_on_dry_run


class IsoDeviceException(Exception):
    """Exception specific to IsoDev class usage."""
    pass


class IsoDev(object):
    def __init__(self, iso_path, dest_location):
        """This class will handle all interaction with a boot ISO."""
        self._iso_path = iso_path
        self._dest_location = dest_location
        self._iso_mount = None

    @property
    def iso_path(self):
        return self._iso_path

    @property
    def dest_location(self):
        return self._dest_location

    @property
    def stage2(self):
        if not self._iso_mount:
            if is_dry_run():
                return "dry-run-mode"
            else:
                raise IsoDeviceException("To read stage2 name you have to mount the ISO.")

        return self._iso_mount.stage2

    @property
    def label(self):
        if not self._iso_mount:
            if is_dry_run():
                return "dry-run-mode"
            else:
                raise IsoDeviceException("To read label you have to mount the ISO.")

        return self._iso_mount.label

    @disable_on_dry_run
    def mount(self):
        self._iso_mount = IsoMountpoint(self.iso_path, self._dest_location)

    @disable_on_dry_run
    def unmount(self):
        self._iso_mount.umount()
