
from compilerFunctions import *

### EXPRESSIONS ###

def p_expression_value(p):
    'expression : value'
    p[0] = p[1]
    
def p_add_sub(p):
    '''expression : value PLUS value
                    | value MINUS value'''
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    if p[2] == '+':
        # chyba zamiast PUT f powinno być zapisywanie do pamięci, czy może jednak trzymanie w rejestrach???
        code += 'GET b\nADD d\nPUT f\n'
    else:
        code += 'GET b\nSUB d\nPUT f\n'

def p_multiply(p):
    'expression : value TIMES value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    code += 'RST c\nGET b\nSUB d\nJPOS  \nGET b\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n \nGET d\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n'
    p[0] = code

def p_divide(p):
    'expression : value DIVIDE value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    # trzeba poprawić i jeszcze dopisać adresy skoków
    # wynik jest w rejestrze f
    code += 'RST c\nRST f\nGET d\nPUT e\nSHL e\nGET b\nJZERO  \nSUB e\nJZERO  \nINC c\nJUMP  \nGET e\nJZERO  \nSUB b\nJZERO  \nSHL c\nGET c\nADD f\nPUT f\nRST c\
        \nSHR e\nGET b\nSUB e\nSHL a\nPUT e\nJUMP  \n'
    p[0] = code

def p_modulo(p):
    'expression : value MOD value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    code += ''
    p[0] = code