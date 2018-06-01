#!/usr/bin/python3

#
# Copyright (C) 2018  Red Hat, Inc.
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

# This script runs a single kickstart test on a single system.  It takes
# command line arguments instead of environment variables because it is
# designed to be driven by run_kickstart_tests.sh via parallel.  It is
# not for direct use.

# Possible return values:
# 0  - Everything worked
# 1  - Test failed for unspecified reasons
# 2  - Test failed due to time out
# 3  - Test failed due to kernel panic
# 77 - Something needed by the test doesn't exist, so skip
# 99 - Test preparation failed


import os
import shutil
import subprocess

from lib.temp_manager import TempManager
from lib.configuration import RunnerConfiguration, VirtualConfiguration
from lib.shell_launcher import ShellLauncher
from lib.virtual_controller import VirtualManager
from lib.validator import KickstartValidator, LogValidator, ResultFormatter

import logging
log = logging.getLogger("livemedia-creator")


class Runner(object):

    def __init__(self, configuration, tmp_dir):
        super().__init__()
        self._conf = configuration
        self._tmp_dir = tmp_dir
        self._ks_file = None

        self._shell = ShellLauncher(configuration, tmp_dir)
        self._result_formatter = ResultFormatter(self._conf.ks_test_name)
        # test prepare function can change place of the kickstart test
        # so the validator will be set later
        self._validator = None

    def prepare_test(self):
        self._copy_image_to_tmp()

        try:
            shell_out = self._shell.run_prepare()
            shell_out.check_ret_code_with_exception()
            self._ks_file = shell_out.stdout
        except subprocess.CalledProcessError as e:
            self._result_formatter.print_result(result=False, msg="Test prep failed",
                                                description=e.stdout.decode())
            self._shell.run_cleanup()
            return False

        self._validator = KickstartValidator(self._conf.ks_test_name, self._ks_file)
        self._validator.check_ks_substitution()
        if self._validator.result is False:
            self._validator.print_result()
            self._shell.run_cleanup()
            return False

        return True

    def _copy_image_to_tmp(self):
        print("Copying image to temp directory {}".format(self._tmp_dir))
        shutil.copy2(self._conf.boot_image, self._tmp_dir)

    def run_test(self):
        if not self.prepare_test():
            return 99

        kernel_args = self._get_kernel_args()

        if self._conf.update_img_path:
            kernel_args.append("inst.updates={}".format(self._conf.updates_img_path))

        disk_args = self._collect_disks()
        nics_args = self._collect_network()
        boot_args = self._get_boot_args()

        v_conf = VirtualConfiguration(self._conf.boot_image, [self._ks_file])
        v_conf.kernel_args = kernel_args
        v_conf.test_name = self._conf.ks_test_name
        v_conf.temp_dir = self._tmp_dir
        v_conf.log_path = os.path.join(self._tmp_dir, "livemedia.log")
        v_conf.ram = 1024
        v_conf.vnc = "vnc"
        v_conf.boot_image = boot_args
        v_conf.timeout = 60
        v_conf.disk_paths = disk_args
        v_conf.networks = nics_args

        virt_manager = VirtualManager(v_conf)

        if not virt_manager.run():
            return 1

        validator = self._validate_logs(v_conf)

        if not validator.result:
            validator.log_result()
            validator.print_result()
            self._shell.run_cleanup()
            return validator.return_code

        ret = self._validate_result()
        if ret.check_ret_code():
            self._result_formatter.print_result(True, "test done")

        self._shell.run_cleanup()
        return ret.return_code

    def _collect_disks(self):
        ret = []

        out = self._shell.run_prepare_disks()
        out.check_ret_code_with_exception()

        for d in out.stdout_as_array:
            ret.append("{},cache=unsafe".format(d))

        return ret

    def _collect_network(self):
        ret = []

        out = self._shell.run_prepare_network()
        out.check_ret_code_with_exception()

        for n in out.stdout_as_array:
            ret.append("--nic")
            ret.append(n)

        return ret

    def _get_runner_args(self):
        ret = []

        out = self._shell.run_additional_runner_args()
        out.check_ret_code_with_exception()
        for arg in out.stdout_as_array:
            ret.append(arg)

        return ret

    def _get_kernel_args(self):
        out = self._shell.run_kernel_args()

        out.check_ret_code_with_exception()
        return out.stdout

    def _get_boot_args(self):
        out = self._shell.run_boot_args()

        out.check_ret_code_with_exception()
        return out.stdout_as_array

    def _validate_logs(self, virt_configuration):
        validator = LogValidator(self._conf.ks_test_name, log)
        validator.check_install_errors(virt_configuration.install_logpath)

        if validator.result:
            validator.check_virt_errors(virt_configuration.log_path)

        return validator

    def _validate_result(self):
        output = self._shell.run_validate()

        if not output.check_ret_code():
            msg = "with return code {}".format(output.return_code)
            description = "stdout: '{}' stderr: '{}'".format(output.stdout,
                                                             output.stderr)
            self._result_formatter.print_result(False, msg, description)

        return output


if __name__ == '__main__':
    config = RunnerConfiguration()

    config.process_argument()

    with TempManager(config.keep_level, config.ks_test_name) as temp_dir:
        runner = Runner(config, temp_dir)
        runner.prepare_test()
        ret_code = runner.run_test()

    exit(ret_code)