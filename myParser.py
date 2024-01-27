
import ply.yacc as yacc
from myLexer import build_lexer, tokens
import sys

# ta tablica będzie zawierać wszystkie zadeklarowane symbole w postaci: (nazwa_symbolu, czy_tablica, pojemność_tablicy, miejsce_w_pamięci, czy_zainicjowana, nazwa_procedury)
# nazwa_procedury tylko, jeżeli zmienna pochodzi z procedury; jeszcze musi być adres pamięci
symbols_array = []
# każdy element procedures_list będzie postaci (nazwa_procedury, gdzie_początek, gdzie_koniec, adres_assemblerowy, zmienne_z_nawiasu, gdzie_w_pamięci_adres_powrotu)
procedures_list = []
first_free_mem_index = 0
# curr_line_in_code - obecna linijka w generowanym kodzie, czy to zadziała???
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
        print("ifArray: ", ifArray)
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
    #print("variable: ", varName)
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName:
            j = i
    if j == None:
        if currProcedure == None:
            raise Exception("Error: Usage of undeclared variable {} in line {}.".format(varName, lineNumb))
        else:
            print(procedures_list)
            for i in range(len(procedures_list)):
                print(procedures_list[i])
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
                return code
    elif symbols_array[j][1]:
        raise Exception("Error: Incorrect usage of array {} in line {}.".format(varName, lineNumb))
    elif howdeep < 2 and not symbols_array[j][4]:
        raise Exception("Error: Usage of uninitialized variable {} in line {}.".format(symbols_array[j][0], lineNumb))
    else:
        if howdeep >= 2 and not symbols_array[j][4]:
            print("Warning: Variable {} has not been initialized yet (line {}).".format(symbols_array[j][0], lineNumb))
        #code += self.loadValueToRegister(regName, symbols_array[j][3])
        #code += loadValueToRegister('b', symbols_array[j][3]) + 'LOAD b\nPUT {}\n'.format(regName)
        #print('gdzie indziej: ', symbols_array[j][3], " ", symbols_array[j])
        code += loadValueToRegister('b', symbols_array[j][3])
        #code += loadValueToRegister(regName, symbols_array[j][3])
        if not onlyAddress:
            code += 'LOAD b\nPUT {}\n'.format(regName)
            curr_line_in_code += 2
        #code += 'PUT {}\n'.format(regName)
        #curr_line_in_code += 1
        return code

# można by to zrobić wyżej, ale tablica może być indeksowana zmienną, więc wygodniej będzie zrobić osobną funkcję
# do rejestru jest wkładany tylko element tablicy; index - pozycja rządanego elementu
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
                    code += loadValueToRegister('b', procedures_list[j][4][k][2]) + 'LOAD b\n' + loadValueToRegister('b', index) + 'ADD b\nDEC a\nPUT b\n'
                else:
                    code += loadVariableToRegister(index, 'c', lineNumb, False) + loadValueToRegister('b', procedures_list[j][4][k][2]) + 'LOAD b\nADD c\nDEC a\nPUT b\n'
                    curr_line_in_code += 3
    else:
        if type(index) is int:
            # tablica indeksowana liczbą
            #code += loadValueToRegister('b', symbols_array[j][3]+index-1) + 'LOAD b\nPUT {}'.format(regName)
            code += loadValueToRegister('b', symbols_array[j][3]+index)
        else:
            # tablica indeksowana zmienną
            #code += loadVariableToRegister(index, 'c', lineNumb) + loadValueToRegister('a', symbols_array[j][3]) + 'ADD c\nDEC a\nPUT b\nLOAD b\nPUT {}\n'.format(regName)
            print("index: ", index)
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
        if isinstance(values[i], int): # będzie tak tylko w przypadku procedury
            code += loadValueToRegister(regs[i], values[i])
        else:
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
        p[0] = 'JUMP {}\n'.format(procLen) + p[1] + p[2] + 'HALT'
    
