#
# Copyright 2012-2025 Ghent University
#
# This file is part of vsc-utils,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# the Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/hpcugent/vsc-utils
#
# vsc-utils is free software: you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation, either version 2 of
# the License, or (at your option) any later version.
#
# vsc-utils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public License
# along with vsc-utils. If not, see <http://www.gnu.org/licenses/>.
#
"""
Tests for the vsc.utils.zabbix module.

@author: Andy Georges (Ghent University)
@author: Samuel Moors (Vrije Universiteit Brussel)
"""
import json
import os
import tempfile
import sys
import random
import string
from io import StringIO
from pwd import getpwuid

from vsc.install.testing import TestCase

from vsc.utils.zabbix import ZabbixReporter
from vsc.utils.nagios import NAGIOS_EXIT_OK, NAGIOS_EXIT_WARNING, NAGIOS_EXIT_CRITICAL, NAGIOS_EXIT_UNKNOWN


class TestZabbix(TestCase):
    """Test for the zabbix reporter class."""

    def setUp(self):
        user = getpwuid(os.getuid())
        self.nagios_user = user.pw_name
        super().setUp()

    def test_cache(self):
        """Test the caching mechanism in the reporter."""
        length = random.randint(1, 30)
        exit_code = random.randint(0, 3)
        threshold = random.randint(0, 10)

        message = ''.join(random.choice(string.printable) for x in range(length))
        message = message.rstrip()

        (handle, filename) = tempfile.mkstemp()
        os.unlink(filename)
        os.close(handle)
        reporter = ZabbixReporter('test_cache', filename, threshold, self.nagios_user)

        nagios_exit = [NAGIOS_EXIT_OK, NAGIOS_EXIT_WARNING, NAGIOS_EXIT_CRITICAL, NAGIOS_EXIT_UNKNOWN][exit_code]

        reporter.cache(nagios_exit, message)

        (handle, _) = tempfile.mkstemp()
        os.close(handle)

        try:
            old_stdout = sys.stdout
            buffer = StringIO()
            sys.stdout = buffer
            reporter_test = ZabbixReporter('test_cache', filename, threshold, self.nagios_user)
            reporter_test.report_and_exit()
        except SystemExit as err:
            line = buffer.getvalue().rstrip()
            sys.stdout = old_stdout
            buffer.close()
            self.assertEqual(err.code, nagios_exit[0])
            line = json.loads(line)
            self.assertEqual(line["exit_string"], nagios_exit[1])
            self.assertEqual(line["message"], message)

        os.unlink(filename)
