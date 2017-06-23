from plyxproto.logicparser import *
import ply.lex as lex
import ply.yacc as yacc

test_1 = "true"
test_2 = "a | b"
test_3 = "exists a: x=y"
test_4 = "forall a: exists b: x.b=y.b"
test_5 = "forall a: {{ a.endswith('good') }} "

DEBUG = 0

lexer = lex.lex(module=FOLLexer(), debug=DEBUG)#, optimize=1)
parser = yacc.yacc(module=FOLParser(), start='goal', debug=DEBUG)

for x,v in globals().items():
    if x.startswith('test_'):
        print parser.parse(v, lexer = lexer, debug=DEBUG)
