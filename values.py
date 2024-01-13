
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