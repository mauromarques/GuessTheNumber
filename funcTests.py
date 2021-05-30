#encode = 'utf-8'
import pytest

from subprocess import Popen
from subprocess import PIPE

# Função de teste funcional que verifica que quando são passados um número ínválido de argumentos na linha de comando
# para a execução dos programas, a mensagem de erro devolvida é a esperada.
def numArgs ():
    proc = Popen ("python3 client.py", stdout=PIPE, shell=True)
    assert proc.wait() == 1
    assert proc.stdout.read().decode('utf-8') == "Deve passar como argumentos: client_id, Porto, DNS\n"

    proc = Popen("python3 client.py mauro", stdout=PIPE, shell=True)
    assert proc.wait() == 1
    assert proc.stdout.read().decode('utf-8') == "Deve passar como argumentos: client_id, Porto, DNS\n"

    print("*- CLIENTE numero de argumentos inválido: PASSOU")

    proc = Popen("python3 server.py", stdout=PIPE, shell=True)
    assert proc.wait() == 1
    assert proc.stdout.read().decode('utf-8') == "Deve passar o porto como argumento para o servidor\n"

    proc = Popen("python3 server.py 2344 567 78", stdout=PIPE, shell=True)
    assert proc.wait() == 1
    assert proc.stdout.read().decode('utf-8') == "Deve passar o porto como argumento para o servidor\n"

    print("*- SERVIDOR numero de argumentos inválido: PASSOU")

# Função de teste funcional que verifica que quando são passados argumentos inválidos na linha de comando para a execução
# dos programas, a mensagem de erro devolvida é a esperada.
def invalidArgs ():
    proc = Popen ("python3 client.py mauro patricia labi", stdout=PIPE, shell=True)
    assert proc.wait () == 2
    assert proc.stdout.read ().decode ('utf-8') == "Porto deve ser um numero inteiro\n"

    proc = Popen ("python3 client.py mauro -5 127.0.0.1", stdout=PIPE, shell=True)
    assert proc.wait () == 2
    assert proc.stdout.read ().decode ('utf-8') == "Porto deve ser um numero inteiro positivo\n"

    proc = Popen("python3 client.py mauro 27,4 127.0.0.1", stdout=PIPE, shell=True)
    assert proc.wait() == 2
    assert proc.stdout.read().decode('utf-8') == "Porto deve ser um numero inteiro\n"

    proc = Popen("python3 client.py mauro 3456 lol", stdout=PIPE, shell=True)
    assert proc.wait() == 2
    assert proc.stdout.read().decode('utf-8') == "maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255\n"

    proc = Popen("python3 client.py mauro 3456 256.0.0.1", stdout=PIPE, shell=True)
    assert proc.wait() == 2
    assert proc.stdout.read().decode('utf-8') == "maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255\n"

    print("*- CLIENTE tipo dos argumentos invalidos: PASSOU")

    proc = Popen("python3 server.py -23", stdout=PIPE, shell=True)
    assert proc.wait() == 2
    assert proc.stdout.read().decode('utf-8') == "Porto deve ser um numero inteiro positivo\n"

    proc = Popen("python3 server.py banana", stdout=PIPE, shell=True)
    assert proc.wait() == 2
    assert proc.stdout.read().decode('utf-8') == "Porto deve ser um numero inteiro\n"

    print("*- SERVIDOR tipo dos argumentos invalidos: PASSOU")

print("----- FUNCTIONAL TESTS -----")
numArgs()
invalidArgs()