
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
