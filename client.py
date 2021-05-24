#!/usr/bin/python3

import os
import sys
import socket
import json
import base64
from common_comm import send_dict, recv_dict, sendrecv_dict

from Crypto.Cipher import AES

# Função para encriptar valores a enviar em formato jsos com codificação base64
# return int data encrypted in a 16 bytes binary string coded in base64
def encrypt_intvalue (cipherkey, data):
	return None


# Função para desencriptar valores recebidos em formato json com codificação base64
# return int data decrypted from a 16 bytes binary strings coded in base64
def decrypt_intvalue (cipherkey, data):
	return None


# verify if response from server is valid or is an error message and act accordingly
def validate_response (client_sock, response):
	try:
		op = response['op']
		status = response['status']
		return True
	except:
		return False

	return None

# process QUIT operation
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


# Outcomming message structure:
# { op = "START", client_id, [cipher] }
# { op = "QUIT" }
# { op = "GUESS", number }
# { op = "STOP", number, attempts }
#
# Incomming message structure:
# { op = "START", status, max_attempts }
# { op = "QUIT" , status }
# { op = "GUESS", status, result }
# { op = "STOP", status, guess }


#
# Suporte da execução do cliente
#
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
			request = {'op': 'START', 'client_id': client_id}
			response = sendrecv_dict(client_sock, request)

			if validate_response(client_sock, response):
				if response['status'] == False:
					print("Erro: "+response['error'])
				else:
					message = "Jogo iniciado, tens " + str(response['max_attempts']) + " jogadas para acertar o segredo."
					jogMax = response['max_attempts']
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

			request = {'op': 'GUESS', 'number': number}
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
			request = {'op': 'STOP', 'number': lastAttempt, 'attempts': jogadas}
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
