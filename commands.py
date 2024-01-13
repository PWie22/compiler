
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
    j = None
    for i in range(len(symbols_array)):
        if p[1][0] == symbols_array[i][0]:
            j = i
    if j == None:
        raise Exception("Error: Assigning value to undeclared variable {} in line .".format(p[1][0]))
    else:
        # jak przypisuję wartość do zmiennej, to muszę ją zapisać w pamięci???
        print()

def p_if_statement(p):
    'command : IF condition THEN commands ENDIF'
    # trzeba zapisać to, co mamy condition i commands
    commLen = len(p[4].split('\n'))
    if p[2] is tuple:
        # w warunku występuje >= lub <= - są tam dwa skoki zamiast jednego, dlatego ten przypadek osobno
        print()
    else:
        # w warunku nie ma >= ani <=
        print()
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
    # tutaj trzeba napisać kod wywołania procedury

def p_repeat_loop(p):
    'command : REPEAT commands UNTIL condition SEMICOLON'
    # potrzebuję zapisać to, co mamay z commands i condition
    p[0] = p[2] + p[4]