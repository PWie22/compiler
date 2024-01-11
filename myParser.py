
from sly import Parser
from myLexer import MyLexer

class MyParser(Parser):

    ### SECTION FOR GLOBAL VARIABLES OF THE CLASS ###

    tokens = MyLexer.tokens

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
    def addSymbolToArray(self, varName, ifArray, capacity, lineNumb):
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
    def loadValueToRegister(self, regName, value):
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

    def loadVariableToRegister(self, varName, regName):
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
            # czy nie trzeba dodać czegoś jeszcze np. LOAD albo GET
            code = self.loadValueToRegister(regName, symbols_array[j][3])
        return code

    # funkcja potrzebna, żeby nie sprawdzać czym są val1 i val2 wiele razy
    # w values są trzymane dwójki (val, is_numb) - val to wartość, is_numb to wartość boolowska, jest równa true, jeżeli to jest zwykła liczba
    # shouldOrder - jeżeli zostanie ustawiona na True to znaczy, że trzeba wstawić do rejestrów w kolejności rosnącej, potrzebne przy mnożeniu,
    # ale trzeba to jakoś sprytnie zrobić
    def loadValuesToRegs(self, values, regs, shouldOrder=False):
        code = ''
        for i in range(len(values)):
            if values[i][1]:
                # to jest liczba
                code += self.loadValueToRegister(regs[i], int(values[i][0]))
            else:
                # to jest zmienna
                print()
                # może to być zwykła zmienna albo tablica
        return code

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
            p[0] = p[1] + p[7] + 'HALT'
            procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[8]].lineno
        else:
            p[0] = p[1] + p[6] + 'HALT'
            procedures_list[len(procedures_list)-1][2] = p.parser.token_slice[p.slice[7]].lineno
    
    def p_main(p):
        '''main : PROGRAM IS declarations IN commands END
                | PROGRAM IS IN commands END'''
        # tutaj trzeba sczytać wszystko z declarations, jeżeli są
        if len(p) == 6:
            print()
            # tutaj dodać funkcję dodającą nazwy zadeklarowanych zmiennych do tablicy
        else:
            print()
            # co tutaj zrobić
    
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
    
    def p_if_statement(p):
        'command : IF condition THEN commands ENDIF'
        # trzeba zapisać to, co mamy condition i commands
        p[0] = p[2] + p[4]

    def p_if_else_statement(p):
        'command : IF condition THEN commands ELSE commands ENDIF'
        # trzeba zapisać to, co mamy condition, commands i commands
        # czy nie potrzebuję tutaj adresów skoków, żeby przeskakiwać if albo else w zależności, czy warunek jest prawdziwy, czy nie
        p[0] = p[2] + p[4] + p[6]

    def p_while_loop(p):
        'command : WHILE condition DO commands ENDWHILE'
        # potrzebuję zapisać to, co jest w condition i commands, trzeba mieć adres skoku???
        p[0] = p[2] + p[4]

    def p_command_proc_call(p):
        'command : proc_call SEMICOLON'

    def p_repeat_loop(p):
        'command : REPEAT commands UNTIL condition SEMICOLON'
        # potrzebuję zapisać to, co mamay z commands i condition

    def p_read(p):
        'command : READ identifier SEMICOLON'
        code = ''
        # trzeba najprawdopodobniej zapisać wartość zmiennej do pamięci
        p[0] = code
    
    def p_write(p):
        'command : WRITE value SEMICOLON'
        code = ''
        # jeżeli to jest liczba, to trzeba ją po prostu wypisać, jeżeli zmienna, to trzeba znaleźć jej adres w pamięci i wypisać jej wartość,
        # jeżeli jest to indeks w tablicy, to mamy dwie możliwości: albo jako indeks jest liczba, albo zmienna
        p[0] = code

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
                raise Exception("Error: Calling procedure {} in line  before its declaration.".format(p[1]))
            elif line_of_call > procedures_list[j][1] and line_of_call < procedures_list[j][2]:
                raise Exception("Error: Recursive call in procedure {} in line .".format(p[1]))
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

    def p_array_declaration(p):
        '''args_decl : args_decl COMMA ARRAYSIGN VARID
                        | ARRAYSIGN VARID'''
    
    def p_var_declaration(p):
        '''args_decl : args_decl COMMA VARID
                        | VARID'''

    def p_args(p):
        '''args : args COMMA VARID
                | VARID'''
    
    ### EXPRESSIONS ###

    def p_expression_value(p):
        'expression : value'
    
    def p_add_sub(self, p):
        '''expression : value PLUS value
                        | value MINUS value'''
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        if p[2] == '+':
            # chyba zamiast PUT f powinno być zapisywanie do tablicy, czy może jednak trzymanie w rejestrach???
            code += 'GET b\nADD d\nPUT f\n'
        else:
            code += 'GET b\nSUB d\nPUT f\n'

    def p_multiply(self, p):
        'expression : value TIMES value'
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        code += 'RST c\nGET b\nSUB d\nJPOS  \nGET b\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n \nGET d\nPUT e\nSHR e\nSHL e\nGET d\nSUB e\nJPOS  \n'
        p[0] = code

    def p_divide(self, p):
        'expression : value DIVIDE value'
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        # trzeba poprawić i jeszcze dopisać adresy skoków
        # wynik jest w rejestrze f
        code += 'RST c\nRST f\nGET d\nPUT e\nSHL e\nGET b\nJZERO  \nSUB e\nJZERO  \nINC c\nJUMP  \nGET e\nJZERO  \nSUB b\nJZERO  \nSHL c\nGET c\nADD f\nPUT f\nRST c\
            \nSHR e\nGET b\nSUB e\nSHL a\nPUT e\nJUMP  \n'
        p[0] = code

    def p_modulo(self, p):
        'expression : value MOD value'
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        code += ''
        p[0] = code

    ### CONDITIONS ###

    def p_equal(self, p):
        'condition : value EQUAL value'
        # procedura działania: załadować liczby do dwóch różnych rejestrów, w innym rejestrze odjąć val1 od val2,
        # w jednym z dwóch pierwszych odjąć val2 od val1, a potem dodać do siebie dwie różnice
        # wynik będzie równy zero tylko wtedy, gdy dwie liczby są sobie równe
        # przemyśleć, czy jakiś skok nie jest potrzebny, ale chyba nie
        # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        # dodać adres ostatniego skoku tak, żeby przeskoczyło całego ifa albo pętlę
        code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJPOS'
    
    def p_negation(self, p):
        'condition : value NEG value'
        # procedura działania: załadować val1 i val2 do dwóch rejestrów, w innym rejestrze odjąć val1 od val2,
        # gdzieś indziej odjąć val2 od val1, potem dodać do siebie te dwie różnice
        # porównać je, jeżeli wynik jest różny od zera, to liczby nie są sobie równe
        # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
        code = self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        # dodać adres ostatniego skoku
        code += 'GET b\nSUB d\nPUT c\nGET d\nSUB b\nADD c\nJZERO'

    def p_greater_less(self, p):
        '''condition : value GREATER value
                        | value LESS value'''
        code = ''
        if p[2] == ">":
            # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
            code += self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        else:
            code += self.loadValuesToRegs([p[1], p[3]], ['d', 'b'])
        # muszę skoczyć, kiedy liczby są równe albo ta w rejestrze d jest większa
        code += 'GET b\nSUB d\nJZERO '
        p[0] = code

    def p_greater_less_equal(self, p):
        '''condition : value GREATEREQ value
                        | value LESSEQ value'''
        code = ''
        # te dwa rodzaje warunków są takie same, są własną odwrotnością, wystarczy wstawić wartości do rejestrów odwrotnie
        if p[2] == ">=":
            # czy tu można zamieniać na int? bo to mogą być zmienne albo elementy tablicy
            code += self.loadValuesToRegs([p[1], p[3]], ['b', 'd'])
        else:
            code += self.loadValuesToRegs([p[1], p[3]], ['d', 'b'])
        # uzupełnić adres skoku po JPOS - wartość w rejestrze b jest większa niż w d, więc warunek prawdziwy
        # dodać adres skoku po drugim JPOS - warunek nie jest prawdziwy, więc muszę przeskoczyć fragment kodu
        code += 'GET b\nSUB d\nJPOS \nGET d\nSUB b\nJPOS '
        p[0] = code

    ### REST ###

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
    
    def p_array_identifier(p):
        '''identifier : VARID SQLPAREN NUMBER SQRPAREN
                        | VARID SQLPAREN VARID SQRPAREN'''
        
    ### SYNTAX ERRORS ###

    def p_error(self, p):
        raise SyntaxError("Error: Syntax error in line {}.".format(p.parser.lineno))