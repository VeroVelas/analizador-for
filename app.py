from flask import Flask, request, render_template_string
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# Palabras reservadas y tokens
reservadas = {
    'for': 'FOR',
    'system.out.println': 'IMPRIMIR',
    'int': 'INT'
}

tokens = (
    'PARENIZQ', 'PARENDER', 'PUNTOYCOMA', 'LLAVEIZQ', 'LLAVEDER',
    'IGUAL', 'NUMERO', 'MENORIGUAL', 'INCREMENTO', 'ID'
) + tuple(reservadas.values())

# Definición de tokens
t_PARENIZQ    = r'\('
t_PARENDER    = r'\)'
t_PUNTOYCOMA  = r';'
t_LLAVEIZQ    = r'\{'
t_LLAVEDER    = r'\}'
t_IGUAL       = r'='
t_MENORIGUAL  = r'<='
t_INCREMENTO  = r'\+\+'

# Definición de identificadores y números
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9\.]*'
    t.type = reservadas.get(t.value.lower(), 'ID')
    return t

def t_NUMERO(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Ignorar espacios y tabulaciones
t_ignore = ' \t'

# Manejo de errores léxicos
def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Construcción del lexer
analizadorLexico = lex.lex()

# --- Análisis Sintáctico ---
# Precedencia y asociatividad de operadores
precedencia = ()

# Almacén de variables declaradas
variables = set()
errores = []

# Definición de la gramática
def p_programa(p):
    '''programa : lista_declaraciones'''
    p[0] = p[1]

def p_lista_declaraciones(p):
    '''lista_declaraciones : lista_declaraciones declaracion
                           | declaracion'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_declaracion(p):
    '''declaracion : declaracion_variable
                   | sentencia'''
    p[0] = p[1]

def p_declaracion_variable(p):
    '''declaracion_variable : INT ID PUNTOYCOMA'''
    if p[2] in variables:
        errores.append(f"Error: Variable '{p[2]}' redeclarada.")
    else:
        variables.add(p[2])
    p[0] = f"{p[1]} {p[2]};"

def p_sentencia(p):
    '''sentencia : sentencia_for
                 | sentencia_imprimir
                 | sentencia_expresion'''
    p[0] = p[1]

def p_sentencia_for(p):
    '''sentencia_for : FOR PARENIZQ inicializacion PUNTOYCOMA condicion PUNTOYCOMA incremento PARENDER LLAVEIZQ lista_sentencias LLAVEDER'''
    if p[3][0] != 'asignar' or p[3][1] not in variables:
        errores.append(f"Error: Variable '{p[3][1]}' no declarada.")
    p[0] = f"{p[1]}({p[3]}; {p[5]}; {p[7]}) {{\n{p[10]}\n}}"

def p_inicializacion(p):
    '''inicializacion : ID IGUAL NUMERO'''
    p[0] = ('asignar', p[1], p[3])

def p_condicion(p):
    '''condicion : ID MENORIGUAL NUMERO'''
    p[0] = f"{p[1]} <= {p[3]}"

def p_incremento(p):
    '''incremento : ID INCREMENTO'''
    p[0] = f"{p[1]}++"

def p_lista_sentencias(p):
    '''lista_sentencias : lista_sentencias sentencia
                        | sentencia'''
    if len(p) == 3:
        p[0] = p[1] + "\n" + p[2]
    else:
        p[0] = p[1]

def p_sentencia_imprimir(p):
    '''sentencia_imprimir : IMPRIMIR PARENIZQ expresion PARENDER PUNTOYCOMA'''
    p[0] = f"{p[1]}({p[3]});"

def p_sentencia_expresion(p):
    '''sentencia_expresion : expresion PUNTOYCOMA'''
    p[0] = f"{p[1]};"

def p_expresion(p):
    '''expresion : ID'''
    if p[1] not in variables:
        errores.append(f"Error: Variable '{p[1]}' no declarada.")
    p[0] = p[1]

# Manejo de errores sintácticos
def p_error(p):
    if p:
        print(f"Error de sintaxis en '{p.value}'")
        errores.append(f"Error de sintaxis en '{p.value}'")
    else:
        print("Error de sintaxis en EOF")
        errores.append("Error de sintaxis en EOF")

# Construcción del parser
analizadorSintactico = yacc.yacc()

# --- Aplicación Flask ---
@app.route('/', methods=['GET', 'POST'])
def index():
    global errores
    global variables
    errores = []
    variables = set()
    resultado = ""
    conteoTokens = {
        'ID': 0, 'PR': 0, 'NUMEROS': 0, 'SIMBOLOS': 0, 'ERRORES': 0, 'TOTAL': 0
    }
    if request.method == 'POST':
        codigo = request.form['codigo']
        analizadorLexico.input(codigo)
        listaTokens = []
        while True:
            tok = analizadorLexico.token()
            if not tok:
                break
            listaTokens.append(str(tok))
            if tok.type in conteoTokens:
                conteoTokens[tok.type] += 1
            elif tok.type in reservadas.values():
                conteoTokens['PR'] += 1
            else:
                conteoTokens['SIMBOLOS'] += 1

        try:
            analizadorSintactico.parse(codigo)
            if errores:
                resultado = "\n".join(errores)
                conteoTokens['ERRORES'] = len(errores)
            else:
                resultado = "Compilación exitosa:\n" + "\n".join(listaTokens)
        except SyntaxError as e:
            resultado = str(e)
            conteoTokens['ERRORES'] += 1
        except Exception as e:
            resultado = "Ocurrió un error inesperado: " + str(e)
            conteoTokens['ERRORES'] += 1

        conteoTokens['TOTAL'] = sum(conteoTokens.values())

    return render_template_string('''
        <!doctype html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analizador Léxico, Sintáctico y Semántico</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: #fff;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    text-align: center;
                    color: #444;
                }
                textarea {
                    width: 100%;
                    height: 200px;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    resize: none;
                    margin-bottom: 10px;
                    font-family: monospace;
                }
                input[type="submit"] {
                    display: block;
                    width: 100%;
                    padding: 10px;
                    border: none;
                    background-color: #007bff;
                    color: #fff;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-bottom: 20px;
                }
                input[type="submit"]:hover {
                    background-color: #0056b3;
                }
                pre {
                    background-color: #f4f4f4;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th, td {
                    padding: 10px;
                    text-align: center;
                }
                th {
                    background-color: #007bff;
                    color: #fff;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Analizador Léxico, Sintáctico y Semántico</h1>
                <form method="post">
                    <textarea name="codigo" rows="10" placeholder="Introduce tu código aquí...">{{ request.form['codigo'] }}</textarea><br>
                    <input type="submit" value="Compilar">
                </form>
                {% if resultado %}
                    <h2>Resultado:</h2>
                    <pre>{{ resultado }}</pre>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>PR</th>
                                <th>Números</th>
                                <th>Símbolos</th>
                                <th>Errores</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{{ conteoTokens['ID'] }}</td>
                                <td>{{ conteoTokens['PR'] }}</td>
                                <td>{{ conteoTokens['NUMEROS'] }}</td>
                                <td>{{ conteoTokens['SIMBOLOS'] }}</td>
                                <td>{{ conteoTokens['ERRORES'] }}</td>
                                <td>{{ conteoTokens['TOTAL'] }}</td>
                            </tr>
                        </tbody>
                    </table>
                {% endif %}
            </div>
        </body>
        </html>
    ''', resultado=resultado, conteoTokens=conteoTokens)

if __name__ == '__main__':
    app.run(debug=True)
