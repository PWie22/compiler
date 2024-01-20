
import ply.yacc as yacc
from myLexer import build_lexer, tokens
import sys

# ta tablica będzie zawierać wszystkie zadeklarowane symbole w postaci: (nazwa_symbolu, czy_tablica, pojemność_tablicy, miejsce_w_pamięci, czy_zainicjowana)
# nazwa_procedury tylko, jeżeli zmienna pochodzi z procedury; jeszcze musi być adres pamięci
symbols_array = []
# każdy element procedures_list będzie postaci (nazwa_procedury, gdzie_początek, gdzie_koniec, adres_assemblerowy) - main też musi być tu dodany
procedures_list = []
first_free_mem_index = 0
# curr_line_in_code - obecna linijka w generowanym kodzie, czy to zadziała???
curr_line_in_code = 0

### SECTION FOR ALL FUNCTIONS NECESARRY FOR THE PARSER ###

# funkcja dodająca nową nazwę zmiennej do zbioru już zadeklarowanych zmiennych
def addSymbolToArray(varName, ifArray, capacity, lineNumb):
    global symbols_array, first_free_mem_index
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName:
            j = i
    if j != None:
        print("Error: Redeclaration of variable {} in line {}.".format(varName, lineNumb))
    else:
        symbols_array.append([varName, ifArray, capacity, first_free_mem_index, False])
        #print(symbols_array[len(symbols_array)-1])
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
    # najpierw trzeba znaleźć, gdzie w pamięci jest zmienna o danej nazwie i potem odczytać jej wartość
    global symbols_array, curr_line_in_code
    code = ''
    j = None
    #print("variable: ", varName)
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line {}.".format(varName, lineNumb))
    else:
        #code += self.loadValueToRegister(regName, symbols_array[j][3])
        #code += loadValueToRegister('b', symbols_array[j][3]) + 'LOAD b\nPUT {}\n'.format(regName)
        #print('gdzie indziej: ', symbols_array[j][3], " ", symbols_array[j])
        code += loadValueToRegister('b', symbols_array[j][3])
        if not onlyAddress:
            code += 'LOAD b\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
        return code

# można by to zrobić wyżej, ale tablica może być indeksowana zmienną, więc wygodniej będzie zrobić osobną funkcję
# do rejestru jest wkładany tylko element tablicy; index - pozycja rządanego elementu
def loadArrayToRegister(arrName, regName, index, lineNumb, onlyAddress):
    global symbols_array, curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == arrName:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared array {} in line {}.".format(arrName, lineNumb))
    else:
        if type(index) is int:
            # tablica indeksowana liczbą
            #code += loadValueToRegister('b', symbols_array[j][3]+index-1) + 'LOAD b\nPUT {}'.format(regName)
            code += loadValueToRegister('b', symbols_array[j][3]+index)
        else:
            # tablica indeksowana zmienną
            #code += loadVariableToRegister(index, 'c', lineNumb) + loadValueToRegister('a', symbols_array[j][3]) + 'ADD c\nDEC a\nPUT b\nLOAD b\nPUT {}\n'.format(regName)
            code += loadVariableToRegister(index, 'c', lineNumb, False) + loadValueToRegister('a', symbols_array[j][3]) + 'ADD c\nDEC a\nPUT b\n'
            curr_line_in_code += 3
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
        print(values[i])
        #if type(values[i][0]) is tuple:
        #if not values[i][1]:
        #if not values[i][1]:
        if not values[i][0][0][1]:
        #if isinstance(values[i][0], tuple):
            print(values[i][1])
            #if values[i][0][1]:
            #if values[i][1]:
            if values[i][1]:
                # to jest element tablicy
                #code += loadArrayToRegister(values[i][1][0], regs[i], values[i][1][2], lineNumb, onlyAddress)
                code += loadArrayToRegister(values[i][0][0][0], regs[i], values[i][2], lineNumb, onlyAddress)
            else:
                # to jest zwykła zmienna
                #code += loadVariableToRegister(values[i][0][0], regs[i], lineNumb, onlyAddress)
                code += loadVariableToRegister(values[i][0][0][0], regs[i], lineNumb, onlyAddress)
        else:
            # to jest zwykła liczba
            #code += loadValueToRegister(regs[i], int(values[i][0]))
            code += loadValueToRegister(regs[i], int(values[i][0][0][0]))
        #curr_line_in_code += len(code.split('\n'))
    return code

    ### MAIN PART OF THE PARSER ###

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
        
