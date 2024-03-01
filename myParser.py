
import ply.yacc as yacc
from myLexer import lexer, tokens
import sys

'''
 symbols_list - list of all declared symbols except these in brackets in procedures; every element of the list follows the pattern:
 [0] name of the symbol,
 [1] boolean variable; if True, then this symbol is a name of an array, otherwise it is a variable,
 [2] capacity of an array; if a symbol is not an array, then its capacity is zero,
 [3] memory cells are enumerated from zero and this is a position taken by the symbol in the memory; if this 
     is an array, then it is the first memory cell allocated for this array,
 [4] boolean variable; if a symbol has not been initiated, it is set to False, True otherwise (if this is an array,
                   then this variable is set to True when one of its elements is asigned a value),
 [5] name of procedure which a symbol belongs to
'''
symbols_list = []
'''
 procedures_list - list of all declared symbols except these in brackets in procedures; every element of the list follows the pattern:
 [0] name of the procedure,
 [1] number of line where the procedure begins in generated code,
 [2] list of variables from brackets
 [3] number of memory cell where the return address (line which programme should jump to when the procedure is finished) is stored
'''
procedures_list = []

first_free_mem_index = 0 # number of first free memory cell
curr_line_in_code = 0 # variable used to track line in generated code, mostly to adjust the jumps
currProcedure = None # variable used to track which procedure is currently being analysed during compilation process; if it is
                     # to None, main function is being analysed
# proc_bracket_args, proc_call_args, proc_inside_variables - lists used to temporarily store a list of arguments when
# a procedure is declared or called
proc_bracket_args = []
proc_call_args = []
proc_inside_variables = []
howdeep = 0 # variable which tracks how deep into loops/if-else statements programme went
procedures_code = '' # variable used to store only the code generated from procedures

### NOT PARSER FUNCTIONS ###

def addSymbolToArray(varName, ifArray, capacity, lineNumb, currProc):
    global symbols_list, first_free_mem_index
    j = None
    for i in range(len(symbols_list)):
        if symbols_list[i][0] == varName and symbols_list[i][5] == currProc:
            j = i
    if j != None:
        print("Error: Redeclaration of variable {} in line {}.".format(varName, lineNumb))
    else:
        symbols_list.append([varName, ifArray, capacity, first_free_mem_index, False, currProc])
        if ifArray:
            first_free_mem_index += capacity
        else:
            first_free_mem_index += 1

def loadValueToRegister(regName, value):
    global curr_line_in_code
    code = ''
    while (value > 0):
        if (value % 2 == 0):
            code = 'SHL {}\n'.format(regName) + code
            value /= 2
        else:
            code = 'INC {}\n'.format(regName) + code
            value -= 1
    code = 'RST {}\n'.format(regName) + code
    curr_line_in_code += len(code.split('\n'))-1
    return code

def loadVariableToRegister(varName, regName, lineNumb, onlyAddress):
    global curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_list)):
        if symbols_list[i][0] == varName and symbols_list[i][5] == currProcedure:
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Use of undeclared variable {} in line {}.".format(varName, lineNumb))
        else:
            for i in range(len(procedures_list)):
                if procedures_list[i][0] == currProcedure:
                    j = i
                    break
            k = None
            for i in range(len(procedures_list[j][2])):
                if procedures_list[j][2][i][0] == varName:
                    k = i
                    break
            if k == None:
                raise Exception("Error: Use of undeclared variable {} in procedure {} in line {}.".format(varName, currProcedure, lineNumb))
            elif procedures_list[j][2][k][1]:
                raise Exception("Error: Incorrect use of variable {} in procedure {} in line {}.".format(varName, currProcedure, lineNumb))
            else:
                code += loadValueToRegister('b', procedures_list[j][2][k][2]) + 'LOAD b\nPUT {}\n'.format(regName)
                if not onlyAddress:
                    code += 'LOAD {}\nPUT {}\n'.format(regName, regName)
                    curr_line_in_code += 2
                curr_line_in_code += 2
    elif symbols_list[j][1]:
        raise Exception("Error: Incorrect use of array {} in line {}.".format(varName, lineNumb))
    elif howdeep < 2 and not symbols_list[j][4]:
        raise Exception("Error: Use of uninitialized variable {} in line {}.".format(symbols_list[j][0], lineNumb))
    else:
        if howdeep >= 2 and not symbols_list[j][4]:
            print("Warning: Variable {} has not been initialized yet (line {}).".format(symbols_list[j][0], lineNumb))
        code += loadValueToRegister('b', symbols_list[j][3])
        if not onlyAddress:
            code += 'LOAD b\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
    return code

