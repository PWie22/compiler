
import ply.yacc as yacc
from myLexer import build_lexer, tokens
import sys
# próba kolejnego commitu

#class MyParser(Parser):

#tokens = MyLexer.tokens

# ta tablica będzie zawierać wszystkie zadeklarowane symbole w postaci: (nazwa_symbolu, czy_tablica, pojemność_tablicy, miejsce_w_pamięci, czy_zainicjowana)
# nazwa_procedury tylko, jeżeli zmienna pochodzi z procedury; jeszcze musi być adres pamięci
symbols_array = []
# każdy element procedures_list będzie postaci (nazwa_procedury, gdzie_początek, gdzie_koniec)
procedures_list = []
first_free_mem_index = 0
# curr_line_in_code - obecna linijka w generowanym kodzie, czy to zadziała???
curr_line_in_code = 0

### SECTION FOR ALL FUNCTIONS NECESARRY FOR THE PARSER ###

# funkcja dodająca nową nazwę zmiennej do zbioru już zadeklarowanych zmiennych
def addSymbolToArray(varName, ifArray, capacity, lineNumb):
    # ta metoda nie "dokłada" kodu, jest potrzebna tylko do działania kompilatora
    global symbols_array, first_free_mem_index
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName:
            j = i
    if j != None:
        print("Error: Redeclaration of variable ", varName, " in line ", lineNumb)
    else:
        symbols_array.append([varName, ifArray, capacity, first_free_mem_index, False])
        if ifArray:
            first_free_mem_index += capacity
        else:
            first_free_mem_index += 1

    # do rejestrów nie można wpisać wartości po prostu podając liczbę, trzeba ją "wygenerować" w rejestrze
def loadValueToRegister(regName, value):
    code = ''
    while (value > 0):
        if (value % 2 == 0):
            code = 'SHL {}\n'.format(regName) + code
            value /= 2
        else:
            code = 'INC {}\n'.format(regName) + code
            value -= 1
    code = 'RESET {}\n'.format(regName) + code
    return code

# można jeszcze przekazać numer linii, w której jest błąd
def loadVariableToRegister(varName, regName):
    # najpierw trzeba znaleźć, gdzie w pamięci jest zmienna o danej nazwie i potem odczytać jej wartość
    global symbols_array
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == varName:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line .".format(varName))
    else:
        # czy trzeba rozróżniać wstawianie wartości elementów tablic do rejestrów od wstawiania zwyczajnych liczb???
        #code += self.loadValueToRegister(regName, symbols_array[j][3])
        code += loadValueToRegister('b', symbols_array[j][3]) + 'LOAD b\nPUT {}'.format(regName)
        # osobno obsłużyć przypadek, kiedy to jest tablica indeksowana zmienną - wtedy chyba trzeba najpierw odczytać
        # z pamięci zmienną, a potem element tablicy
        # przypadek, kiedy jest to element tablicy indeksowany liczbą - wtedy adres pamięci jest następujący:
        # pierwszy_indeks_zajmowany_w_pamięci_przez_tablicę + liczba_w_nawiasach - 1
    return code

# można by to zrobić wyżej, ale tablica może być indeksowana zmienną, więc wygodniej będzie zrobić osobną funkcję
# do rejestru jest wkładany tylko element tablicy; index - pozycja rządanego elementu
def loadArrayToRegister(arrName, regName, index):
    global symbols_array
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if symbols_array[i][0] == arrName:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared array {} in line .".format(arrName))
    else:
        if type(index) is int:
            # tablica indeksowana liczbą
            # sprawdzić, czy na pewno nie muszę przekonwertować index na int (int(index))
            code += loadValueToRegister('b', symbols_array[j][3]+index-1) + 'LOAD b\nPUT {}'.format(regName)
            print()
        else:
            # tablica indeksowana zmienną
            code += loadVariableToRegister(index, 'c') + loadValueToRegister('a', symbols_array[j][3]) + 'ADD c\nDEC a\nPUT b\nLOAD b\nPUT {}\n'.format(regName)
            print()
    return code

