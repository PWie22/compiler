
from compilerFunctions import *
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