def loadArrayToRegister(arrName, regName, index, lineNumb, onlyAddress):
    global curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_list)):
        if symbols_list[i][0] == arrName and symbols_list[i][5] == currProcedure: # dodany drugi warunek
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Use of undeclared array {} in line {}.".format(arrName, lineNumb))
        else:
            for i in range(len(procedures_list)):
                if procedures_list[i][0] == currProcedure:
                    j = i
            k = None
            for i in range(len(procedures_list[j][2])):
                if procedures_list[j][2][i][0] == arrName:
                    k = i
            if k == None:
                raise Exception("Error: Use of undeclared array {} in line {}.".format(arrName, lineNumb))
            else:
                if type(index) is int:
                    code += loadValueToRegister('b', procedures_list[j][2][k][2]) + 'LOAD b\n' + loadValueToRegister('b', index) + 'ADD b\nPUT {}\n'.format(regName)
                    curr_line_in_code += 3
                else:
                    code += loadVariableToRegister(index, 'h', lineNumb, False) + loadValueToRegister('b', procedures_list[j][2][k][2]) + 'LOAD b\nADD h\nPUT {}\n'.format(regName)
                    curr_line_in_code += 3
                if not onlyAddress:
                    code += 'LOAD {}\nPUT {}\n'.format(regName, regName)
                    curr_line_in_code += 2
    else:
        if type(index) is int:
            # tablica indeksowana liczbą
            code += loadValueToRegister('b', symbols_list[j][3]+index)
            if not onlyAddress:
                code += 'LOAD b\nPUT {}\n'.format(regName)
                curr_line_in_code += 2
        else:
            # tablica indeksowana zmienną
            code += loadVariableToRegister(index, 'h', lineNumb, False) + loadValueToRegister('a', symbols_list[j][3]) + 'ADD h\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
            if not onlyAddress:
                code += 'LOAD {}\nPUT {}\n'.format(regName, regName)
                curr_line_in_code += 2
    return code

def loadValuesToRegs(values, regs, lineNumb, onlyAddress):
    code = ''
    for i in range(len(values)):
        if type(values[i]) is int: # będzie tak tylko w przypadku procedury
            code += loadValueToRegister(regs[i], values[i])
        else:
            if len(values[i]) > 1:
                if values[i][1]:
                    # to jest element tablicy
                    code += loadArrayToRegister(values[i][0], regs[i], values[i][2], lineNumb, onlyAddress)
                else:
                    # to jest zwykła zmienna
                    code += loadVariableToRegister(values[i][0], regs[i], lineNumb, onlyAddress)
            else:
                # to jest zwykła liczba
                code += loadValueToRegister(regs[i], values[i][0])
    return code

### PARSER FUNCTIONS ###

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
        
def p_program(p):
    '''program : procedures main'''
    global procedures_code
    if not p[1]:
        p[0] = p[2] + 'HALT'
    else:
        p[0] = 'JUMP {}\n'.format(len(procedures_code.split('\n'))) + procedures_code + p[2] + 'HALT'
    
def p_main(p):
    '''main : PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END'''
    if len(p) == 7:
        p[0] = p[5]
    else:
        p[0] = p[4]
    