def p_main(p):
    '''main : PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END'''
    if len(p) == 7:
        p[0] = p[5]
    else:
        p[0] = p[4]
        # co tutaj zrobić

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END
                    |'''
    global procedures_list, currProcedure, temp_arr, decl_arr, first_free_mem_index
    code = ''
    if (len(p) == 1):
        print("okej")
        currProcedure = None
        print("koniec procedur")
    elif (len(p) == 9):
            #p[0] = p[1] + p[7] + 'HALT'
            #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[8]].lineno
            #currProcedure = p[3][0]
            #proc_address = len(p[1].split('\n')) + 1
            # chyba jeszcze gdzieś na początku musi być jakiś jump do linijki, w której zaczyna się program
            temp_arr = []
            decl_arr = []
            code += loadValueToRegister('b', procedures_list[len(procedures_list)-1][5]) + 'LOAD b\nJUMPR a\n'
            print("ustawiam na none 1")
            currProcedure = None
            p[0] = p[7] + code
    else:
        #p[0] = p[1] + p[6] + 'HALT'
        #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[7]].lineno
        #currProcedure = p[3][0]
        #proc_address = len(p[1].split('\n')) + 1
        temp_arr = []
        code += loadValueToRegister('b', procedures_list[len(procedures_list)-1][5]) + 'LOAD b\nJUMPR a\n'
        print("ustawiam na none 2")
        currProcedure = None
        p[0] = p[6] + code

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
        #procedures_list.append([p[1], p.lineno, 0]); w p[3] będą zapisywane nazwy i typy zmiennych wejściowych procedury
        procedures_list.append([p[1], p.lexer.lineno-1, 0, curr_line_in_code, temp_arr, first_free_mem_index])
        first_free_mem_index += 1
        print("ustawiam na ", p[1])
        currProcedure = p[1]
        print("proce_head ", currProcedure)
        p[0] = (p[1], p.lineno)

def p_command_proc_call(p):
    'command : proc_call SEMICOLON'
    # tutaj trzeba napisać kod wywołania procedury
    # na koniec nie zapomnieć o ustawieniu currProc na None
    global currProcedure
    p[0] = p[1]
    #currProcedure = None

def p_proc_call(p):
    'proc_call : VARID LPAREN args RPAREN'
    global procedures_list, currProcedure, symbols_array, curr_line_in_code, temp_arr, temp_arr2
    code = ''
    j = None
    for i in range(len(procedures_list)):
        if procedures_list[i][0] == p[1]:
            j = i
    if j == None:
        raise Exception("Error: Calling unexisting (or not yet declared) procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    elif currProcedure == procedures_list[j][0]:
        print("wywołanie w środku ", procedures_list[j][0], " ", currProcedure)
        raise Exception("Error: Recursive call in procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
    else:
        #if line_of_call < procedures_list[j][1]:
            # ten przypadek chyba nie zajdzie, bo przed zadeklarowaniem procedury nie ma jej w procedures_list
            #raise Exception("Error: Calling procedure {} in line {} before it is declared.".format(p[1], p.lexer.lineno-1))
        #if line_of_call > procedures_list[j][1] and line_of_call < procedures_list[j][2]:
            #raise Exception("Error: Recursive call in procedure {} in line {}.".format(p[1], p.lexer.lineno-1))
        #else:
            m = None
            print("przed pętlą ", temp_arr2, " ", len(temp_arr2))
            print("all proc: ", procedures_list, " ", currProcedure)
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
                        print("jaka procedura: ", currProcedure)
                        print("all symbols: ", symbols_array, " temp arr2: ", temp_arr2)
                        raise Exception("Error: Usage of undeclared variable {} in procedure {} in line {}.".format(temp_arr2[i], currProcedure, p.lexer.lineno-1))
                    else:
                        procNumb = None
                        for n in range(len(procedures_list)):
                            if procedures_list[n][0] == currProcedure:
                                procNumb = n
                                break
                        code += loadValueToRegister('b', procedures_list[procNumb][4][i][2]) + 'LOAD b\n' + loadValueToRegister('b', procedures_list[j][4][i][2]) + 'STORE b\n'
                        curr_line_in_code += 2
                        m = None
                else: # symbol został wcześniej zadeklarowany i znajduje się w symbols_array
                    print(procedures_list[j][4], " ", i)
                    if symbols_array[m][1] == procedures_list[j][4][i][1]: # typy się zgadzają
                        #comebackAdd = curr_line_in_code
                        #code += loadValueToRegister('b', procedures_list[j][5]) + loadValueToRegister('a', curr_line_in_code) + 'STORE b\n' # ładowanie adresu powrotu
                        symbols_array[m][4] = True # dodane, ponieważ można wywołać procedurę z parametrami, które były wcześniej tylko zadeklarowane, ale nie zainicjowane
                        code += loadValueToRegister('b', procedures_list[j][4][i][2]) + loadValueToRegister('a',symbols_array[m][3]) + 'STORE b\n'
                        # dodać adres skoku do procedury
                        curr_line_in_code += 2
                        m = None
                    else: # typy się nie zgadzają
                        raise Exception("Error: Calling procedure {} with an argument ({}) of wrong type in line {}.".format(p[1], symbols_array[m][0], p.lexer.lineno-1))
            #currProcedure = p[1] - niepotrzebne, bo to tylko wywołanie procedury, komendy były już wcześniej, jakby co to można się odwołać do p[1]
            # tutaj trzeba dodać skok do miejsca, w którym zaczyna się procedura - ale p.lexer.lineno daje nam linijkę w kodzie,
            # więc trzeba jakoś inaczej znaleźć adres skoku
            # trzeba jeszcze dodać zmianę zmiennej currProcedure na p[1]???
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
            print("decl w mainie")
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
        else:
            print("decl w mainie")
    
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
            print("decl w mainie")
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
        else:
            print("decl w mainie")

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
    codeLen = 0
    j = None
    #print("p[1][0][0]: ", p[1][0][0], " ", p[1])
    for i in range(len(symbols_array)):
        #if p[1][0] == symbols_array[i][0]:
        if p[1][0][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        # w wyświetlaniu błędu jako p[1][0] pokazuje się (('nazwa zmiennej', czy_jest_liczbą),) - zmienić, żeby pokazywało tylko nazwę
        #raise Exception("Error: Assigning value to undeclared variable {} in line {}.".format(p[1][0], p.lexer.lineno-1))
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
                    print("szukam błędu: ", procedures_list[j][4][k][2])
                    code += p[3][1] + loadValuesToRegs((procedures_list[j][4][k][2],), ('b',), p.lexer.lineno-1, True) + 'GET {}\nSTORE b\n'.format(p[3][0])
                else:
                    code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, True) + loadValuesToRegs((procedures_list[j][4][k][2],), ('b',), p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
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
            print("Coś jest nie tak: ", p[3][0])
            # tutaj nie może być PUT c dodawane do kodu 'PUT c\n' + było przed załadowaniem drugiej wartości do rejestru b
            code += loadValuesToRegs((p[3],), ('c',), p.lexer.lineno-1, True) + loadValuesToRegs((p[1],), ('b',), p.lexer.lineno-1, True) + 'GET c\nSTORE b\n'
    curr_line_in_code += 2
    p[0] = code

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    global curr_line_in_code, howdeep
    code = ''
    commLen = len(p[4].split('\n'))
    print(p[2], " ", p[4], " commLen: ", commLen, " curr: ", curr_line_in_code, " ", type(p[2]))
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
        #condLen = len(p[2].split('\n'))
        #curr_line_in_code += condLen + commLen
    howdeep -= 1
    p[0] = code + p[4]

def p_if_else_statement(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    global curr_line_in_code, howdeep
    code = ''
    commLen1 = len(p[4].split('\n'))
    commLen2 = len(p[6].split('\n'))
    if isinstance(p[2], tuple):
        print("p[2]: ", p[2])
        # zastanowić się nad dodaniem dodatkowo condLen
        #code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + commLen1) + p[4] \
         #       + 'JUMP {}\n'.format(curr_line_in_code + commLen1 + commLen2) + p[6]
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen1 - commLen2) + p[2][0][2] + '{}\n'.format(curr_line_in_code + 1) \
              + 'JUMP {}\n'.format(curr_line_in_code-commLen2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + 1) + p[6]
        curr_line_in_code += 6 #commLen1 + commLen2 + 1 # 6 to długość kodu dla tego warunku
    else:
        code += p[2] + '{}\n'.format(curr_line_in_code + commLen1) + p[4] + 'JUMP {}\n'.format(curr_line_in_code + commLen1 + commLen2) + p[6]
        #curr_line_in_code += commLen1 + commLen2
        curr_line_in_code += 1
    #p[0] = p[2] + p[4] + p[6]
    howdeep -= 1
    p[0] = code

def p_while_loop(p):
    'command : WHILE condition DO commands ENDWHILE'
    global curr_line_in_code, howdeep
    code = ''
    condLen = 0
    commLen = len(p[4].split('\n'))
    print("WHILE curr ", curr_line_in_code, " commlen ", commLen)
    if isinstance(p[2], tuple):
        #code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + 3 + commLen + 1) + p[4] \
                #+ 'JUMP {}\n'.format(curr_line_in_code)
        #condLen = len(p[2][0][1].split('\n')) + len(p[2][0][2].split('\n'))
        addLen = len(p[2][0][0].split('\n'))
        print("add: ", addLen)
        condLen = 6
        code += p[2][0][0] + p[2][0][1] + '{}\n'.format(curr_line_in_code - commLen + 2) + p[2][0][2] + '{}\n'.format(curr_line_in_code + 2) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen - addLen + 3)
        #+ 'JUMP {}\n'.format(curr_line_in_code)
        #curr_line_in_code += 6 + commLen + 1
    else:
        condLen = len(p[2].split('\n'))
        print(" ", condLen)
        #code += p[2] + '{}\n'.format(curr_line_in_code + condLen + commLen) + p[4] + 'JUMP {}\n'.format(curr_line_in_code)
        code += p[2] + '{}\n'.format(curr_line_in_code + 2) + p[4] + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen + 2)
        #curr_line_in_code += condLen + commLen + 1
    curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

def p_repeat_loop(p):
    'command : REPEAT commands UNTIL condition SEMICOLON'
    global curr_line_in_code, howdeep
    code = ''
    condLen = 0
    commLen = len(p[2].split('\n'))
    print("curr line: ", curr_line_in_code)
    #if p[4] is tuple:
    if isinstance(p[4], tuple):
        condLen= len(p[4][1].split('\n')) + len(p[4][2].split('\n'))
        code += p[2] + p[4][0] + p[4][1] + '{}\n'.format(curr_line_in_code - condLen - commLen) + p[4][2] \
                + '{}\n'.format(curr_line_in_code + 1) + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen)
    else:
        condLen = len(p[4].split('\n'))
        print("cond: ", condLen, " comm: ", commLen)
        #code += p[2] + p[4] + '{}\n'.format(curr_line_in_code + 3) + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen + 3)
        code += p[2] + p[4] + '{}\n'.format(curr_line_in_code + 2) + 'JUMP {}\n'.format(curr_line_in_code - condLen - commLen + 2)
    curr_line_in_code += 1
    howdeep -= 1
    p[0] = code

### CONDITIONS ###

def p_equal(p):
    'condition : value EQUAL value'
    global curr_line_in_code, howdeep
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    code += 'GET c\nSUB d\nPUT e\nGET d\nSUB c\nADD e\nJPOS '
    curr_line_in_code += 7
    howdeep += 1
    p[0] = code
    
def p_negation(p):
    'condition : value NEG value'
    global curr_line_in_code, howdeep
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], False)
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
        #code += loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
        code += loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    else:
        #code += loadValuesToRegs([p[1], p[3]], ['d', 'b'], p.lexer.lineno-1, False)
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
        #code += loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
        code += loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    else:
        #code += loadValuesToRegs([p[1], p[3]], ['d', 'b'], p.lexer.lineno-1, False)
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
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
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
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    print("przed mnożeniem: ", currLi)
    #code += 'RST c\nGET b\nSUB d\nJPOS  \nGET b\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n \nGET d\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n'
    #code += 'RST e\nGET d\nSHR a\nSHL a\nPUT c\nGET d\nSUB c\nJZERO \nGET e\nADD b\nPUT e\nSHL b\nSHR d\nGET d\nJPOS \n'
    # pierwszy i drugi skok na koniec mnożenia, trzeci do mnożenia, bo druga liczba jest nieparzysta, czwarty i piąty do sprawdzenia,
    # czy druga liczba nie jest już równa 0
    #code += 'RST f\nGET b\nJZERO {}\nGET d\nJZERO {}\nPUT c\nSHR c\nSHL c\nSUB c\nJPOS {}\nSHL b\nSHR d\nJUMP {}\nGET f\nADD b\n\
     #   PUT f\nDEC d\nJUMP {}\nGET f'.format(currLi+17, currLi+17, currLi+14, currLi+4, currLi+4)
    code += 'RST f\nGET c\nJZERO {}\nGET d\nJZERO {}\nPUT e\nSHR e\nSHL e\nSUB e\nJPOS {}\nSHL c\nSHR d\nJUMP {}\nGET f\nADD c\n\
PUT f\nDEC d\nJUMP {}\nGET f\n'.format(currLi+19, currLi+19, currLi+14, currLi+4, currLi+4)
    curr_line_in_code += 19
    print("po mnożeniu ", curr_line_in_code)
    p[0] = ('f', code)

def p_divide(p):
    'expression : value DIVIDE value'
    global curr_line_in_code
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    #code += 'RST c\nRST f\nGET d\nPUT e\nSHL e\nGET b\nJZERO  \nSUB e\nJZERO  \nINC c\nJUMP  \nGET e\nJZERO  \nSUB b\nJZERO  \nSHL c\nGET c\nADD f\nPUT f\nRST c\
        #\nSHR e\nGET b\nSUB e\nSHL a\nPUT e\nJUMP  \n'
    #code += 'RST e\nGET d\nJZERO {}\nGET b\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB b\nJPOS {}\nINC e\nJUMP {}\nRST f\nINC f\nGET d\nPUT c\nSHL c\n\
     #   SHL f\nGET b\nSUB c\nJPOS {}\nGET c\nSUB b\nJZERO {}\nSHR f\nGET e\nADD f\nPUT e\nSHR c\nGET b\nSUB c\nPUT b\nJUMP {}\nGET e\nADD f\nPUT e\n\
      #  GET e\n'.format(currLi+37, currLi+37, currLi+13, currLi+37, currLi+37, currLi+17, currLi+34, currLi+4)
    code += 'RST f\nGET d\nJZERO {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nINC f\nJUMP {}\nRST g\nINC g\nGET d\nPUT e\nSHL e\n\
SHL g\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\nJZERO {}\nSHR g\nGET f\nADD g\nPUT f\nSHR e\nGET c\nSUB e\nPUT c\nJUMP {}\nGET f\nADD g\nPUT f\n\
GET f\n'.format(currLi+37, currLi+37, currLi+13, currLi+37, currLi+37, currLi+17, currLi+34, currLi+4)

        #INC e\nJPOS \nGET c\nSUB b\nJPOS \nINC e\nJUMP \nSHL c\nGET b\nSUB c\
        #\nJZERO \nINC e\nINC e\nJPOS\nSHR c\nGET b\nSUB c\nPUT b\nJUMP \n'
    #code += 'RST g\nGET d\nPUT e\nGET b\nPUT c\nGET b\nJZERO \nGET d\nJZERO \nGET b\nSUB e\nPUT b\nGET c\nSUB d\nADD b\nJZERO \nGET d\nSUB c\nJZERO \nJUMP \nRST g\n\
     #   JUMP \nRST g\nINC g\nJUMP \nGET d\nPUT b\nGET c\nPUT e\nRST g\nRST f\nINC f\nGET e\nJZERO \nSHR e\nSHR b\nJUMP \nGET c\nPUT e\nGET b\nJZERO \n\
      #  SHR b\nSHL e\nINC f\nJUMP \nGET d\nPUT b\nGET f\nJZERO \nINC b\n GET b\nSUB d\nPUT b\nJZERO \nDEC b\nDEC f\nSHL g\nINC g\nSHR e\nGET b\nPUT d\n\
       # JUMP \nGET d\nPUT b\nSHL g\nDEC f\nSHR e\nJUMP \nGET g\n'
    curr_line_in_code += 37
    print("po dzieleniu ", curr_line_in_code)
    p[0] = ('g', code)

def p_modulo(p):
    'expression : value MOD value'
    global curr_line_in_code
    #code = loadValuesToRegs([p[1], p[3]], ['b', 'd'], p.lexer.lineno-1, False)
    code = loadValuesToRegs([p[1], p[3]], ['c', 'd'], p.lexer.lineno-1, False)
    currLi = curr_line_in_code
    #code += 'GET d\nJZERO {}\nGET b\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB b\nJZERO {}\nGET b\nJUMP {}\nGET d\nPUT c\nSHL c\nGET b\nSUB c\nJPOS {}\nGET c\nSUB b\n\
     #   JZERO {}\nSHR c\nGET b\nSUB c\nPUT b\nSUB c\nJPOS {}\nGET b\n'.format(currLi+27, currLi+27, currLi+12, currLi+27, currLi+27, currLi+12, currLi+27, currLi+12)
    code += 'GET d\nJPOS {}\nPUT c\nJUMP {}\nGET c\nJZERO {}\nSUB d\nJPOS {}\nGET d\nSUB c\nJPOS {}\nRST c\nJUMP {}\nGET d\nPUT e\nSHL e\nGET c\nSUB e\nJPOS {}\nGET e\nSUB c\n\
JZERO {}\nSHR e\nGET c\nSUB e\nPUT c\nSUB e\nJPOS {}\n'.format(currLi + 5, currLi+29, currLi+29, currLi+14, currLi+29, currLi+29, currLi+16, currLi+29, currLi+14)
    curr_line_in_code += 29
    print("po modulo ", curr_line_in_code)
    p[0] = ('c', code)

def p_read(p):
    'command : READ identifier SEMICOLON'
    global curr_line_in_code
    code = ''
    j = None
    for i in range(len(symbols_array)):
        #if p[2][0][0] == symbols_array[i][0]:
        if p[2][0][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line {}.".format(p[2][0], p.lexer.lineno-1))
    else:
        if p[2][1]:
            # to jest tablica
            if type(p[2][2]) is int:
                #code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]+p[2][0][2]-1) + 'STORE b\n'
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
    #if p[2][0] is not tuple:
    print(p[2][0][0])
    #if not isinstance(p[2][0], tuple):
    if p[2][0][0][1]:
        # to jest liczba
        code += loadValueToRegister('a', p[2][0][0][0]) + 'WRITE\n'
    else:
        # to jest albo zmienna albo element tablicy
        #if p[2][0][1]:
        if p[2][1]:
            # to jest tablica
            #code += loadArrayToRegister(p[2][0][0], 'a', p[2][0][2], p.lexer.lineno-1, False)
            #code += loadArrayToRegister(p[2][0][0][0], 'a', p[2][0][2], p.lexer.lineno-1, False) + 'WRITE\n'
            print("index: ", p[2][0][0][0])
            code += loadArrayToRegister(p[2][0][0][0], 'a', p[2][2], p.lexer.lineno-1, False) + 'WRITE\n'
        else:
            # to jest zmienna
            #code += loadVariableToRegister(p[2][0][0], 'a', p.lexer.lineno-1, False) + 'WRITE\n'
            print("index: ", p[2][0][0][0])
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
    lexer = build_lexer()
    parser = yacc.yacc()

#try:
    compiled = parser.parse(programme, tracking=True)
    with open(sys.argv[2], "w") as file:
        file.write(compiled)
#except Exception as ex:
    #print(ex, " ")