
import ply.yacc as yacc
from myLexer import lexer, tokens
import sys

# ta tablica będzie zawierać wszystkie zadeklarowane symbole w postaci: (nazwa_symbolu, czy_tablica, pojemność_tablicy, miejsce_w_pamięci, czy_zainicjowana, nazwa_procedury)
# nazwa_procedury tylko, jeżeli zmienna pochodzi z procedury; jeszcze musi być adres pamięci
symbols_array = []
# każdy element procedures_list będzie postaci (nazwa_procedury, gdzie_początek, gdzie_koniec, adres_assemblerowy, zmienne_z_nawiasu, gdzie_w_pamięci_adres_powrotu)
procedures_list = []
first_free_mem_index = 0
# curr_line_in_code - obecna linijka w generowanym kodzie
curr_line_in_code = 0
# isinprocedure - zmienna, która jest wykorzystywana, żeby dobrze dodać zmienne procedury i maina do tablicy symboli
currProcedure = None
# temp_arr to tablica na dodanie symboli z nawiasu procedury, żeby sprawdzić, czy nie powtarzają symboli, podczas deklarowania procedury
temp_arr = []
# temp_arr2 to tablica na dodanie symboli z nawiasu procedury, gdy jest ona wywoływana
temp_arr2 = []
# decl_arr to tablica na przechowanie zmiennych własnych procedury
decl_arr = []
# howdeep to zmienna, która mówi, jak głęboko w pętlach i/lub ifach jesteśmy - jedno wejście do conditions zwiększa jej wartość o 1, a wyjście z pętli/ifa zmniejsza o 1
howdeep = 0
# procedures_code to zmienna, w ktorej zapisywany jest kod procedur
procedures_code = ''

### SECTION FOR ALL FUNCTIONS NECESARRY FOR THE PARSER ###

# funkcja dodająca nową nazwę zmiennej do zbioru już zadeklarowanych zmiennych
def addSymbolToArray(varName, ifArray, capacity, lineNumb, currProc):
    global symbols_array, first_free_mem_index
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName and symbols_array[i][5] == currProc:
            j = i
    if j != None:
        print("Error: Redeclaration of variable {} in line {}.".format(varName, lineNumb))
    else:
        symbols_array.append([varName, ifArray, capacity, first_free_mem_index, False, currProc])
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
    global symbols_array, curr_line_in_code, currProcedure, procedures_list, howdeep
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName and symbols_array[i][5] == currProcedure:
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Usage of undeclared variable {} in line {}.".format(varName, lineNumb))
        else:
            for i in range(len(procedures_list)):
                if procedures_list[i][0] == currProcedure:
                    j = i
                    break
            k = None
            for i in range(len(procedures_list[j][4])):
                if procedures_list[j][4][i][0] == varName:
                    k = i
                    break
            if k == None:
                raise Exception("Error: Usage of undeclared variable {} in procedure {} in line {}.".format(varName, currProcedure, lineNumb))
            elif procedures_list[j][4][k][1]:
                raise Exception("Error: Incorrect usage of variable {} in procedure {} in line {}.".format(varName, currProcedure, lineNumb))
            else:
                code += loadValueToRegister('b', procedures_list[j][4][k][2]) + 'LOAD b\nPUT {}\n'.format(regName)
                curr_line_in_code += 2
                if not onlyAddress:
                    code += 'LOAD b\nPUT {}\n'.format(regName)
                    curr_line_in_code += 2
                return code
    elif symbols_array[j][1]:
        raise Exception("Error: Incorrect usage of array {} in line {}.".format(varName, lineNumb))
    elif howdeep < 2 and not symbols_array[j][4]:
        raise Exception("Error: Usage of uninitialized variable {} in line {}.".format(symbols_array[j][0], lineNumb))
    else:
        if howdeep >= 2 and not symbols_array[j][4]:
            print("Warning: Variable {} has not been initialized yet (line {}).".format(symbols_array[j][0], lineNumb))
        code += loadValueToRegister('b', symbols_array[j][3])
        if not onlyAddress:
            code += 'LOAD b\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
        return code

