#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, Cédric Krier
# Copyright (c) 2015, B2CK
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"Test isonasacs"
import unittest
import datetime
from mock import Mock

from isonasacs import Isonasacs, IsonasacsError
from isonasacs import get_datetime, get_type, is_notification, split_values


class TestISONASACS(unittest.TestCase):

    def setUp(self):
        _Telnet = Mock()
        self._telnet = _Telnet()
        self._telnet.read_until.return_value = '<LOGON>'
        self.isonasacs = Isonasacs('localhost', 7101, _Telnet=_Telnet)
        self._telnet.reset_mock()

    def test_logon(self):
        self._telnet.read_until.return_value = '<LOGON ACCEPTED>|'
        self.isonasacs.logon('clientid', 'password')
        self._telnet.write.assert_called_once_with(
            '<LOGON><clientid><password>|')

    def test_logon_failure(self):
        self._telnet.read_until.return_value = '<ERROR>Access Denied|'
        self.assertRaises(IsonasacsError,
            self.isonasacs.logon, 'clientid', 'wrongpassword')

    def test_add(self):
        self._telnet.read_until.return_value = '<ACK>|'
        self.isonasacs.add('IDFILE', 'LastName', 'ID')
        self._telnet.write.assert_called_once_with(
            '<ADD><IDFILE><LastName><ID>|')

    def test_add_failure(self):
        self._telnet.read_until.return_value = '<ERROR>|'
        self.assertRaises(IsonasacsError, self.isonasacs.add, 'foo')

    def test_delete(self):
        self._telnet.read_until.return_value = '<ACK>|'
        self.isonasacs.delete('IDFILE', 'ID')
        self._telnet.write.assert_called_once_with(
            '<DELETE><IDFILE><ID>|')

    def test_update(self):
        self._telnet.read_until.return_value = '<ACK>|'
        self.isonasacs.update('IDFILE', 'ID', 'LastName')
        self._telnet.write.assert_called_once_with(
            '<UPDATE><IDFILE><ID><LastName>|')

    def test_query_all(self):
        self._telnet.read_until.side_effect = [
            '<ALL IDFILE><1>|', '<ALL IDFILE><2>|', '<ALL IDFILE><3>|',
            '<END IDFILE>|']
        self.assertEqual(self.isonasacs.query_all('IDFILE'),
            [['1'], ['2'], ['3']])
        self._telnet.write.assert_called_once_with(
            '<QUERY><ALL IDFILE>|')

    def test_query(self):
        self._telnet.read_until.return_value = (
            '<IDFILE><LastName><FirstName><Initial><1>|')
        self.assertEqual(self.isonasacs.query('IDFILE', '1'),
            ['LastName', 'FirstName', 'Initial', '1'])
        self._telnet.write.assert_called_once_with(
            '<QUERY><IDFILE><1>|')

    def test_query_group(self):
        self._telnet.read_until.side_effect = [
            '<GROUP><group><1>|', '<GROUP><group><2>|', '<END GROUP>|']
        self.assertEqual(self.isonasacs.query('GROUP', 'group'),
            [['group', '1'], ['group', '2']])
        self._telnet.write.assert_called_once_with(
            '<QUERY><GROUP><group>|')


class TestTools(unittest.TestCase):

    def test_get_datetime(self):
        self.assertEqual(get_datetime('< 8/17/2015><10:15:00><MESSAGE>'),
            (datetime.datetime(2015, 8, 17, 10, 15), '<MESSAGE>'))

    def test_get_type(self):
        self.assertEqual(get_type('<LOGON ACCEPTED>'), 'LOGON ACCEPTED')

    def test_is_notification(self):
        self.assertTrue(is_notification('<REJECT><DoorName>'))

    def test_split_values(self):
        self.assertEqual(split_values('<1><foo><><foo bar><><><>'),
            ['1', 'foo', '', 'foo bar', '', '', ''])
        self.assertEqual(split_values(
                '<1><{00000000-0000-0000-0000-000000000000}>'),
            ['1', '{00000000-0000-0000-0000-000000000000}'])

if __name__ == '__main__':
    unittest.main()
