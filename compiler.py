# główny program kompilatora

import sys
from myParser import MyLexer, MyParser

if len(sys.argv) != 3:
    print("To use programme, type following command: python compiler.py <input_file> <output_file>")