def loadArrayToRegister(arrName, regName, index, lineNumb, onlyAddress):
    global symbols_array, curr_line_in_code, currProcedure, procedures_list
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == arrName:
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Usage of undeclared array {} in line {}.".format(arrName, lineNumb))
        else:
            for i in range(len(procedures_list)):
                if procedures_list[i][0] == currProcedure:
                    j = i
            k = None
            for i in range(len(procedures_list[j][4])):
                if procedures_list[j][4][i][0] == arrName:
                    k = i
            if k == None:
                raise Exception("Error: Usage of undeclared array {} in line {}.".format(arrName, lineNumb))
            else:
                if type(index) is int:
                    code += loadValueToRegister('b', procedures_list[j][4][k][2]) + 'LOAD b\n' + loadValueToRegister('b', index) + 'ADD b\nPUT b\n'
                    curr_line_in_code += 3
                else:
                    code += loadVariableToRegister(index, 'h', lineNumb, False) + loadValueToRegister('b', procedures_list[j][4][k][2]) + 'LOAD b\nADD h\nPUT b\n'
                    curr_line_in_code += 3
                if not onlyAddress:
                    code += 'LOAD b\nPUT {}\n'.format(regName)
                    curr_line_in_code += 2
    else:
        if type(index) is int:
            # tablica indeksowana liczbą
            code += loadValueToRegister('b', symbols_array[j][3]+index)
        else:
            # tablica indeksowana zmienną
            code += loadVariableToRegister(index, 'h', lineNumb, False) + loadValueToRegister('a', symbols_array[j][3]) + 'ADD h\nPUT b\n'
            curr_line_in_code += 2
        if not onlyAddress:
            code += 'LOAD b\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
    return code

# funkcja potrzebna, żeby nie sprawdzać czym są val1 i val2 wiele razy
# w values są trzymane dwójki (val, is_numb) - val to wartość, is_numb to wartość boolowska, jest równa true, jeżeli to jest zwykła liczba
def loadValuesToRegs(values, regs, lineNumb, onlyAddress):
    global symbols_array, curr_line_in_code
    code = ''
    for i in range(len(values)):
        if isinstance(values[i], int): # będzie tak tylko w przypadku procedury
            code += loadValueToRegister(regs[i], values[i])
        else:
            if not values[i][0][0][1]:
                if values[i][1]:
                    # to jest element tablicy
                    code += loadArrayToRegister(values[i][0][0][0], regs[i], values[i][2], lineNumb, onlyAddress)
                else:
                    # to jest zwykła zmienna
                    code += loadVariableToRegister(values[i][0][0][0], regs[i], lineNumb, onlyAddress)
            else:
                # to jest zwykła liczba
                code += loadValueToRegister(regs[i], int(values[i][0][0][0]))
    return code

    ### MAIN PART OF THE PARSER ###

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
        
def p_program(p):
    '''program : procedures main'''
    global procedures_code
    if not p[1]:
        print("tutaj")
        p[0] = p[2] + 'HALT'
    else:
        procLen = len(p[1].split('\n'))
        p[0] = 'JUMP {}\n'.format(len(procedures_code.split('\n'))) + procedures_code + p[2] + 'HALT'
    
