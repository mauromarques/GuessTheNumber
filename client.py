#!/usr/bin/python3

import os
import sys
import socket
import json
import base64
from common_comm import send_dict, recv_dict, sendrecv_dict
from Crypto.Cipher import AES

# Função para encriptar valores a enviar em formato json com codificação base64
# Cada numero inteiro comunicado entre o servidor e o cliente é encriptado por blocos usando a função AES-128 em modo ECB.
# Como a chave de cifragem é passada como argumento da função, convertemos o inteiro em uma string binaria com 128 bits e a
# codificamos no formato Base64, para que os criptogramas possam ser suportados pelo JSON.
# Por fim, este valor codificado e encriptado é retornado pela função, para que possa ser enviado.
def encrypt_intvalue (cipherkey, data):
	cipher = AES.new(cipherkey, AES.MODE_ECB)
	data2 = cipher.encrypt(bytes("%16d" % (data), 'utf8'))
	data_tosend = str(base64.b64encode(data2), 'utf8')
	return data_tosend


# Função para desencriptar valores recebidos em formato json com codificação base64
# Cada numero inteiro comunicado entre o servidor e o cliente é encriptado por blocos usando a função AES-128 em modo ECB.
# Como a chave de cifragem é passada como argumento da função, descodificamos os dados passados à função como argumento no formato
# Base64 e descriptografamos o seu conteúdo, para que enfim possa ser codificado novamente em um valor inteiro e retornado
# pela função.
def decrypt_intvalue (cipherkey, data):
	cipher = AES.new(cipherkey, AES.MODE_ECB)
	data = base64.b64decode(data)
	data = cipher.decrypt(data)
	data = int(str(data, 'utf8'))
	return data


# Esta função valida a resposta do servidor recebida pelo cliente. Para que uma resposta seja valida, consideramos que
# ela deve ser do tipo " 'op': xxxx, 'status': xxxx ", já que são campos em comum em todas as mensagens enviadas pelo servidor,
# e qualquer outro formato não é válido.
# Portanto, para validar a resposta, usamos um "try-catch" que tenta aceder aos valores de 'op' e 'status'. Caso isso
# seja possiível, ou seja, caso os campos existam na resposta, a função retorna True. Caso o acesso aos campos falhe,
# a função retorna "False"
def validate_response (client_sock, response):
	try:
		op = response['op']
		status = response['status']
		return True
	except:
		return False

	return None

# Processa a operação QUIT
# Quando o utilizador fizer o input do comando QUIT, esta função será chamada.
def quit_action (client_sock, attempts):
	request = {'op': 'QUIT'}
	response = sendrecv_dict(client_sock, request)

	if validate_response(client_sock, response):
		if response['status']:
			print("Jogo terminado com sucesso.")
		else:
			print("Impossível terminar um jogo que não foi iniciado.")
	else:
		print("Erro: resposta do servidor não é valida")
	return None

#
# Suporte da execução do cliente
#

cipherkey = os.urandom(16)
cipherkey_toSend = str(base64.b64encode(cipherkey), 'utf8')

def run_client (client_sock, client_id):

	emUso = True
	jogadas = 0
	jogMax = None
	auto=False
	nextCom = ""
	lastAttempt = None
	while emUso:

		if auto == False:
			inp = input("Comando: ")
			comando = inp.upper()
		else:
			comando=nextCom
			auto = False

		if comando == "START":

			request = {'op': 'START', 'client_id': client_id, 'cipherkey':cipherkey_toSend }
			print(cipherkey)
			print(cipherkey_toSend)
			response = sendrecv_dict(client_sock, request)

			if validate_response(client_sock, response):
				if response['status'] == False:
					print("Erro: "+response['error'])
				else:
					max = decrypt_intvalue(cipherkey, response['max_attempts'])
					message = "Jogo iniciado, tens " + str(max) + " jogadas para acertar o segredo."
					jogMax = max
					jogadas = 0
					print(message)
			else:
				print("Erro: resposta do servidor não é valida")


		if comando == "QUIT":
			quit_action(client_sock, jogadas)
			jogadas = 0
			jogMax = None


		if comando == "GUESS":
			numeroValido = False
			numeroInteiro = False
			#number_str = input("Numero para jogar: ")
			number = ""

			#verifica se o input é um inteiro
			while numeroInteiro != True or numeroValido != True:
				numeroValido = False
				numeroInteiro = False

				number_str = input("Numero para jogar: ")

				try:
					number = int(number_str)
					numeroInteiro = True
				except:
					print("Jogada deve ser um numero")
					continue

				number = int(number_str)

				if number >= 0 and number <= 100:
					numeroValido = True
				else:
					print("Numero deve estar entre 0 e 100")
					continue

			request = {'op': 'GUESS', 'number': encrypt_intvalue(cipherkey,number)}
			lastAttempt = number
			if jogadas == jogMax:
				continue
			else:
				response = sendrecv_dict(client_sock, request)
				if validate_response(client_sock, response):
					jogadas = jogadas + 1
					if response['status']:
						if response['result'] == "equals":
							print("Parabéns, acertaste o número!")
							auto = True
							nextCom = "STOP"
							continue
						elif response['result'] == "smaller":
							print("O número secreto é maior!")
						elif response['result'] == "larger":
							print("O número secreto é menor!")

						print("Max: " + str(jogMax) + " Jogadas: " + str(jogadas))
						if jogadas == jogMax:
							print("Atingiu o limite de jogadas! Comece outro jogo para tentar novamente.")
							auto = True
							nextCom = "STOP"
							continue
					else:
						print(response['error'])

				else:
					print("Erro: resposta do servidor não é valida")

		if comando == "STOP":
			request = {'op': 'STOP', 'number': encrypt_intvalue(cipherkey, number), 'attempts': encrypt_intvalue(cipherkey, jogadas)}
			response = sendrecv_dict(client_sock, request)

			if validate_response(client_sock, response):
				jogadas = 0
				jogMax = None
				exit(1)
			else:
				print("Erro: resposta do servidor não é valida")


	return None
	

def main():
	# validate the number of arguments and eventually print error message and exit with error
	# verify type of of arguments and eventually print error message and exit with error
	instead3 = False
	if len(sys.argv) != 4:
		if len(sys.argv) == 3:
			instead3 = True
		else:
			sys.exit("Deve passar como argumentos: client_id, Porto, DNS")
	try:
		int(sys.argv[2])
	except ValueError:
		sys.exit("Porto deve ser um numero inteiro")
	if int(sys.argv[2]) < 0:
		sys.exit("Porto deve ser um numero inteiro positivo")

	if instead3:
		maquina = "127.0.0.1".split(".")
	else:
		maquina = sys.argv[3].split(".")

	if len(maquina) != 4:
		sys.exit("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")
	for digito in maquina:
		try:
			int(digito)
		except ValueError:
			sys.exit("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")
		if int(digito) > 255 or int(digito) < 0:
			sys.exit("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")

	port = int(sys.argv[2])

	if instead3:
		hostname = "127.0.0.1"
	else:
		hostname = sys.argv[3]

	client_sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
	client_sock.connect ((hostname, port))

	run_client (client_sock, sys.argv[1])

	client_sock.close ()
	sys.exit (0)

if __name__ == "__main__":
    main()
