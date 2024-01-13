
from sly import Parser
from myLexer import MyLexer
from compilerFunctions import *
from mathFunctions import *
from conditions import *
from values import *

class MyParser(Parser):

    ### SECTION FOR GLOBAL VARIABLES OF THE CLASS ###

    tokens = MyLexer.tokens

    ### MAIN PART OF THE PARSER ###

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )
        
    def p_program(p):
        'program : procedures main'
        # co tutaj zrobić, czy tego nie usunąć???
        # co się dzieje, jeżeli nie ma żadnych procedur
        p[0] = p[1] + p[2] + 'HALT'

    def p_procedures(p):
        '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                        | procedures PROCEDURE proc_head IS IN commands END'''
        # tutaj chyba źle
        global procedures_list
        # upewnić się, czy te numery linijek są na pewno dobrze dobrane - czy jest możliwe, żeby przed wstawieniem końca lin
        if (len(p) == 9):
            #p[0] = p[1] + p[7] + 'HALT'
            procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[8]].lineno
            # chyba jeszcze gdzieś na początku musi być jakiś jump do linijki, w której zaczyna się program
            p[0] = p[7]
        else:
            #p[0] = p[1] + p[6] + 'HALT'
            procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[7]].lineno
            p[0] = p[6]
    
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

    def p_proc_head(p):
        'proc_head : VARID LPAREN args_decl RPAREN'
        global procedures_list
        j = None
        for i in range(len(procedures_list)):
            if procedures_list[i][0] == p[1]:
                j = i
        if j != None:
            raise Exception("Error: Redaclaration of procedure {} in line .".format(p[1]))
        else:
            procedures_list.append([p[1], p.lineno, 0])
    
    def p_proc_call(p):
        'proc_call : VARID LPAREN args RPAREN'
        global procedures_list
        j = -1
        for i in range(len(procedures_list)):
            if procedures_list[i][0] == p[1]:
                j = i
        if j == -1:
            raise Exception("Error: Calling unexisting procedure {} in line .".format(p[1]))
        else:
            line_of_call = p.lineno
            if line_of_call < procedures_list[j][1]:
                raise Exception("Error: Calling procedure {} in line  before it is declared.".format(p[1]))
            elif line_of_call > procedures_list[j][1] and line_of_call < procedures_list[j][2]:
                raise Exception("Error: Recursive call of procedure {} in line .".format(p[1]))
            else:
                print()
                # tutaj trzeba dodać skok do miejsca, w którym zaczyna się procedura - ale p.lineno daje nam linijkę w kodzie,
                # więc trzeba jakoś inaczej znaleźć adres skoku
        # teraz chyba trzeba dodać else, żeby dodać jump???
    
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

    def p_array_proc_decl(p):
        '''args_decl : args_decl COMMA ARRAYSIGN VARID
                        | ARRAYSIGN VARID'''
    
    def p_var_proc_decl(p):
        '''args_decl : args_decl COMMA VARID
                        | VARID'''

    def p_args_proc(p):
        '''args : args COMMA VARID
                | VARID'''
        
    ### SYNTAX ERRORS ###

    def p_error(self, p):
        raise SyntaxError("Error: Syntax error in line {}.".format(p.parser.lineno))