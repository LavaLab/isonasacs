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
"a library to communicate with ISONAS Access Control System"
__version__ = '0.3'
__all__ = ['Isonasacs', 'IsonasacsError']

import datetime
import re
from telnetlib import Telnet

_DATETIME_RE = re.compile(r"""
    <(?P<month>\s*\d{1,2})/(?P<day>\s*\d{1,2})/(?P<year>\d{4})>
    <(?P<hour>\s*\d{1,2}):(?P<minute>\s*\d{1,2}):(?P<second>\s*\d{1,2})>
    (?P<message>.*)""", re.X)
_TYPE_RE = re.compile(r'<(?P<type>[A-Z ]+)>')
_VALUES_RE = re.compile(r'<([a-zA-Z0-9{}\-_ ]*)>')

NOTIFICATIONS = {'REJECT', 'ADMIT', 'UNAUTHORIZED OPEN', 'TAMPER', 'AUX',
    'REX', 'EXTENDED OPEN', 'CONTROLLER FAILURE', 'LOCKDOWN', 'UNLOCKED',
    'NORMAL RESET', 'REJECT PASSBACK', 'REJECT EXPIRED', 'OPENED', 'CLOSED',
    'REJECT OVER LIMIT', 'REJECT TAMPER', 'OPERATIONS ADMIT', 'OPENED',
    'CLOSED', 'CLEAR ALARM', 'LOCAL RESET', 'ARM DUAL AUTHORIZATION',
    'INPUT POINT TRUE', 'INPUT POINT FALSE', 'OUTPUT POINT TRUE',
    'OUTPUT POINT FALSE', 'ALARM INPUT TRUE', 'ALARM INPUT FALSE',
    'ALARM INPOUT CHANGE', 'ALARM OUTPUT TRUE', 'ALARM OUTPUT FALSE',
    'ALARM OUTPUT CHANGE', 'DISABLE INPUT POINT', 'ENABLE INPUT POINT',
    'DISABLE OUPUT POINT', 'ENABLE OUTPUT POINT'}


class Isonasacs(object):
    """ISONAS ACS interface class

    An instance of this class represents a TCP/IP connection to a ISONAS Access
    Control System.
    """

    def __init__(self, host, port=7101, _Telnet=Telnet):
        """Constructor

        The instance is directly connected.
        """
        self._telnet = _Telnet(host, port)
        response = self.read_response()
        assert get_type(response) == 'LOGON'

    def _read_responses(self):
        while True:
            message = self._telnet.read_until('|')
            if not message:
                continue
            yield message

    def read_response(self):
        """Read one response

        Raise IsonasacsError is the response is an error.
        """
        for message in self._read_responses():
            if not message:
                continue
            if not is_notification(message):
                if get_type(message) == 'ERROR':
                    raise IsonasacsError(message)
                return get_datetime(message)[1]
            else:
                pass  # TODO store notification

    def write_message(self, *args):
        """Write the message from the list of argument

        Each argument is surrounded by "< >".
        The message is ended by "|".
        """
        message = ''.join('<%s>' % s for s in args)
        self._telnet.write(message + '|')

    def logon(self, clientid, password):
        """Logon the system

        Using the clientid and password.
        """
        self.write_message('LOGON', clientid, password)
        response = self.read_response()
        assert get_type(response) == 'LOGON ACCEPTED'
        self._telnet.read_until('|')  # Sent twice |

    def _command(self, command, *args):
        self.write_message(command, *args)
        response = self.read_response()
        assert get_type(response) == 'ACK'

    def add(self, table, *data):
        "Add data to the table"
        self._command('ADD', table, *data)

    def delete(self, table, *data):
        "Delete data from the table"
        self._command('DELETE', table, *data)

    def update(self, table, *data):
        "Update data from the table"
        self._command('UPDATE', table, *data)

    def _read_list(self, tag, end):
        while True:
            response = self.read_response()
            if not response:
                continue
            if get_type(response) == end:
                break
            else:
                assert response.startswith('<%s>' % tag)
                yield split_values(response[len('<%s>' % tag):-1])

    def query_all(self, table):
        "Query all records of table"
        self.write_message('QUERY', 'ALL %s' % table)
        return list(self._read_list('ALL %s' % table, 'END %s' % table))

    def query(self, table, *args):
        "Query one record of table"
        self.write_message('QUERY', table, *args)
        if table in ['GROUP', 'BADGES']:
            return list(self._read_list(table, 'END %s' % table))
        else:
            response = self.read_response()
            assert response.startswith('<%s>' % table)
            return split_values(response[len('<%s>' % table):-1])


class IsonasacsError(Exception):
    pass


def get_datetime(message):
    match = _DATETIME_RE.match(message)
    if not match:
        return None, message
    values = {k: int(v) for k, v in match.groupdict().items()
        if k != 'message'}
    datetime_ = datetime.datetime(**values)
    return datetime_, match.group('message')


def get_type(message):
    # Strip all datetime as ERROR message has many
    _, message = get_datetime(message)
    while True:
        _, new_message = get_datetime(message)
        if new_message == message:
            break
        else:
            message = new_message
    return _TYPE_RE.match(message).group('type')


def is_notification(message):
    return get_type(message) in NOTIFICATIONS


def split_values(message):
    return _VALUES_RE.findall(message)
