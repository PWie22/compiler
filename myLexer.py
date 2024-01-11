
from sly import Lexer

class MyLexer(Lexer):

    tokens = {'VARID', 'NUMBER',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
              'ASSIGN', 'NEG', 'SQRPAREN', 'SQLPAREN', 'RPAREN', 'LPAREN',
              'EQUAL', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ',
              'IF', 'THEN', 'ELSE', 'ENDIF',
              'REPEAT', 'UNTIL',
              'WHILE', 'DO', 'ENDWHILE',
              'READ', 'WRITE',
              'PROGRAM', 'PROCEDURE',
              'IS', 'IN', 'END', 'SEMICOLON', 'COMMA', 'ARRAYSIGN'}

    ignore = ' \t'
    ignore_comment = r'^\#(.|\\)*\n'

    # identyfikator/nazwa deklarowanej zmiennej
    VARID = r'[a-z_]+'

    def t_NUMBER(t):
        r'\d+'
        t.value = int(t.value)
        return t

    PLUS = r'\+'
    MINUS = r'\-'
    TIMES = r'\*'
    DIVIDE = r'\/'
    MOD = r'\%'
    ASSIGN = r':='
    NEG = r'!='
    SQRPAREN = r'\]'
    SQLPAREN = r'\['
    RPAREN = r'\)'
    LPAREN = r'\('
    EQUAL = r'='
    LESS = r'<'
    LESSEQ = r'<='
    GREATER = r'>'
    GREATEREQ = r'>='

    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    ENDIF = r'ENDIF'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    WHILE = r'WHILE'
    DO = r'DO'
    ENDWHILE = r'ENDWHILE'
    READ = r'READ'
    WRITE = r'WRITE'
    PROGRAM = r'PROGRAM'
    PROCEDURE = r'PROCEDURE'
    IS = r'IS'
    IN = r'IN'
    END = r'END'
    SEMICOLON = r'\;'
    COMMA = r'\,'
    ARRAYSIGN = r'T'

lexer = MyLexer()
'''for token in lexer.tokenize'''