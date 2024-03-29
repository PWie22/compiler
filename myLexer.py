
import ply.lex as lex
import sys

tokens = (  'NEWLINE', 'COMMENT',
            'VARID', 'NUMBER',
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'NEG',
            'ASSIGN', 'SQRPAREN', 'SQLPAREN', 'RPAREN', 'LPAREN',
            'EQUAL', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ',
            'IF', 'THEN', 'ELSE', 'ENDIF',
            'REPEAT', 'UNTIL',
            'WHILE', 'DO', 'ENDWHILE',
            'READ', 'WRITE',
            'PROGRAM', 'PROCEDURE',
            'IS', 'IN', 'END',
            'SEMICOLON', 'COMMA', 'ARRAYSIGN')

t_ignore = ' \t'

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    pass

def t_COMMENT(t):
    r'\#(.|\\)*\n'
    t.lexer.lineno += 1
    pass

t_VARID = r'[a-z_]+'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_DIVIDE = r'\/'
t_MOD = r'\%'
t_ASSIGN = r':='
t_NEG = r'!='
t_SQRPAREN = r'\]'
t_SQLPAREN = r'\['
t_RPAREN = r'\)'
t_LPAREN = r'\('
t_EQUAL = r'='
t_LESS = r'<'
t_LESSEQ = r'<='
t_GREATER = r'>'
t_GREATEREQ = r'>='

t_IF = r'IF'
t_THEN = r'THEN'

def t_ELSE(t):
    r'ELSE'
    t.value = 'ELSE'
    t.lexer.isElse = True
    return t

def t_ENDIF(t):
    r'ENDIF'
    t.value = 'ENDIF'
    t.lexer.isElse = False
    return t

t_REPEAT = r'REPEAT'
t_UNTIL = r'UNTIL'
t_WHILE = r'WHILE'
t_DO = r'DO'
t_ENDWHILE = r'ENDWHILE'
t_READ = r'READ'
t_WRITE = r'WRITE'
t_PROGRAM = r'PROGRAM'

def t_PROCEDURE(t):
	r'PROCEDURE'
	t.value = 'PROCEDURE'
	t.lexer.hasProcedures = True
	return t

t_IS = r'IS'
t_IN = r'IN'
t_END = r'END'
t_SEMICOLON = r'\;'
t_COMMA = r'\,'
t_ARRAYSIGN = r'T'

def t_error(t):
    print("Illegal sign in line ", t.lexer.lineno)
    t.lexer.skip(1)

programme = ''
with open(sys.argv[1], "r") as file:
    programme = file.read()

lexer = lex.lex()

lexer.isElse = False
lexer.hasProcedures = False
lexer.input(programme)
while True:
    t = lexer.token()
    if not t:
        break
lexer.lineno = 1