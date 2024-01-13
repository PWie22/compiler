
from compilerFunctions import *

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
        code += loadValueToRegister('b', p[j][3]) + p[3] + 'STORE b\n'
        print()

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