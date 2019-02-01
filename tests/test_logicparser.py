# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import unittest

import ply.lex as lex
import ply.yacc as yacc
from plyxproto.logicparser import FOLLexer, FOLParser


class TestFOL(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.DEBUG = 0
        self.lexer = lex.lex(module=FOLLexer(), debug=self.DEBUG)
        self.parser = yacc.yacc(module=FOLParser(), start='goal', debug=self.DEBUG)

    def test_true(self):
        '''verify basic truth statement'''

        t_in = "<true>"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, "true")

    def test_or(self):
        '''verify or statement'''

        t_in = "<a | b>"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, {'|': ['a', 'b']})

    def test_exists(self):
        '''verify exists statement'''

        t_in = "<exists a: x=y>"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, {'exists': ['a', {'=': ('x', 'y')}]})

    def test_forall(self):
        '''verify forall statement'''

        t_in = "<forall a: exists b: x.b=y.b>"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, {'forall': ['a', {'exists': ['b', {'=': ('x.b', 'y.b')}]}]})

    def test_endswith(self):
        '''verify endswith statement'''

        t_in = "<forall a: {{ a.endswith('good') }}>"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, {'forall': ['a', {'python': "a.endswith('good')"}]})

    def test_function(self):
        '''verify policy function calls'''

        t_in = "< *doit(foo) >"
        p_out = self.parser.parse(t_in, lexer=self.lexer, debug=self.DEBUG)
        self.assertEqual(p_out, {'policy': ['doit', 'foo']})
