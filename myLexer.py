
import ply.lex as lex
import sys

#class MyLexer(Lexer):

tokens = ('NEWLINE', 'VARID', 'NUMBER',
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
            'ASSIGN', 'NEG', 'SQRPAREN', 'SQLPAREN', 'RPAREN', 'LPAREN',
            'EQUAL', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ',
            'IF', 'THEN', 'ELSE', 'ENDIF',
            'REPEAT', 'UNTIL',
            'WHILE', 'DO', 'ENDWHILE',
            'READ', 'WRITE',
            'PROGRAM', 'PROCEDURE',
            'IS', 'IN', 'END', 'SEMICOLON', 'COMMA', 'ARRAYSIGN')

t_ignore = ' \t'
t_ignore_comment = r'\#(.|\\)*\n'
#t_NEWLINE = r'\n+'

# identyfikator/nazwa deklarowanej zmiennej
t_VARID = r'[a-z_]+'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_NEWLINE(t):
    r'\n+'
    pass

#NUMBER = r'\d+'

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
t_ELSE = r'ELSE'
t_ENDIF = r'ENDIF'
t_REPEAT = r'REPEAT'
t_UNTIL = r'UNTIL'
t_WHILE = r'WHILE'
t_DO = r'DO'
t_ENDWHILE = r'ENDWHILE'
t_READ = r'READ'
t_WRITE = r'WRITE'
t_PROGRAM = r'PROGRAM'
t_PROCEDURE = r'PROCEDURE'
t_IS = r'IS'
t_IN = r'IN'
t_END = r'END'
t_SEMICOLON = r'\;'
t_COMMA = r'\,'
t_ARRAYSIGN = r'T'

def build_lexer():
    return lex.lex()

def t_error(t):
    print("Illegal sign in line .")
    t.lexer.skip(1)

programme = ''
with open(sys.argv[1], "r") as file:
    programme = file.read()

lexer = build_lexer()
lexer.input(programme)
while True:
    t = lexer.token()
    if not t:
        break
    print(t)