def p_program(p):
    '''program : procedures main'''
    if not p[1]:
        print("tutaj")
        p[0] = p[2] + 'HALT'
    else:
        procLen = len(p[1].split('\n')) + 1
        p[0] = 'JUMP {}'.format(procLen) + p[1] + p[2] + 'HALT'
    
def p_main(p):
    '''main : PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END'''
    if len(p) == 7:
        # tutaj dodać funkcję dodającą nazwy zadeklarowanych zmiennych do tablicy
        p[0] = p[5]
    else:
        p[0] = p[4]
        # co tutaj zrobić

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END
                    |'''
    global procedures_list
    if (len(p) == 1):
        print("okej")
    elif (len(p) == 9):
        #p[0] = p[1] + p[7] + 'HALT'
        #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[8]].lineno
        proc_address = len(p[1].split('\n')) + 1
        procedures_list.append(p[3][0], p[3][1], p.parser.token_slice[p.slice[8]].lineno, proc_address)
        # chyba jeszcze gdzieś na początku musi być jakiś jump do linijki, w której zaczyna się program
        p[0] = p[7]
    else:
        #p[0] = p[1] + p[6] + 'HALT'
        #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[7]].lineno
        proc_address = len(p[1].split('\n')) + 1
        procedures_list.append(p[3][0], p[3][1], p.parser.token_slice[p.slice[7]].lineno, proc_address)
        p[0] = p[6]

def p_proc_head(p):
    'proc_head : VARID LPAREN args_decl RPAREN'
    global procedures_list
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if j != None:
        raise Exception("Error: Redaclaration of procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
        #procedures_list.append([p[1], p.lineno, 0])
        p[0] = (p[1], p.lineno)

def p_command_proc_call(p):
    'command : proc_call SEMICOLON'
    # tutaj trzeba napisać kod wywołania procedury

def p_proc_call(p):
    'proc_call : VARID LPAREN args RPAREN'
    global procedures_list
    j = -1
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if j == -1:
        raise Exception("Error: Calling unexisting procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
        line_of_call = p.lineno
        if line_of_call < procedures_list[j][1]:
            # ten przypadek chyba nie zajdzie, bo przed zadeklarowaniem procedury nie ma jej w procedures_list
            raise Exception("Error: Calling procedure {} in line {} before it is declared.".format(p[1], p.lexer.lineno-1))
        elif line_of_call > procedures_list[j][1] and line_of_call < procedures_list[j][2]:
            raise Exception("Error: Recursive call of procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
        else:
            print()
            # tutaj trzeba dodać skok do miejsca, w którym zaczyna się procedura - ale p.lexer.lineno daje nam linijkę w kodzie,
            # więc trzeba jakoś inaczej znaleźć adres skoku
    # teraz chyba trzeba dodać else, żeby dodać jump???

# w args_decl są deklarowane nazwy zmiennych procedury
# w args są podawane argumenty do procedury

def p_array_proc_decl(p):
    '''args_decl : args_decl COMMA ARRAYSIGN VARID
                    | ARRAYSIGN VARID'''
    
def p_var_proc_decl(p):
    '''args_decl : args_decl COMMA VARID
                    | VARID'''

def p_args_proc(p):
    '''args : args COMMA VARID
            | VARID'''
    
### DECLARATIONS OF VARIABLES USED IN A FUNCTION ###
    
def p_array_use(p):
    '''declarations : declarations COMMA VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN NUMBER SQRPAREN'''
    line = p.lexer.lineno-1 # numer linii, w której jest dopasowany tekst
    if len(p) == 7:
        addSymbolToArray(p[3], True, int(p[5]), line)
    else:
        addSymbolToArray(p[1], True, int(p[3]), line)
    
def p_var_use(p):
    '''declarations : declarations COMMA VARID
                    | VARID'''
    line = p.lexer.lineno-1
    #if p[1] != None:
    if len(p) == 4:
        addSymbolToArray(p[3], False, 0, line)
    else:
        addSymbolToArray(p[1], False, 0, line)

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
    codeLen = 0
    j = None
    #print("p[1][0][0]: ", p[1][0][0], " ", p[1])
    for i in range(len(symbols_array)):
        #if p[1][0] == symbols_array[i][0]:
        if p[1][0][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Assigning value to undeclared variable {} in line {}.".format(p[1][0], p.lexer.lineno-1))
    else:
        symbols_array[j][4] = True
        #code += loadValueToRegister('b', symbols_array[j][3]) + str(p[3][0]) + 'STORE b\n'
        #ładowanie adresu zmiennej do rejestru, żeby móc zapisać tam jej nową wartość
        #code += loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True)
        #code += loadValuesToRegs((p[1][0][0],), ('b',), p.lexer.lineno-1, True)
        if type(p[3][0]) is str:
            # to jest wyrażenie
            code += p[3][1] + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'GET {}\nSTORE b\n'.format(p[3][0])
        else:
            # to jest liczba, zmienna albo element tablicy
            code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, True) + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
        curr_line_in_code += 2
        p[0] = code

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    global curr_line_in_code
    code = ''
    # trzeba zapisać to, co mamy condition i commands
    commLen = len(p[4].split('\n'))
    print(p[2], " ", p[4], " commLen: ", commLen, " curr: ", curr_line_in_code, " ", type(p[2]))
    #if p[2] is tuple:
    #if len(p[2]) > 1:
    if isinstance(p[2], tuple):
        # w warunku występuje >= lub <= - są tam dwa skoki zamiast jednego, dlatego ten przypadek osobno
        #code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + commLen)
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen + 2) + p[2][0][2] + '{}\n'.format(curr_line_in_code + 1)
        #curr_line_in_code += 6 + commLen # 6 to długość kodu dla tego warunku
    else:
        # w warunku nie ma >= ani <=
        #code += p[2] + '{}\n'.format(curr_line_in_code + commLen) - w curr_line_in_code już jest zawarte commLen
        code += p[2] + '{}\n'.format(curr_line_in_code + 1)
        condLen = len(p[2].split('\n'))
        #curr_line_in_code += condLen + commLen
    #p[0] = p[2] + p[4]
    p[0] = code + p[4]

def p_if_else_statement(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    global curr_line_in_code
    code = ''
    # trzeba zapisać to, co mamy condition, commands i commands
    # czy nie potrzebuję tutaj adresów skoków, żeby przeskakiwać if albo else w zależności, czy warunek jest prawdziwy, czy nie
    commLen1 = len(p[4].split('\n'))
    commLen2 = len(p[6].split('\n'))
    if p[2] is tuple:
        # zastanowić się nad dodaniem dodatkowo condLen
        code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + commLen1) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code + commLen1 + commLen2) + p[6]
        curr_line_in_code += 6 + commLen1 + commLen2 + 1 # 6 to długość kodu dla tego warunku
    else:
        code += p[2] + '{}\n'.format(curr_line_in_code + commLen1) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + commLen1 + commLen2) + p[6]
        curr_line_in_code += commLen1 + commLen2
    #p[0] = p[2] + p[4] + p[6]
    p[0] = code

def p_while_loop(p):
    'command : WHILE condition DO commands ENDWHILE'
    global curr_line_in_code
    code = ''
    condLen = len(p[2].split('\n'))
    commLen = len(p[4].split('\n'))
    print("WHILE curr ", curr_line_in_code, " commlen ", commLen)
    # potrzebuję zapisać to, co jest w condition i commands, trzeba mieć adres skoku???
    if p[2] is tuple:
        #code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + 3 + commLen + 1) + p[4] \
                #+ 'JUMP {}\n'.format(curr_line_in_code)
        code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code - commLen + 2) + p[2][2] + '{}\n'.format(curr_line_in_code + 1) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code)
        #curr_line_in_code += 6 + commLen + 1
    else:
        print(" ", condLen)
        #code += p[2] + '{}\n'.format(curr_line_in_code + condLen + commLen) + p[4] + 'JUMP {}\n'.format(curr_line_in_code)
        code += p[2] + '{}\n'.format(curr_line_in_code + 2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code- condLen - commLen + 2)
        #curr_line_in_code += condLen + commLen + 1
    curr_line_in_code += 1
    p[0] = code

def p_repeat_loop(p):
    'command : REPEAT commands UNTIL condition SEMICOLON'
    # potrzebuję zapisać to, co mamay z commands i condition
    global curr_line_in_code
    code = ''
    commLen = len(p[2].split('\n'))
    if p[2] is tuple:
        code += p[4] + p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3 + 1) + 'JUMP {}\n'.format(curr_line_in_code) + p[2][2] \
                + '{}\n'.format(curr_line_in_code + commLen + 6 + 2) + 'JUMP {}\n'.format(curr_line_in_code)
    else:
        print()
        code += p[4] + p[2] + '{}\n'.format(curr_line_in_code + commLen + 1) + 'JUMP {}\n'.format(curr_line_in_code)
    p[0] = code

### CONDITIONS ###

def p_equal(p):
    'condition : value EQUAL value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJPOS '
    curr_line_in_code += 7
    p[0] = code
    
def p_negation(p):
    'condition : value NEG value'
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJZERO '
    curr_line_in_code += 7
    p[0] = code

def p_greater_less(p):
    '''condition : value GREATER value
                    | value LESS value'''
    global curr_line_in_code
    code = ''
    if p[2] == ">":
        code += loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'b'], p.lexer.lineno-1, False)
    code += 'GET b\nSUB d\nJZERO '
    curr_line_in_code += 3
    p[0] = code

def p_greater_less_equal(p):
    '''condition : value GREATEREQ value
                    | value LESSEQ value'''
    global curr_line_in_code
    code = ''
    # te dwa rodzaje warunków są takie same, są własną odwrotnością, wystarczy wstawić wartości do rejestrów odwrotnie
    if p[2] == ">=":
        code += loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno, False)
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'b'], p.lexer.lineno, False)
    p[0] = ((code, 'GET b\nSUB d\nJPOS ', 'GET d\nSUB b\nJPOS '),)
    curr_line_in_code += 6

### EXPRESSIONS ###

def p_expression_value(p):
    'expression : value'
    p[0] = p[1]
    
def p_add_sub(p):
    '''expression : value PLUS value
                    | value MINUS value'''
    global curr_line_in_code
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
    if p[2] == '+':
        code += 'GET b\nADD d\nPUT f\n'
    else:
        code += 'GET b\nSUB d\nPUT f\n'
    curr_line_in_code += 3
    p[0] = ('f', code)

def p_multiply(p):
    'expression : value TIMES value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    #code += 'RST c\nGET b\nSUB d\nJPOS  \nGET b\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n \nGET d\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n'
    #code += 'RST e\nGET d\nSHR a\nSHL a\nPUT c\nGET d\nSUB c\nJZERO \nGET e\nADD b\nPUT e\nSHL b\nSHR d\nGET d\nJPOS \n'
    code += 'RST e\nGET b\nJZERO \nGET d\nJZERO \nPUT c\nSHR c\nSHL c\nSUB c\nJPOS \nSHL b\nSHR d\nJUMP \nGET e\nADD b\nPUT e\nJUMP \nGET e'
    p[0] = ('e', code)

def p_divide(p):
    'expression : value DIVIDE value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    #code += 'RST c\nRST f\nGET d\nPUT e\nSHL e\nGET b\nJZERO  \nSUB e\nJZERO  \nINC c\nJUMP  \nGET e\nJZERO  \nSUB b\nJZERO  \nSHL c\nGET c\nADD f\nPUT f\nRST c\
        #\nSHR e\nGET b\nSUB e\nSHL a\nPUT e\nJUMP  \n'
    #code += 'RST e\nRST c\nGET d\nPUT c\nGET b\nSUB c\nJZERO 9\nINC e\nJPOS \nGET c\nSUB b\nJPOS \nINC e\nJUMP \nSHL c\nGET b\nSUB c\
        #\nJZERO \nINC e\nINC e\nJPOS\nSHR c\nGET b\nSUB c\nPUT b\nJUMP \n'
    code += 'GET d\nPUT e\nGET b\nPUT c\nGET b\nJZERO \nGET d\nJZERO \nGET b\nSUB e\nPUT b\nGET c\nSUB d\nADD b\nJZERO \nGET d\nSUB c\nJZERO \nJUMP \nRST g\n\
        JUMP \nRST g\nINC g\nJUMP \nGET d\nPUT b\nGET c\nPUT e\nRST g\nRST f\nINC f\nGET e\nJZERO \nSHR e\nSHR b\nJUMP \nGET c\nPUT e\nGET b\nJZERO \n\
        SHR b\nSHL e\nINC f\nJUMP \nGET d\nPUT b\nGET f\nJZERO \nINC b\n GET b\nSUB d\nPUT b\nJZERO \nDEC b\nDEC f\nSHL g\nINC g\nSHR e\nGET b\nPUT d\n\
        JUMP \nGET d\nPUT b\nSHL g\nDEC f\nSHR e\nJUMP \nGET g\n'
    p[0] = ('g', code)

def p_modulo(p):
    'expression : value MOD value'
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    code += 'RST e\n'
    p[0] = ('e', code)

def p_read(p):
    'command : READ identifier SEMICOLON'
    code = ''
    j = None
    for i in range(len(symbols_array)):
        #if p[2][0][0] == symbols_array[i][0]:
        if p[2][0][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line {}.".format(p[2][0], p.lexer.lineno-1))
    else:
        #print(p[2])
        if p[2][1]:
            # to jest tablica
            if type(p[2][2]) is int:
                #code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]+p[2][0][2]-1) + 'STORE b\n'
                code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]+p[2][2]) + 'STORE b\n'
            else:
                code += 'READ\n' + loadVariableToRegister(p[2][2], 'a', p.lexer.lineno-1, False) + loadValueToRegister('b', symbols_array[j][3]) + 'ADD b\nDEC a\nPUT b\nREAD\nSTORE b\n'
        else:
            # to jest zmienna
            code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]) + 'STORE b\n'
        # zmienna jest zainicjowana, więc ustawiam wartość na True
        symbols_array[j][4] = True
    p[0] = code

def p_write(p):
    'command : WRITE value SEMICOLON'
    code = ''
    #if p[2][1]:
    #if p[2][0] is not tuple:
    if not isinstance(p[2][0], tuple):
        # to jest liczba
        #print(p[2], " ", type(p[2][0]))
        code += loadValueToRegister('a', p[2][0]) + 'WRITE\n'
    else:
        # to jest albo zmienna albo element tablicy
        #if p[2][0][1]:
        if p[2][1]:
            # to jest tablica
            #code += loadArrayToRegister(p[2][0][0], 'a', p[2][0][2], p.lexer.lineno-1, False)
            code += loadArrayToRegister(p[2][0][0][0], 'a', p[2][0][2], p.lexer.lineno-1, False) + 'WRITE\n'
        else:
            # to jest zmienna
            #code += loadVariableToRegister(p[2][0][0], 'a', p.lexer.lineno-1, False) + 'WRITE\n'
            code += loadVariableToRegister(p[2][0][0][0], 'a', p.lexer.lineno-1, False) + 'WRITE\n'
    p[0] = code

def p_value_numb(p):
    'value : NUMBER'
    #p[0] = ((p[1], True),)
    #p[0] = (p[1], True)
    p[0] = (((p[1], True),),)
    
def p_value_id(p):
    'value : identifier'
    # czy nie trzeba zamienić elementów tablicy p na int
    #p[0] = (p[1], False)
    #p[0] = ((p[1],), False)
    p[0] = p[1]

def p_identifier(p):
    'identifier : VARID'
    # w nawiasie podana jest najpierw nazwa zmiennej, a potem, czy jest tablicą
    #p[0] = (p[1], False)
    p[0] = (((p[1], False),), False)
    
def p_array_identifier(p):
    '''identifier : VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN VARID SQRPAREN'''
    #p[0] = (p[1], True, p[3])
    p[0] = (((p[1], False),), True, p[3])

### SYNTAX ERRORS ###

def p_error(p):
    print(p)
    raise SyntaxError("Error: Syntax error in line {}.".format(p.lexer.lineno-1))

programme = ''
compiled = ''

with open(sys.argv[1], "r") as f:
    programme = f.read()
    lexer = build_lexer()
    parser = yacc.yacc()

#try:
    compiled = parser.parse(programme, tracking=True)
    with open(sys.argv[2], "w") as file:
        file.write(compiled)
#except Exception as ex:
    #print(ex, " ")