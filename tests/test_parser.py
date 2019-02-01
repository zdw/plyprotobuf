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

import plyxproto.parser as plyxparser
import plyxproto.model as plyxmodel
import plyxproto.helpers as plyxhelpers

# Example of creating unittests on PLY code:
#  https://github.com/dabeaz/ply/tree/master/test
#  http://www.dalkescientific.com/writings/NBN/parsing_with_ply.html


def get_name(element):
    '''returns name of element'''
    return element.name.value.pval


def get_field_type(ft):
    ''' returns field type'''

    # FIXME: these are confusing
    if isinstance(ft, plyxmodel.FieldType):
        return ft.name.pval

    elif isinstance(ft, plyxmodel.DotName):
        return ft.value

    else:
        print("unknown field type: %s" % ft)
        raise BaseException


def get_field_directives(field):
    ''' navigate the morass that is fieldDirective '''

    fds = {}

    for fieldd in field.fieldDirective:

        fd_key = ""
        fd_val = ""

        # FIXME: Do these differences in heirarchy have value? They seem
        # arbitrary and maybe the parser should handle it instead?

        if hasattr(fieldd, 'name'):
            fd_key = fieldd.name.value
        elif hasattr(fieldd.pval.name, 'pval'):
            fd_key = fieldd.pval.name.pval
        elif hasattr(fieldd.pval.name.value, 'pval'):
            fd_key = fieldd.pval.name.value.pval
        else:
            print("problem with key in fieldDirective: ", fieldd)
            raise BaseException

        if type(fieldd) is list:
            fd_val = [item.pval for item in fieldd.value]
        elif hasattr(fieldd, 'value'):
            if type(fieldd.value) is list:
                fd_val = [item.pval for item in fieldd.value]
            elif hasattr(fieldd.value, 'pval'):
                fd_val = fieldd.value.pval
            elif hasattr(fieldd.value, 'value'):
                if hasattr(fieldd.value.value, 'pval'):
                    fd_val = fieldd.value.value.pval
                else:
                    fd_val = fieldd.value.value
            else:
                print("problem with value.value in fieldDirective: %s" % fieldd)
                raise BaseException
        elif hasattr(fieldd.pval.value, 'pval'):
            fd_val = fieldd.pval.value.pval
        elif hasattr(fieldd.pval.value.value, 'pval'):
            fd_val = fieldd.pval.value.value.pval
        else:
            print("problem with value in fieldDirective: ", fieldd)
            raise BaseException

        fds[fd_key] = fd_val

    return fds


def msg_dict(msgdef):
    '''
    Given a MessageDefinition object, returns a dict describing it
    Should probably really be a recursive __dict__ method on that object
    '''

    fd = {}  # FieldDefinition
    md = {}  # sub-ModelDefinition
    en = {}  # EnumDefinitons
    ed = {}  # ExtensionsDirective
    os = {}  # OptionStatement

    assert isinstance(msgdef, plyxmodel.MessageDefinition)

    for field in msgdef.body:

        if isinstance(field, plyxmodel.FieldDefinition):

            fd[field.name.value.pval] = {
                'id': int(field.fieldId.pval),
                'modifier': field.field_modifier.pval,
                'type': get_field_type(field.ftype),
                'policy': field.policy,
                'directives': get_field_directives(field),
            }

        elif isinstance(field, plyxmodel.LinkSpec):

            fd[field.field_def.name.value.pval] = {
                'id': int(field.field_def.fieldId.pval),
                'modifier': field.field_def.field_modifier.pval,
                'type': field.field_def.ftype.value,  # Why different (not in a LU as in FieldDefinition)?
                'link_type': field.link_def.link_type.pval,
                'link_name': field.link_def.name[0].pval,  # Why in a list?
                'link_src_port': field.link_def.src_port.value.pval,  # confusingly named - why include "port" ?
                'link_dst_port': field.link_def.dst_port.value.pval,
                'directives': get_field_directives(field.field_def),
            }

        elif isinstance(field, plyxmodel.MessageDefinition):

            md[field.name.value.pval] = msg_dict(field)

        elif isinstance(field, plyxmodel.EnumDefinition):

            enumopts = {}

            for enumdef in field.body:
                enumopts[int(enumdef.fieldId.pval)] = get_name(enumdef)

            en[field.name.value.pval] = enumopts

        elif isinstance(field, plyxmodel.ExtensionsDirective):

            # FIXME: models.ExtensionsMax() isn't well defined, so
            # omit to/from when non-LU is found

            if type(field.fromVal) is plyxhelpers.LU:
                ed['from'] = field.fromVal.pval

            if type(field.toVal) is plyxhelpers.LU:
                ed['to'] = field.toVal.pval

        elif isinstance(field, plyxmodel.OptionStatement):

            os[field.name.value.pval] = field.value.value.pval

        else:
            print("Unknown message type: %s" % type(field))
            raise BaseException

    return fd, md, en, ed, os