# funkcja potrzebna, żeby nie sprawdzać czym są val1 i val2 wiele razy
# w values są trzymane dwójki (val, is_numb) - val to wartość, is_numb to wartość boolowska, jest równa true, jeżeli to jest zwykła liczba
def loadValuesToRegs(values, regs):
    code = ''
    for i in range(len(values)):
        if type(values[i][1]) is tuple:
            if values[i][1][1]:
                # to jest zwykła zmienna
                code += loadVariableToRegister(regs[i], values[i][0])
            else:
                # to jest element tablicy
                code += loadArrayToRegister(values[i][1][0], regs[i], values[i][1][2])
        else:
            # to jest zwykła liczba
            code += loadValueToRegister(regs[i], int(values[i][0]))
    return code

    ### MAIN PART OF THE PARSER ###

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
        
def p_program(p):
    '''program : procedures main'''
    # czy nie powinno być jeszcze samego maina, bo co, jeżeli nie ma żadnych procedur?
    # co tutaj zrobić, czy tego nie usunąć???
    # co się dzieje, jeżeli nie ma żadnych procedur
    if not p[1]:
        p[0] = p[2]
    else:
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

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END
                    |'''
    global procedures_list
    # upewnić się, czy te numery linijek są na pewno dobrze dobrane - czy jest możliwe, żeby przed wstawieniem końca lin
    if (len(p) == 1):
        print("okej")
    elif (len(p) == 9):
        #p[0] = p[1] + p[7] + 'HALT'
        #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[8]].lineno
        procedures_list.append(p[3][0], p[3][1], p.parser.token_slice[p.slice[8]].lineno)
        # chyba jeszcze gdzieś na początku musi być jakiś jump do linijki, w której zaczyna się program
        p[0] = p[7]
    else:
        #p[0] = p[1] + p[6] + 'HALT'
        #procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[7]].lineno
        procedures_list.append(p[3][0], p[3][1], p.parser.token_slice[p.slice[7]].lineno)
        p[0] = p[6]

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
        raise Exception("Error: Calling unexisting procedure {} in line .".format(p[1]))
    else:
        line_of_call = p.lineno
        if line_of_call < procedures_list[j][1]:
            # ten przypadek chyba nie zajdzie, bo przed zadeklarowaniem procedury nie ma jej w procedures_list
            raise Exception("Error: Calling procedure {} in line  before it is declared.".format(p[1]))
        elif line_of_call > procedures_list[j][1] and line_of_call < procedures_list[j][2]:
            raise Exception("Error: Recursive call of procedure {} in line .".format(p[1]))
        else:
            print()
            # tutaj trzeba dodać skok do miejsca, w którym zaczyna się procedura - ale p.lineno daje nam linijkę w kodzie,
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
    line = p.lineno # numer linii, w której jest dopasowany tekst
    if len(p) == 7:
        addSymbolToArray(p[3], True, int(p[5]), line)
    else:
        addSymbolToArray(p[1], True, int(p[3]), line)
    
def p_var_use(p):
    '''declarations : declarations COMMA VARID
                    | VARID'''
    line = p.lineno
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
    # tutaj jest inicjowanie zmiennych, trzeba wywołać funkcję, która zapisuje wartości zmiennych do tablicy
    global symbols_array
    code = ''
    j = None
    for i in range(len(symbols_array)):
        if p[1][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Assigning value to undeclared variable {} in line .".format(p[1][0]))
    else:
        # jak przypisuję wartość do zmiennej, to muszę ją zapisać w pamięci???
        # muszę znaleźć adres zajmowany w pamięci przez zmienną, potem wziąć kod wygenerowany przez expression, a na koniec dodać STORE [adres w pamięci]
        #code += loadValueToRegister('b', symbols_array[j][3]) + str(p[3][0]) + 'STORE b\n'
        code += loadValueToRegister('b', symbols_array[j][3]) + loadValueToRegister('a', p[3][0]) + 'STORE b\n'
        print(symbols_array)
        p[0] = code

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    global curr_line_in_code
    code = ''
    # trzeba zapisać to, co mamy condition i commands
    commLen = len(p[4].split('\n'))
    if p[2] is tuple:
        # w warunku występuje >= lub <= - są tam dwa skoki zamiast jednego, dlatego ten przypadek osobno
        code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + commLen)
        curr_line_in_code += 6 + commLen # 6 to długość kodu dla tego warunku
    else:
        # w warunku nie ma >= ani <=
        code += p[2] + '{}\n'.format(curr_line_in_code + commLen)
        condLen = len(p[2].split('\n'))
        curr_line_in_code += condLen + commLen
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
    #p[0] = p[2] + p[4] + p[6]
    p[0] = code

def p_while_loop(p):
    'command : WHILE condition DO commands ENDWHILE'
    global curr_line_in_code
    code = ''
    commLen = len(p[4].split('\n'))
    # potrzebuję zapisać to, co jest w condition i commands, trzeba mieć adres skoku???
    if p[2] is tuple:
        code += p[2][0] + p[2][1] + '{}\n'.format(curr_line_in_code + 3) + p[2][2] + '{}\n'.format(curr_line_in_code + 3 + commLen + 1) + p[4] \
                + 'JUMP {}\n'.format(curr_line_in_code)
        curr_line_in_code += 6 + commLen + 1
    else:
        condLen = len(p[2].split('\n'))
        code += p[2] + '{}\n'.format(curr_line_in_code + condLen + commLen) + p[4] + 'JUMP {}\n'.format(curr_line_in_code)
        curr_line_in_code += condLen + commLen + 1
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
    # procedura działania: załadować liczby do dwóch różnych rejestrów, w innym rejestrze odjąć val1 od val2,
    # w jednym z dwóch pierwszych odjąć val2 od val1, a potem dodać do siebie dwie różnice
    # wynik będzie równy zero tylko wtedy, gdy dwie liczby są sobie równe
    # przemyśleć, czy jakiś skok nie jest potrzebny, ale chyba nie
    # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    # dodać adres ostatniego skoku tak, żeby przeskoczyło całego ifa albo pętlę
    code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJPOS '
    p[0] = code
    
def p_negation(p):
    'condition : value NEG value'
    # procedura działania: załadować val1 i val2 do dwóch rejestrów, w innym rejestrze odjąć val1 od val2,
    # gdzieś indziej odjąć val2 od val1, potem dodać do siebie te dwie różnice
    # porównać je, jeżeli wynik jest różny od zera, to liczby nie są sobie równe
    # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
    code = loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    # dodać adres ostatniego skoku
    code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJZERO '
    p[0] = code

def p_greater_less(p):
    '''condition : value GREATER value
                    | value LESS value'''
    code = ''
    if p[2] == ">":
        # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
        code += loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'b'])
    # muszę skoczyć, kiedy liczby są równe albo ta w rejestrze d jest większa
    code += 'GET b\nSUB d\nJZERO '
    p[0] = code

def p_greater_less_equal(p):
    '''condition : value GREATEREQ value
                    | value LESSEQ value'''
    code = ''
    # te dwa rodzaje warunków są takie same, są własną odwrotnością, wystarczy wstawić wartości do rejestrów odwrotnie
    if p[2] == ">=":
        # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
        code += loadValuesToRegs([p[1], p[3]], ['b', 'd'])
    else:
        code += loadValuesToRegs([p[1], p[3]], ['d', 'b'])
    # uzupełnić adres skoku po JPOS - wartość w rejestrze b jest większa niż w d, więc warunek prawdziwy
    # dodać adres skoku po drugim JPOS - warunek nie jest prawdziwy, więc muszę przeskoczyć fragment kodu
    #code += 'GET b\nSUB d\nJPOS \nGET d\nSUB b\nJPOS '
    p[0] = (code, 'GET b\nSUB d\nJPOS ', '\nGET d\nSUB b\nJPOS ')

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
    p[0] = code

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

def p_read(p):
    'command : READ identifier SEMICOLON'
    code = ''
    # trzeba najprawdopodobniej zapisać wartość zmiennej do pamięci
    j = None
    for i in range(len(symbols_array)):
        if p[2][0][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Usage of undeclared variable {} in line .".format(p[2][0]))
    else:
        # po odczytaniu trzeba wstawić do pamięci, ale do tego trzeba odczytać, w którym miejscu pamięci ma byc wstawiona dana zmienna
        # trzeba też oznaczyć odpowiednią zmienną jako zainicjowaną
        # po odczytaniu wartość znajduje się w rejestrze a, teraz muszę wstawić do innego rejestru adres, pod który wstawię tą wartość
        # na końcu użyć LOAD
        if p[2][0][1]:
            # to jest tablica
            if type(p[2][0][2]) is int:
                code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]+p[2][0][2]-1) + 'STORE b\n'
            else:
                code += loadVariableToRegister(p[2][0][2], 'a') + loadValueToRegister('b', symbols_array[j][3]) + 'ADD b\nDEC a\nPUT b\nREAD\nSTORE b\n'
        else:
            # to jest zmienna
            code += 'READ\n' + loadValueToRegister('b', symbols_array[j][3]) + 'STORE b\n'
        # zmienna jest zainicjowana, więc ustawiam wartość na True
        symbols_array[j][4] = True
    p[0] = code

def p_write(p):
    'command : WRITE value SEMICOLON'
    code = ''
    # jeżeli to jest liczba, to trzeba ją po prostu wypisać, jeżeli zmienna, to trzeba znaleźć jej adres w pamięci i wypisać jej wartość,
    # jeżeli jest to indeks w tablicy, to mamy dwie możliwości: albo jako indeks jest liczba, albo zmienna
    # żeby wypisać wartość to musi się ona znaleźć w rejestrze a, bo tylko wtedy zadziała WRITE z komend assemblerowych
    if p[2][1]:
        # to jest liczba
        code += loadValueToRegister('a', p[2]) + 'WRITE\n'
    else:
        # to jest albo zmienna albo element tablicy
        if p[2][0][1]:
            # to jest tablica
            code += loadArrayToRegister(p[2][0][0], 'a', p[2][0][2])
        else:
            # to jest zmienna
            code += loadVariableToRegister(p[2], 'a') + 'WRITE\n'
    p[0] = code

def p_value_numb(p):
    'value : NUMBER'
    # czy nie trzeba zamienić elementów tablicy p na int
    p[0] = (p[1], True)
    
def p_value_id(p):
    'value : identifier'
    # czy nie trzeba zamienić elementów tablicy p na int
    p[0] = (p[1], False)

def p_identifier(p):
    'identifier : VARID'
    # w nawiasie podana jest najpierw nazwa zmiennej, a potem, czy jest tablicą
    p[0] = (p[1], False)
    
def p_array_identifier(p):
    '''identifier : VARID SQLPAREN NUMBER SQRPAREN
                    | VARID SQLPAREN VARID SQRPAREN'''
    p[0] = (p[1], True, p[3])

### SYNTAX ERRORS ###

def p_error(p):
    raise SyntaxError("Error: Syntax error {} in line {}.".format(p, p.lexer.lineno))

programme = ''
compiled = ''

with open(sys.argv[1], "r") as f:
    programme = f.read()
    #compiled = parser.parse(lexer.tokenize(programme))
    lexer = build_lexer()
    parser = yacc.yacc()

try:
    compiled = parser.parse(programme, tracking=True)
    #print(compiled)
    with open(sys.argv[2], "w") as file:
        file.write(compiled)
except Exception as ex:
    print(ex, " ")