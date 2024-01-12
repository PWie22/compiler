
from compilerFunctions import *

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