def options_dict(protofile):
    '''returns a dictionary of name:value options from a ProtoFile'''

    options = {}

    for item in protofile.body:
        if isinstance(item, plyxmodel.OptionStatement):
            options[item.name.value.pval] = item.value.value.pval

    return options


class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.parser = plyxparser.ProtobufAnalyzer()

    def test_invalid_input(self):
        '''invalid input'''

        t_in = """this is invalid"""

        with self.assertRaises(plyxparser.ParsingError):
            self.parser.parse_string(t_in)

    def test_package(self):
        '''creating a package'''

        t_in = """package tutorial;"""
        p_out = self.parser.parse_string(t_in)

        self.assertIsInstance(p_out, plyxmodel.ProtoFile)
        self.assertIsInstance(p_out.body[0], plyxmodel.PackageStatement)
        self.assertEqual(p_out.body[0].name.value[0].pval, "tutorial")

    def test_def_policy(self):
        '''defining a policy'''

        t_in = """policy foo <exists foo: foo.x=foo.y>"""
        p_out = self.parser.parse_string(t_in)

        self.assertIsInstance(p_out, plyxmodel.ProtoFile)
        self.assertIsInstance(p_out.body[0], plyxmodel.PolicyDefinition)
        self.assertEqual(get_name(p_out.body[0]), "foo")
        self.assertDictEqual(p_out.body[0].body, {'exists': ['foo', {'=': ('foo.x', 'foo.y')}]})

    def test_def_message(self):
        '''defining a message'''

        t_in = """package tutorial;

message Person {
  required string name = 1;
  required int32 id = 2;
  optional string email = 3;
}
"""
        p_out = self.parser.parse_string(t_in)

        self.assertIsInstance(p_out, plyxmodel.ProtoFile)
        # see test_package for testing `package ...` statement
        self.assertIsInstance(p_out.body[1], plyxmodel.MessageDefinition)
        self.assertEqual(get_name(p_out.body[1]), 'Person')

        fd, md, en, ed, os = msg_dict(p_out.body[1])

        self.assertDictEqual(fd['name'],
                             {'id': 1, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {}})
        self.assertDictEqual(fd['id'],
                             {'id': 2, 'modifier': 'required', 'type': 'int32', 'policy': None, 'directives': {}})
        self.assertDictEqual(fd['email'],
                             {'id': 3, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {}})

    def test_options(self):
        '''setting options'''

        t_in = """package tutorial;
option java_outer_classname = "PushNotifications";
option optimize_for = SPEED;
"""
        p_out = self.parser.parse_string(t_in)
        od = options_dict(p_out)

        self.assertDictEqual(od, {'java_outer_classname': '"PushNotifications"', 'optimize_for': 'SPEED'})

    def test_def_relation(self):
        '''test defining related messages'''

        t_in = """package tutorial;

message Person(core.Actor) {
  required string name = 1;
  required int32 id = 2;
  optional string email = 3;

  required manytoone work_location->Location/types.Company:employees = 4;

  enum PhoneType {
    MOBILE = 0;
    HOME = 1;
    WORK = 2;
  }

  message PhoneNumber {
    required string number = 1;
    optional PhoneType type = 2 [default = HOME];
  }

  repeated PhoneNumber phone = 4;
  extensions 500 to 990;
}

message AddressBook {
  repeated Person person = 1;

  // Possible extension numbers.
  extensions 500 to max;
}
"""
        p_out = self.parser.parse_string(t_in)

        fd, md, en, ed, os = msg_dict(p_out.body[1])

        self.assertDictEqual(fd, {'name': {'id': 1, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {}}, 'id': {'id': 2, 'modifier': 'required', 'type': 'int32', 'policy': None, 'directives': {}}, 'email': {'id': 3, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {}}, 'work_location': {'id': 4, 'modifier': 'required', 'type': 'int32', 'link_type': 'manytoone', 'link_name': 'Location', 'link_src_port': 'work_location', 'link_dst_port': 'employees', 'directives': {'type': 'link', 'model': ['Location'], 'port': 'employees'}}, 'phone': {'id': 4, 'modifier': 'repeated', 'type': 'PhoneNumber', 'policy': None, 'directives': {}}})

        self.assertDictEqual(md, {'PhoneNumber': ({'number': {'id': 1, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {}}, 'type': {'id': 2, 'modifier': 'optional', 'type': 'PhoneType', 'policy': None, 'directives': {'default': 'HOME'}}}, {}, {}, {}, {})})
        self.assertDictEqual(en, {'PhoneType': {0: 'MOBILE', 1: 'HOME', 2: 'WORK'}})
        self.assertDictEqual(ed, {'from': '500', 'to': '990'})
        self.assertDictEqual(os, {})

        fd, md, en, ed, os = msg_dict(p_out.body[2])

        self.assertDictEqual(fd, {'person': {'id': 1, 'modifier': 'repeated', 'type': 'Person', 'policy': None, 'directives': {}}})
        self.assertDictEqual(md, {})
        self.assertDictEqual(en, {})
        self.assertDictEqual(ed, {'from': '500'})
        self.assertDictEqual(os, {})

    def test_xos_core(self):
        '''test chunk of xos core xproto'''

        t_in = """
option app_label = "core";
option legacy="True";

// use thi policy to allow access to admins only
policy admin_policy < ctx.user.is_admin >

message XOSBase {
     option skip_init = True;
     option custom_header = "xosbase_header";
     option abstract = True;

     // field 1 is reserved for "id"
     required string created = 2 [content_type = "date", auto_now_add = True, help_text = "Time this model was created"];
     required string updated = 3 [default = "now()", content_type = "date", help_text = "Time this model was changed by a non-synchronizer"];
     optional string enacted = 4 [null = True, content_type = "date", blank = True, default = None, help_text = "When synced, set to the timestamp of the data that was synced"];
     optional string policed = 5 [null = True, content_type = "date", blank = True, default = None, help_text = "When policed, set to the timestamp of the data that was policed"];
     optional string backend_register = 6 [default = "{}", max_length = 1024, feedback_state = True];
     required bool backend_need_delete = 7 [default = False, blank = True];
     required bool backend_need_reap = 8 [default = False, blank = True];
     required string backend_status = 9 [default = "Provisioning in progress", max_length = 1024, null = True, feedback_state = True];
     required int32 backend_code = 10 [default = 0, feedback_state = True];
     required bool deleted = 11 [default = False, blank = True];
     required bool write_protect = 12 [default = False, blank = True];
     required bool lazy_blocked = 13 [default = False, blank = True];
     required bool no_sync = 14 [default = False, blank = True];
     required bool no_policy = 15 [default = False, blank = True];
     optional string policy_status = 16 [default = "Policy in process", max_length = 1024, feedback_state = True];
     optional int32 policy_code = 17 [default = 0, feedback_state = True];
     required string leaf_model_name = 18 [null = False, max_length = 1024, help_text = "The most specialized model in this chain of inheritance, often defined by a service developer"];
     required bool backend_need_delete_policy = 19 [default = False, help_text = "True if delete model_policy must be run before object can be reaped", blank = True];
     required bool xos_managed = 20 [default = True, help_text = "True if xos is responsible for creating/deleting this object", blank = True, gui_hidden = True];
     optional string backend_handle = 21 [max_length = 1024, feedback_state = True, blank=True, null=True, help_text = "Handle used by the backend to track this object", gui_hidden = True];
     optional string changed_by_step = 22 [null = True, content_type = "date", blank = True, default = None, gui_hidden = True, help_text = "Time this model was changed by a sync step"];
     optional string changed_by_policy = 23 [null = True, content_type = "date", blank = True, default = None, gui_hidden = True, help_text = "Time this model was changed by a model policy"];
}

// A user may give a permission that he has to another user
policy grant_policy < ctx.user.is_admin
                      | exists Privilege:Privilege.object_type = obj.object_type
                        & Privilege.object_id = obj.object_id
                        & Privilege.accessor_type = "User"
                        & Privilege.accessor_id = ctx.user.id
                        & Privilege.permission = "role:admin" >

message Privilege::grant_policy (XOSBase) {
     required int32 accessor_id = 1 [null = False, blank=False];
     required string accessor_type = 2 [null = False, max_length=1024, blank = False];
     optional int32 controller_id = 3 [null = True, blank = True];
     required int32 object_id = 4 [null = False, blank=False];
     required string object_type = 5 [null = False, max_length=1024, blank = False];
     required string permission = 6 [null = False, default = "all", max_length=1024, tosca_key=True];
     required string granted = 7 [content_type = "date", auto_now_add = True, max_length=1024];
     required string expires = 8 [content_type = "date", null = True, max_length=1024];
}
"""

        p_out = self.parser.parse_string(t_in)

        # check options
        od = options_dict(p_out)
        self.assertDictEqual(od, {'app_label': '"core"', 'legacy': '"True"'})

        self.assertIsInstance(p_out.body[2], plyxmodel.PolicyDefinition)
        self.assertEqual(get_name(p_out.body[2]), "admin_policy")
        self.assertEqual(p_out.body[2].body, 'ctx.user.is_admin')

        fd, md, en, ed, os = msg_dict(p_out.body[3])

        self.assertDictEqual(fd, {'created': {'id': 2, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'content_type': '"date"', 'auto_now_add': 'True', 'help_text': '"Time this model was created"'}}, 'updated': {'id': 3, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'default': '"now()"', 'content_type': '"date"', 'help_text': '"Time this model was changed by a non-synchronizer"'}}, 'enacted': {'id': 4, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'null': 'True', 'content_type': '"date"', 'blank': 'True', 'default': 'None', 'help_text': '"When synced, set to the timestamp of the data that was synced"'}}, 'policed': {'id': 5, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'null': 'True', 'content_type': '"date"', 'blank': 'True', 'default': 'None', 'help_text': '"When policed, set to the timestamp of the data that was policed"'}}, 'backend_register': {'id': 6, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'default': '"{}"', 'max_length': '1024', 'feedback_state': 'True'}}, 'backend_need_delete': {'id': 7, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'backend_need_reap': {'id': 8, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'backend_status': {'id': 9, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'default': '"Provisioning in progress"', 'max_length': '1024', 'null': 'True', 'feedback_state': 'True'}}, 'backend_code': {'id': 10, 'modifier': 'required', 'type': 'int32', 'policy': None, 'directives': {'default': '0', 'feedback_state': 'True'}}, 'deleted': {'id': 11, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'write_protect': {'id': 12, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'lazy_blocked': {'id': 13, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'no_sync': {'id': 14, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'no_policy': {'id': 15, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'blank': 'True'}}, 'policy_status': {'id': 16, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'default': '"Policy in process"', 'max_length': '1024', 'feedback_state': 'True'}}, 'policy_code': {'id': 17, 'modifier': 'optional', 'type': 'int32', 'policy': None, 'directives': {'default': '0', 'feedback_state': 'True'}}, 'leaf_model_name': {'id': 18, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'null': 'False', 'max_length': '1024', 'help_text': '"The most specialized model in this chain of inheritance, often defined by a service developer"'}}, 'backend_need_delete_policy': {'id': 19, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'False', 'help_text': '"True if delete model_policy must be run before object can be reaped"', 'blank': 'True'}}, 'xos_managed': {'id': 20, 'modifier': 'required', 'type': 'bool', 'policy': None, 'directives': {'default': 'True', 'help_text': '"True if xos is responsible for creating/deleting this object"', 'blank': 'True', 'gui_hidden': 'True'}}, 'backend_handle': {'id': 21, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'max_length': '1024', 'feedback_state': 'True', 'blank': 'True', 'null': 'True', 'help_text': '"Handle used by the backend to track this object"', 'gui_hidden': 'True'}}, 'changed_by_step': {'id': 22, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'null': 'True', 'content_type': '"date"', 'blank': 'True', 'default': 'None', 'gui_hidden': 'True', 'help_text': '"Time this model was changed by a sync step"'}}, 'changed_by_policy': {'id': 23, 'modifier': 'optional', 'type': 'string', 'policy': None, 'directives': {'null': 'True', 'content_type': '"date"', 'blank': 'True', 'default': 'None', 'gui_hidden': 'True', 'help_text': '"Time this model was changed by a model policy"'}}})

        self.assertDictEqual(md, {})
        self.assertDictEqual(en, {})
        self.assertDictEqual(ed, {})
        self.assertDictEqual(os, {'skip_init': 'True', 'custom_header': '"xosbase_header"', 'abstract': 'True'})

        self.assertIsInstance(p_out.body[4], plyxmodel.PolicyDefinition)

        self.assertEqual(get_name(p_out.body[4]), "grant_policy")
        self.assertDictEqual(p_out.body[4].body, {'|':
            ['ctx.user.is_admin', {'&':
                [{'&': [{'&': [{'&': [{'exists': ['Privilege', {'=': ('Privilege.object_type', 'obj.object_type')}]},
                               {'=': ('Privilege.object_id', 'obj.object_id')}]},
                               {'=': ('Privilege.accessor_type', '"User"')}]},
                               {'=': ('Privilege.accessor_id', 'ctx.user.id')}]},
                               {'=': ('Privilege.permission', '"role:admin"')}]}]}
                )
        fd, md, en, ed, os = msg_dict(p_out.body[5])

        self.assertDictEqual(fd, {'accessor_id': {'id': 1, 'modifier': 'required', 'type': 'int32', 'policy': None, 'directives': {'null': 'False', 'blank': 'False'}}, 'accessor_type': {'id': 2, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'null': 'False', 'max_length': '1024', 'blank': 'False'}}, 'controller_id': {'id': 3, 'modifier': 'optional', 'type': 'int32', 'policy': None, 'directives': {'null': 'True', 'blank': 'True'}}, 'object_id': {'id': 4, 'modifier': 'required', 'type': 'int32', 'policy': None, 'directives': {'null': 'False', 'blank': 'False'}}, 'object_type': {'id': 5, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'null': 'False', 'max_length': '1024', 'blank': 'False'}}, 'permission': {'id': 6, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'null': 'False', 'default': '"all"', 'max_length': '1024', 'tosca_key': 'True'}}, 'granted': {'id': 7, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'content_type': '"date"', 'auto_now_add': 'True', 'max_length': '1024'}}, 'expires': {'id': 8, 'modifier': 'required', 'type': 'string', 'policy': None, 'directives': {'content_type': '"date"', 'null': 'True', 'max_length': '1024'}}})

        self.assertDictEqual(md, {})
        self.assertDictEqual(en, {})
        self.assertDictEqual(ed, {})
        self.assertDictEqual(os, {})

# FIXME: these sorts of simple validations should fail but currently don't
#
#       def test_invalid_message(self):
#           '''an invalid message'''
#
#           t_in = """message BadMessage {
#     required string name = 0;
#     required int32 id = -2;
#   }"""
#           p_out = self.parser.parse_string(t_in)
#           print(p_out)
#
#
#       def test_duplicate_id(self):
#           '''duplicate id's in a message'''
#
#           t_in = """message BadMessage2 {
#     required string name = 1;
#     required int32 id = 1;
#   }"""
#           p_out = self.parser.parse_string(t_in)
#           print(p_out)
