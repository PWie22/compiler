
from sly import Parser
from myLexer import MyLexer
from compilerFunctions import *
from mathFunctions import *
from conditions import *
from values import *
from commands import *
from ioOperations import *

class MyParser(Parser):

    tokens = MyLexer.tokens

    ### MAIN PART OF THE PARSER ###

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )
        
    def p_program(p):
        'program : procedures main'
        # czy nie powinno być jeszcze samego maina, bo co, jeżeli nie ma żadnych procedur?
        # co tutaj zrobić, czy tego nie usunąć???
        # co się dzieje, jeżeli nie ma żadnych procedur
        procLen = len(p[1].split('\n'))
        p[0] = 'JUMP {}'.format(procLen) + p[1] + p[2] + 'HALT'
    
    def p_main(p):
        '''main : PROGRAM IS declarations IN commands END
                | PROGRAM IS IN commands END'''
        # tutaj trzeba sczytać wszystko z declarations, jeżeli są
        if len(p) == 7:
            # tutaj dodać funkcję dodającą nazwy zadeklarowanych zmiennych do tablicy
            p[0] = p[5]
        else:
            p[0] = p[4]
            # co tutaj zrobić
    
    ### DECLARATIONS OF VARIABLES USED IN A FUNCTION ###
    
    def p_array_use(self, p):
        '''declarations : declarations COMMA VARID SQLPAREN NUMBER SQRPAREN
                        | VARID SQLPAREN NUMBER SQRPAREN'''
        line = p.lineno # numer linii, w której jest dopasowany tekst
        if len(p) == 7:
            self.addSymbolToArray(p[3], True, int(p[5]), line)
        else:
            self.addSymbolToArray(p[1], True, int(p[3]), line)
    
    def p_var_use(self, p):
        '''declarations : declarations COMMA VARID
                        | VARID'''
        line = p.lineno
        #if p[1] != None:
        if len(p) == 4:
            self.addSymbolToArray(p[3], False, 0, line)
        else:
            self.addSymbolToArray(p[1], False, 0, line)
        
    ### SYNTAX ERRORS ###

    def p_error(self, p):
        raise SyntaxError("Error: Syntax error in line {}.".format(p.parser.lineno))