### PROCEDURES ###

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END
                    |'''
    global currProcedure, proc_bracket_args, proc_inside_variables, curr_line_in_code, procedures_code
    code = ''
    if (len(p) == 1):
        currProcedure = None
        if p.lexer.hasProcedures:
            curr_line_in_code += 1 # if there are any procedures, jump instruction is added at the begining
    elif (len(p) == 9):
            proc_bracket_args = []
            proc_inside_variables = []
            code += loadValueToRegister('b', procedures_list[-1][3]) + 'LOAD b\nJUMPR a\n'
            curr_line_in_code += 2
            currProcedure = None
            p[0] = p[7] + code
            procedures_code += p[7] + code
    else:
        proc_bracket_args = []
        code += loadValueToRegister('b', procedures_list[-1][3]) + 'LOAD b\nJUMPR a\n'
        curr_line_in_code += 2
        currProcedure = None
        p[0] = p[6] + code
        procedures_code += p[6] + code

def p_proc_head(p):
    'proc_head : VARID LPAREN args_decl RPAREN'
    global procedures_list, currProcedure, first_free_mem_index
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if not j == None:
        raise Exception("Error: Redaclaration of procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
        procedures_list.append([p[1], curr_line_in_code, proc_bracket_args, first_free_mem_index])
        first_free_mem_index += 1
        currProcedure = p[1]

def p_command_proc_call(p):
    'command : proc_call SEMICOLON'
    p[0] = p[1]

def p_proc_call(p):
    'proc_call : VARID LPAREN args RPAREN'
    global curr_line_in_code, proc_call_args
    code = ''
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if j == None:
        raise Exception("Error: Calling unexisting (or not yet declared) procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    elif currProcedure == procedures_list[j][0]:
        raise Exception("Error: Recursive call in procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
            if not len(proc_call_args) == len(procedures_list[j][2]):
                raise Exception("Error: Too few arguments in call of procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
            m = None
            for i in range(len(proc_call_args)):
                for k in range(len(symbols_list)):
                    if proc_call_args[i] == symbols_list[k][0] and symbols_list[k][5] == currProcedure:
                        m = k
                        break
                if m == None:
                    for n in range(len(proc_bracket_args)):
                        if proc_call_args[i] == proc_bracket_args[n][0]:
                            m = n
                            break
                    if m == None:
                        raise Exception("Error: Use of undeclared variable {} in procedure {} in line {}.".format(proc_call_args[i], currProcedure, p.lexer.lineno-1))
                    else:
                        procNumb = None
                        for n in range(len(procedures_list)):
                            if procedures_list[n][0] == currProcedure:
                                procNumb = n
                                break
                        for n in range(len(procedures_list[procNumb][2])):
                            if procedures_list[procNumb][2][n][0] == proc_call_args[i]:
                                break
                        code += loadValueToRegister('b', procedures_list[procNumb][2][n][2]) + 'LOAD b\n' + loadValueToRegister('b', procedures_list[j][2][i][2]) + 'STORE b\n'
                        curr_line_in_code += 2
                        m = None
                else:
                    if symbols_list[m][1] == procedures_list[j][2][i][1]:
                        symbols_list[m][4] = True
                        code += loadValueToRegister('b', procedures_list[j][2][i][2]) + loadValueToRegister('a',symbols_list[m][3]) + 'STORE b\n'
                        curr_line_in_code += 1
                        m = None
                    else:
                        raise Exception("Error: Calling procedure {} with an argument ({}) of wrong type in line {}.".format(p[1], symbols_list[m][0], p.lexer.lineno-1))
            code += loadValueToRegister('b', procedures_list[j][3]) + 'RST a\nINC a\nSHL a\nSHL a\nSTRK c\nADD c\nSTORE b\nJUMP {}\n'.format(procedures_list[j][1])
            curr_line_in_code += 8
            p[0] = code
    proc_call_args = []

def p_array_proc_decl(p):
    '''args_decl : args_decl COMMA ARRAYSIGN VARID
                    | ARRAYSIGN VARID'''
    global proc_bracket_args, first_free_mem_index
    if len(p) == 5:
        proc_bracket_args.append([p[4], True, first_free_mem_index])
    else:
        proc_bracket_args.append([p[2], True, first_free_mem_index])
    first_free_mem_index += 1
    
def p_var_proc_decl(p):
    '''args_decl : args_decl COMMA VARID
                    | VARID'''
    global proc_bracket_args, first_free_mem_index
    if len(p) == 4:
        proc_bracket_args.append([p[3], False, first_free_mem_index])
    else:
        proc_bracket_args.append([p[1], False, first_free_mem_index])
    first_free_mem_index += 1

def p_args_proc(p):
    '''args : args COMMA VARID
            | VARID'''
    global proc_call_args
    if len(p) == 4:
        proc_call_args.append(p[3])
    else:
        proc_call_args.append(p[1])
    
### DECLARATIONS OF VARIABLES USED IN A FUNCTION ###
    
def p_array_use(p):
    '''declarations : declarations COMMA VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN NUMBER SQRPAREN'''
    global proc_inside_variables
    if len(p) == 7:
        addSymbolToArray(p[3], True, p[5], p.lexer.lineno-1, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(proc_bracket_args)):
                if proc_bracket_args[i][0] == p[3]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(proc_bracket_args[j][0], currProcedure, p.lexer.lineno-1))
            else:
                proc_inside_variables.append(p[3])
    else:
        addSymbolToArray(p[1], True, p[3], p.lexer.lineno-1, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(proc_bracket_args)):
                if proc_bracket_args[i][0] == p[1]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(proc_bracket_args[j][0], currProcedure, p.lexer.lineno-1))
            else:
                proc_inside_variables.append(p[1])
    
def p_var_use(p):
    '''declarations : declarations COMMA VARID
                    | VARID'''
    global proc_inside_variables
    if len(p) == 4:
        addSymbolToArray(p[3], False, 0, p.lexer.lineno-1, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(proc_bracket_args)):
                if proc_bracket_args[i][0] == p[3]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(proc_bracket_args[j][0], currProcedure, p.lexer.lineno-1))
            else:
                proc_inside_variables.append(p[3])
    else:
        addSymbolToArray(p[1], False, 0, p.lexer.lineno-1, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(proc_bracket_args)):
                if proc_bracket_args[i][0] == p[1]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(proc_bracket_args[j][0], currProcedure, p.lexer.lineno-1))
            else:
                proc_inside_variables.append(p[1])

### COMMANDS ###

def p_commands(p):
    '''commands : commands command
                | command'''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]
    
def p_assign(p):
    'command : identifier ASSIGN expression SEMICOLON'
    global curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_list)):
        if p[1][0] == symbols_list[i][0] and symbols_list[i][5] == currProcedure:
            j = i
    if not j == None:
        symbols_list[j][4] = True # setting symbol as initiated
    if isinstance(p[3], tuple): # p[3] is an ordinary expression
        code += p[3][1] + loadValuesToRegs([p[1]], ['b'], p.lexer.lineno-1, True) + 'GET {}\nSTORE b\n'.format(p[3][0])
    else: # p[3] is a value
        code += loadValuesToRegs([p[3]], ['c'], p.lexer.lineno-1, False) + loadValuesToRegs([p[1]], ['b'], p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
    curr_line_in_code += 2
    p[0] = code

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    global howdeep
    code = ''
    commandLen = len(p[4].split('\n'))
    if isinstance(p[2], tuple): # in a condition there is '>=' or '<=' - this condition requires two jumps instead of one, unlike other conditions
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commandLen + 1) + p[2][0][2] + '{}\n'.format(curr_line_in_code)
    else: # other conditions - there is just one jump needed
        code += p[2] + '{}\n'.format(curr_line_in_code)
    howdeep -= 1
    p[0] = code + p[4]

def p_if_else_statement(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    global curr_line_in_code, howdeep
    code = ''
    commandLen1 = len(p[4].split('\n'))
    commandLen2 = len(p[6].split('\n'))
    if isinstance(p[2], tuple): # in a condition there is '>=' or '<=' - this condition requires two jumps instead of one, unlike other conditions
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commandLen1 - commandLen2 + 2) + p[2][0][2] \
            + '{}\n'.format(curr_line_in_code-commandLen2 + 2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + 1) + p[6]
    else: # other conditions - there is just one jump needed
        code += p[2] + '{}\n'.format(curr_line_in_code - commandLen2 + 2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + 1) + p[6]
    curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

### LOOPS ###

def p_while_loop(p):
    'command : WHILE condition DO commands ENDWHILE'
    global curr_line_in_code, howdeep
    code = ''
    commandLen = len(p[4].split('\n'))
    if isinstance(p[2], tuple):
        addLen = len(p[2][0][0].split('\n'))
        condLen = 6
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commandLen + 1) + p[2][0][2] + '{}\n'.format(curr_line_in_code + 1) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code - condLen - commandLen - addLen + 2)
    else:
        condLen = len(p[2].split('\n'))
        code += p[2] + '{}\n'.format(curr_line_in_code + 1) + p[4] + 'JUMP {}\n'.format(curr_line_in_code - condLen - commandLen + 1)
    curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

def p_repeat_loop(p):
    'command : REPEAT commands UNTIL condition SEMICOLON'
    global howdeep
    code = ''
    commandLen = len(p[2].split('\n'))
    if isinstance(p[4], tuple):
        condLen= len(p[4][1].split('\n')) + len(p[4][2].split('\n'))
        code += p[2] + p[4][0] + p[4][1] + '{}\n'.format(curr_line_in_code  - 1) + p[4][2] + ' {}\n'.format(curr_line_in_code - condLen - commandLen)
    else:
        condLen = len(p[4].split('\n'))
        code += p[2] + p[4] + '{}\n'.format(curr_line_in_code - condLen - commandLen + 1)
    howdeep -= 1
    p[0] = code

### CONDITIONS ###

def p_equal(p):
    'condition : value EQUAL value'
    global curr_line_in_code, howdeep
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    code += 'GET c\nSUB d\nPUT e\nGET d\nSUB c\nADD e\nJPOS '
    curr_line_in_code += 7
    howdeep += 1
    p[0] = code
    
def p_negation(p):
    'condition : value NEG value'
    global curr_line_in_code, howdeep
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    code += 'GET c\nSUB d\nPUT e\nGET d\nSUB c\nADD e\nJZERO '
    curr_line_in_code += 7
    howdeep += 1
    p[0] = code

def p_greater_less(p):
    '''condition : value GREATER value
                    | value LESS value'''
    global curr_line_in_code, howdeep
    code = ''
    if p[2] == ">":
        code += loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'c'], p.lexer.lineno-1, False)
    code += 'GET c\nSUB d\nJZERO '
    curr_line_in_code += 3
    howdeep += 1
    p[0] = code

def p_greater_less_equal(p):
    '''condition : value GREATEREQ value
                    | value LESSEQ value'''
    global curr_line_in_code, howdeep
    code = ''
    if p[2] == ">=":
        code += loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'c'], p.lexer.lineno-1, False)
    curr_line_in_code += 6
    howdeep += 1
    p[0] = ((code, 'GET c\nSUB d\nJPOS ', 'GET d\nSUB c\nJPOS '),)

### EXPRESSIONS ###

def p_expression_value(p):
    'expression : value'
    p[0] = p[1]
    
def p_add_sub(p):
    '''expression : value PLUS value
                    | value MINUS value'''
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    if p[2] == '+':
        code += 'GET c\nADD d\nPUT e\n'
    else:
        code += 'GET c\nSUB d\nPUT e\n'
    curr_line_in_code += 3
    p[0] = ('e', code)

def p_multiply(p):
    'expression : value TIMES value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    if p.lexer.isElse:
        code += 'RST f\nGET c\nJZERO {}\nGET d\nJZERO {}\nPUT e\nSHR e\nSHL e\nSUB e\nJPOS {}\nSHL c\nSHR d\nJUMP {}\nGET f\nADD c\n\
PUT f\nDEC d\nJUMP {}\n'.format(currLi+19, currLi+19, currLi+14, currLi+4, currLi+4)
    else:
        code += 'RST f\nGET c\nJZERO {}\nGET d\nJZERO {}\nPUT e\nSHR e\nSHL e\nSUB e\nJPOS {}\nSHL c\nSHR d\nJUMP {}\nGET f\nADD c\n\
PUT f\nDEC d\nJUMP {}\n'.format(currLi+18, currLi+18, currLi+13, currLi+3, currLi+3)
    
    curr_line_in_code += 18
    p[0] = ('f', code)

def p_divide(p):
    'expression : value DIVIDE value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    if p.lexer.isElse:
        code += 'RST f\nGET d\nJZERO {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nINC f\nJUMP {}\nRST g\nINC g\nGET d\nPUT e\nSHL e\n\
SHL g\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR g\nGET f\nADD g\nPUT f\nSHR e\nGET c\nSUB e\nPUT c\nJUMP {}\nGET f\nADD g\nPUT f\n\
'.format(currLi+37, currLi+37, currLi+13, currLi+37, currLi+37, currLi+17, currLi+34, currLi+4)
    else:
        code += 'RST f\nGET d\nJZERO {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nINC f\nJUMP {}\nRST g\nINC g\nGET d\nPUT e\nSHL e\n\
SHL g\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR g\nGET f\nADD g\nPUT f\nSHR e\nGET c\nSUB e\nPUT c\nJUMP {}\nGET f\nADD g\nPUT f\n\
'.format(currLi+36, currLi+36, currLi+12, currLi+36, currLi+36, currLi+16, currLi+33, currLi+3)

    curr_line_in_code += 36
    p[0] = ('f', code)

def p_modulo(p):
    'expression : value MOD value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    if p.lexer.isElse:
        code += '''GET d\nJPOS {}\nPUT c\nJUMP {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nRST c\nJUMP {}\nGET d\n\
PUT e\nSHL e\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR e\nGET c\nSUB e\nPUT c\nSUB d\nJPOS {}\nGET d\nSUB c\n\
JZERO {}\n'''.format(currLi + 5, currLi+32, currLi+32, currLi+14, currLi+32, currLi+32, currLi+16, currLi+12, currLi+14, currLi+12)
    else:
        code += '''GET d\nJPOS {}\nPUT c\nJUMP {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nRST c\nJUMP {}\nGET d\nPUT e\n\
SHL e\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR e\nGET c\nSUB e\nPUT c\nSUB d\nJPOS {}\nGET d\nSUB c\n\
JZERO {}\n'''.format(currLi + 4, currLi+31, currLi+31, currLi+13, currLi+31, currLi+31, currLi+15, currLi+11, currLi+13, currLi+11)
    curr_line_in_code += 31
    p[0] = ('c', code)

def p_read(p):
    'command : READ identifier SEMICOLON'
    global curr_line_in_code
    j = None
    for i in range(len(symbols_list)):
        if p[2][0] == symbols_list[i][0] and symbols_list[i][5] == currProcedure:
            j = i
    if not j == None:
        symbols_list[j][4] = True
    code = 'READ\nPUT c\n' + loadValuesToRegs([p[2]], ['b'], p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
    curr_line_in_code += 4
    p[0] = code

def p_write(p):
    'command : WRITE value SEMICOLON'
    global curr_line_in_code
    code = loadValuesToRegs([p[2]], ['a'], p.lexer.lineno-1, False) + 'WRITE\n'
    curr_line_in_code += 1
    p[0] = code

def p_value_numb(p):
    'value : NUMBER'
    p[0] = [p[1]]
    
def p_value_id(p):
    'value : identifier'
    p[0] = p[1]

def p_identifier(p):
    'identifier : VARID'
    p[0] = [p[1], False] # False means that this variable is not an array

def p_array_identifier(p):
    '''identifier : VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN VARID SQRPAREN'''
    p[0] = [p[1], True, p[3]] # True means that this variable is an array

### SYNTAX ERRORS ###

def p_error(p):
    raise SyntaxError("Error: Syntax error in line {}.".format(p.lexer.lineno-1))

programme = ''
compiled = ''

with open(sys.argv[1], "r") as f:
    programme = f.read()
    lex = lexer
    parser = yacc.yacc()

try:
    compiled = parser.parse(programme, tracking=True)
    with open(sys.argv[2], "w") as file:
        file.write(compiled)
except Exception as ex:
    print("Error: ", ex)