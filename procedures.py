
from compilerFunctions import procedures_list

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                    | procedures PROCEDURE proc_head IS IN commands END'''
    global procedures_list
    # upewnić się, czy te numery linijek są na pewno dobrze dobrane - czy jest możliwe, żeby przed wstawieniem końca lin
    if (len(p) == 9):
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

# jedyna komenda, która nie jest w pliku commands.py
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