def p_main(p):
    '''main : PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END'''
    if len(p) == 7:
        p[0] = p[5]
    else:
        p[0] = p[4]

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END
                    |'''
    global procedures_list, currProcedure, temp_arr, decl_arr, first_free_mem_index, curr_line_in_code, procedures_code
    code = ''
    if (len(p) == 1):
        currProcedure = None
        if p.lexer.hasProcedures:
            curr_line_in_code += 1
    elif (len(p) == 9):
            temp_arr = []
            decl_arr = []
            code += loadValueToRegister('b', procedures_list[len(procedures_list)-1][5]) + 'LOAD b\nJUMPR a\n'
            curr_line_in_code += 2
            currProcedure = None
            p[0] = p[7] + code
            procedures_code += p[7] + code
    else:
        temp_arr = []
        code += loadValueToRegister('b', procedures_list[len(procedures_list)-1][5]) + 'LOAD b\nJUMPR a\n'
        curr_line_in_code += 2
        currProcedure = None
        p[0] = p[6] + code
        procedures_code += p[6] + code

def p_proc_head(p):
    'proc_head : VARID LPAREN args_decl RPAREN'
    global procedures_list, currProcedure, curr_line_in_code, first_free_mem_index
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if not j == None:
        raise Exception("Error: Redaclaration of procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
        procedures_list.append([p[1], p.lexer.lineno-1, 0, curr_line_in_code, temp_arr, first_free_mem_index])
        first_free_mem_index += 1
        currProcedure = p[1]
        p[0] = (p[1], p.lineno)

def p_command_proc_call(p):
    'command : proc_call SEMICOLON'
    p[0] = p[1]

def p_proc_call(p):
    'proc_call : VARID LPAREN args RPAREN'
    global procedures_list, currProcedure, symbols_array, curr_line_in_code, temp_arr, temp_arr2
    code = ''
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if j == None:
        raise Exception("Error: Calling unexisting (or not yet declared) procedure {} in line {}.".format(p[1], p.lexer.lineno))
    elif currProcedure == procedures_list[j][0]:
        raise Exception("Error: Recursive call in procedure {} in line {}.".format(p[1], p.lexer.lineno))
    else:
            m = None
            for i in range(len(temp_arr2)):
                for k in range(len(symbols_array)):
                    if temp_arr2[i] == symbols_array[k][0]:
                        m = k
                        break
                if m == None:
                    for n in range(len(temp_arr)):
                        if temp_arr2[i] == temp_arr[n][0]:
                            m = n
                            break
                    if m == None:
                        raise Exception("Error: Usage of undeclared variable {} in procedure {} in line {}.".format(temp_arr2[i], currProcedure, p.lexer.lineno))
                    else:
                        procNumb = None
                        for n in range(len(procedures_list)):
                            if procedures_list[n][0] == currProcedure:
                                procNumb = n
                                break
                        for n in range(len(procedures_list[procNumb][4])): # j to numer procedury, ktora wywoluje; wczesniej zamiast procName bylo j
                            if procedures_list[procNumb][4][n][0] == temp_arr2[i]:
                                break
                        code += loadValueToRegister('b', procedures_list[procNumb][4][n][2]) + 'LOAD b\n' + loadValueToRegister('b', procedures_list[j][4][i][2]) + 'STORE b\n'
                        curr_line_in_code += 2
                        m = None
                else: # symbol został wcześniej zadeklarowany i znajduje się w symbols_array
                    print(procedures_list[j][4], " ", i)
                    if symbols_array[m][1] == procedures_list[j][4][i][1]: # typy się zgadzają
                        symbols_array[m][4] = True # dodane, ponieważ można wywołać procedurę z parametrami, które były wcześniej tylko zadeklarowane, ale nie zainicjowane
                        code += loadValueToRegister('b', procedures_list[j][4][i][2]) + loadValueToRegister('a',symbols_array[m][3]) + 'STORE b\n'
                        curr_line_in_code += 1
                        m = None
                    else: # typy się nie zgadzają
                        raise Exception("Error: Calling procedure {} with an argument ({}) of wrong type in line {}.".format(p[1], symbols_array[m][0], p.lexer.lineno))
            code += loadValueToRegister('b', procedures_list[j][5]) + 'RST a\nINC a\nSHL a\nSHL a\nSTRK c\nADD c\nSTORE b\nJUMP {}\n'.format(procedures_list[j][3])
            curr_line_in_code += 8
            p[0] = code
    temp_arr2 = []

# w args_decl są deklarowane nazwy zmiennych procedury
# w args są podawane argumenty do procedury

def p_array_proc_decl(p):
    '''args_decl : args_decl COMMA ARRAYSIGN VARID
                    | ARRAYSIGN VARID'''
    global temp_arr, first_free_mem_index
    # pierwsza wartość to nazwa, a druga to, że jest tablicą, trzecia to przydzielone miejsce w tablicy
    if len(p) == 5:
        temp_arr.append([p[4], True, first_free_mem_index])
    else:
        temp_arr.append([p[2], True, first_free_mem_index])
    first_free_mem_index += 1
    
def p_var_proc_decl(p):
    '''args_decl : args_decl COMMA VARID
                    | VARID'''
    global temp_arr, first_free_mem_index
    if len(p) == 4:
        temp_arr.append([p[3], False, first_free_mem_index])
    else:
        temp_arr.append([p[1], False, first_free_mem_index])
    first_free_mem_index += 1

def p_args_proc(p):
    '''args : args COMMA VARID
            | VARID'''
    global temp_arr2
    if len(p) == 4:
        temp_arr2.append(p[3])
    else:
        temp_arr2.append(p[1])
    
### DECLARATIONS OF VARIABLES USED IN A FUNCTION ###
    
def p_array_use(p):
    '''declarations : declarations COMMA VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN NUMBER SQRPAREN'''
    line = p.lexer.lineno-1 # numer linii, w której jest dopasowany tekst
    if len(p) == 7:
        addSymbolToArray(p[3], True, int(p[5]), line, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(temp_arr)):
                if temp_arr[i][0] == p[3]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(temp_arr[j][0], currProcedure, p.lexer.lineno))
            else:
                decl_arr.append(p[3])
    else:
        addSymbolToArray(p[1], True, int(p[3]), line, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(temp_arr)):
                if temp_arr[i][0] == p[1]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(temp_arr[j][0], currProcedure, p.lexer.lineno))
            else:
                decl_arr.append(p[1])
    
def p_var_use(p):
    '''declarations : declarations COMMA VARID
                    | VARID'''
    global decl_arr, currProcedure
    line = p.lexer.lineno-1
    if len(p) == 4:
        addSymbolToArray(p[3], False, 0, line, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(temp_arr)):
                if temp_arr[i][0] == p[3]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(temp_arr[j][0], currProcedure, p.lexer.lineno-1))
            else:
                decl_arr.append(p[3])
    else:
        addSymbolToArray(p[1], False, 0, line, currProcedure)
        if not currProcedure == None:
            j = None
            for i in range(len(temp_arr)):
                if temp_arr[i][0] == p[1]:
                    j = i
            if j is not None:
                raise Exception("Error: Symbol {} reused in procedure {} in line {}.".format(temp_arr[j][0], currProcedure, p.lexer.lineno-1))
            else:
                decl_arr.append(p[1])

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
    global symbols_array, curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_array)):
        #if p[1][0] == symbols_array[i][0]:
        if p[1][0][0][0] == symbols_array[i][0] and symbols_array[i][5] == currProcedure:
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Usage of undeclared variable {} in line {}.".format(p[1][0][0][0], p.lexer.lineno))
        else:
            for i in range(len(procedures_list)):
                if procedures_list[i][0] == currProcedure:
                    j = i
            k = None
            for i in range(len(procedures_list[j][4])):
                if procedures_list[j][4][i][0] == p[1][0][0][0]:
                    k = i
            if k == None:
                raise Exception("Error: Usage of undeclared variable {} in line {}.".format(p[1][0][0][0], p.lexer.lineno))
            else:
                if type(p[3][0]) is str:
                    if p[1][1]:
                        code += p[3][1] + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'PUT b\nGET {}\nSTORE b\n'.format(p[3][0])
                        curr_line_in_code += 3
                    else:
                        code += p[3][1] + loadValuesToRegs((procedures_list[j][4][k][2],), ('b',), p.lexer.lineno-1, True) + 'LOAD b\nPUT b\nGET {}\nSTORE b\n'.format(p[3][0])
                        curr_line_in_code += 4
                else:
                    if p[1][1]:
                        code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, False) + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'PUT b\nGET c\nSTORE b\n' # bylo LOAD b\nPUT b\nGET c\nSTORE b\n'
                        curr_line_in_code += 3
                    else:
                        code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, False) + loadValuesToRegs((procedures_list[j][4][k][2],), ('b',), p.lexer.lineno-1, True) + 'LOAD b\nPUT b\nGET c\nSTORE b\n'
                        curr_line_in_code += 4
    else:
        symbols_array[j][4] = True
        if type(p[3][0]) is str:
            # to jest wyrażenie
            code += p[3][1] + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'GET {}\nSTORE b\n'.format(p[3][0])
        else:
            # to jest liczba, zmienna albo element tablicy
            code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, False) + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
        curr_line_in_code += 2
    p[0] = code

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    global curr_line_in_code, howdeep
    code = ''
    commLen = len(p[4].split('\n'))
    if isinstance(p[2], tuple):
        # w warunku występuje >= lub <= - są tam dwa skoki zamiast jednego, dlatego ten przypadek osobno
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen + 1) + p[2][0][2] + '{}\n'.format(curr_line_in_code)
    else:
        # w warunku nie ma >= ani <=
        code += p[2] + '{}\n'.format(curr_line_in_code)
    howdeep -= 1
    p[0] = code + p[4]

def p_if_else_statement(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    global curr_line_in_code, howdeep
    code = ''
    commLen1 = len(p[4].split('\n'))
    commLen2 = len(p[6].split('\n'))
    if isinstance(p[2], tuple):
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen1 - commLen2 + 2) + p[2][0][2] + '{}\n'.format(curr_line_in_code-commLen2 + 2) \
              + p[4] + 'JUMP {}\n'.format(curr_line_in_code + 1) + p[6]
        curr_line_in_code += 1
    else:
        code += p[2] + '{}\n'.format(curr_line_in_code - commLen2 + 2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + 1) + p[6]
        curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

def p_while_loop(p):
    'command : WHILE condition DO commands ENDWHILE'
    global curr_line_in_code, howdeep
    code = ''
    condLen = 0
    commLen = len(p[4].split('\n'))
    if isinstance(p[2], tuple):
        addLen = len(p[2][0][0].split('\n'))
        condLen = 6
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen + 1) + p[2][0][2] + '{}\n'.format(curr_line_in_code + 1) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen - addLen + 2)
    else:
        condLen = len(p[2].split('\n'))
        code += p[2] + '{}\n'.format(curr_line_in_code + 1) + p[4] + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen + 1)
    curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

def p_repeat_loop(p):
    'command : REPEAT commands UNTIL condition SEMICOLON'
    global curr_line_in_code, howdeep
    code = ''
    condLen = 0
    commLen = len(p[2].split('\n'))
    if isinstance(p[4], tuple):
        condLen= len(p[4][1].split('\n')) + len(p[4][2].split('\n'))
        code += p[2] + p[4][0] + p[4][1] + '{}\n'.format(curr_line_in_code - condLen - commLen) + p[4][2] \
                + '{}\n'.format(curr_line_in_code + 1) + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen)
    else:
        condLen = len(p[4].split('\n'))
        code += p[2] + p[4] + '{}\n'.format(curr_line_in_code + 1) + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen + 1)
    curr_line_in_code += 1
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
    # te dwa rodzaje warunków są takie same, są własną odwrotnością, wystarczy wstawić wartości do rejestrów odwrotnie
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
    if not p.lexer.isElse:
        code += 'RST f\nGET c\nJZERO {}\nGET d\nJZERO {}\nPUT e\nSHR e\nSHL e\nSUB e\nJPOS {}\nSHL c\nSHR d\nJUMP {}\nGET f\nADD c\n\
PUT f\nDEC d\nJUMP {}\n'.format(currLi+18, currLi+18, currLi+13, currLi+3, currLi+3)
    else:
        code += 'RST f\nGET c\nJZERO {}\nGET d\nJZERO {}\nPUT e\nSHR e\nSHL e\nSUB e\nJPOS {}\nSHL c\nSHR d\nJUMP {}\nGET f\nADD c\n\
PUT f\nDEC d\nJUMP {}\n'.format(currLi+19, currLi+19, currLi+14, currLi+4, currLi+4)
    curr_line_in_code += 18
    p[0] = ('f', code)

def p_divide(p):
    'expression : value DIVIDE value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    code += 'RST f\nGET d\nJZERO {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nINC f\nJUMP {}\nRST g\nINC g\nGET d\nPUT e\nSHL e\n\
SHL g\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR g\nGET f\nADD g\nPUT f\nSHR e\nGET c\nSUB e\nPUT c\nJUMP {}\nGET f\nADD g\nPUT f\n\
'.format(currLi+37, currLi+37, currLi+13, currLi+37, currLi+37, currLi+17, currLi+34, currLi+4)

    curr_line_in_code += 36
    p[0] = ('f', code)

def p_modulo(p):
    'expression : value MOD value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    code += 'GET d\nJPOS {}\nPUT c\nJUMP {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nRST c\nJUMP {}\nGET d\nPUT e\nSHL e\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\n\
JZERO {}\nSHR e\nGET c\nSUB e\nPUT c\nSUB d\nJPOS {}\nGET d\nSUB c\nJZERO {}\n'.format(currLi + 4, currLi+31, currLi+31, currLi+13, currLi+31, currLi+31, currLi+15, currLi+11, currLi+13, currLi+11)
    curr_line_in_code += 31
    p[0] = ('c', code)

def p_read(p):
    'command : READ identifier SEMICOLON'
    global curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if p[2][0][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line {}.".format(p[2][0], p.lexer.lineno-1))
    else:
        if p[2][1]:
            # to jest tablica
            if type(p[2][2]) is int:
                code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]+p[2][2]) + 'STORE b\n'
                curr_line_in_code += 2
            else:
                code += 'READ\n' + loadVariableToRegister(p[2][2], 'a', p.lexer.lineno-1, False) + loadValueToRegister('b', symbols_array[j][3]) + 'ADD b\nDEC a\nPUT b\nREAD\nSTORE b\n'
                curr_line_in_code += 6
        else:
            # to jest zmienna
            if symbols_array[j][1]:
                raise Exception("Error: Incorrect usage of array {} in line {}.".format(symbols_array[j][0], p.lexer.lineno-1))
            else:
                code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]) + 'STORE b\n'
                curr_line_in_code += 2
        # zmienna jest zainicjowana, więc ustawiam wartość na True
                symbols_array[j][4] = True
    p[0] = code

def p_write(p):
    'command : WRITE value SEMICOLON'
    global curr_line_in_code
    code = ''
    if p[2][0][0][1]:
        # to jest liczba
        code += loadValueToRegister('a', p[2][0][0][0]) + 'WRITE\n'
    else:
        # to jest albo zmienna albo element tablicy
        if p[2][1]:
            # to jest tablica
            code += loadArrayToRegister(p[2][0][0][0], 'a', p[2][2], p.lexer.lineno-1, False) + 'WRITE\n'
        else:
            # to jest zmienna
            code += loadVariableToRegister(p[2][0][0][0], 'a', p.lexer.lineno-1, False) + 'WRITE\n'
    curr_line_in_code += 1
    p[0] = code

def p_value_numb(p):
    'value : NUMBER'
    p[0] = (((p[1], True),),)
    
def p_value_id(p):
    'value : identifier'
    p[0] = p[1]

def p_identifier(p):
    'identifier : VARID'
    # w nawiasie podana jest najpierw nazwa zmiennej, a potem, czy jest tablicą
    p[0] = (((p[1], False),), False)
    
def p_array_identifier(p):
    '''identifier : VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN VARID SQRPAREN'''
    p[0] = (((p[1], False),), True, p[3])

### SYNTAX ERRORS ###

def p_error(p):
    print(p)
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
    print(ex, " ")