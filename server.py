#!/usr/bin/python3

import sys
import socket
import select
import json
import base64
import csv
import random
from common_comm import send_dict, recv_dict, sendrecv_dict

from Crypto.Cipher import AES

# Dicionário com a informação relativa aos clientes
gamers = {'name':[],'sock_id':[]}

# return the client_id of a socket or None
def find_client_id (client_sock):
	peerName = client_sock.getpeername()
	return peerName[1]

# Função para encriptar valores a enviar em formato json com codificação base64
# return int data encrypted in a 16 bytes binary string and coded base64
def encrypt_intvalue (client_id, data):
	return None


# Função para desencriptar valores recebidos em formato json com codificação base64
# return int data decrypted from a 16 bytes binary string and coded base64
def decrypt_intvalue (client_id, data):
	return None


#
# Incomming message structure:
# { op = "START", client_id, [cipher] }
# { op = "QUIT" }
# { op = "GUESS", number }
# { op = "STOP", number, attempts }
#
# Outcomming message structure:
# { op = "START", status, max_attempts }
# { op = "QUIT" , status }
# { op = "GUESS", status, result }
# { op = "STOP", status, guess }


#
# Suporte de descodificação da operação pretendida pelo cliente
#
def new_msg (client_sock):
	request = recv_dict(client_sock)
	print(request)
	if request['op'] == "START":
		new_client(client_sock, request)
	if request['op'] == "QUIT":
		quit_client(client_sock, request)
	if request['op'] == "STOP":
		stop_client(client_sock, request)
	if request['op'] == "GUESS":
		guess_client(client_sock, request)
	#response = {'value': "jamanta"}
	#send_dict(client_sock, response)
	return None
# read the client request
# detect the operation requested by the client
# execute the operation and obtain the response (consider also operations not available)
# send the response to the client


#
# Suporte da criação de um novo jogador - operação START
#
def new_client (client_sock, request):
	name = request['client_id']
	sock_id = find_client_id(client_sock)
	if name in gamers['name']:
		response = {'op': "START", 'status': 'id already found'}
		send_dict(client_sock, response)
	else:
		gamers['name'].append(name)
		gamers['sock_id'].append(sock_id)
		print(gamers)
		response = {'op': "START", 'status': 'id added to gamers'}
		send_dict(client_sock, response)
	return None
# detect the client in the request
# verify the appropriate conditions for executing this operation
# obtain the secret number and number of attempts
# process the client in the dictionary
# return response message with results or error message


#
# Suporte da eliminação de um cliente
#
def clean_client (client_sock):
	return None
# obtain the client_id from his socket and delete from the dictionary


#
# Suporte do pedido de desistência de um cliente - operação QUIT
#
def quit_client (client_sock, request):
	response = {'op': "QUIT", 'status': 'ok'}
	send_dict(client_sock, response)
	return None
# obtain the client_id from his socket
# verify the appropriate conditions for executing this operation
# process the report file with the QUIT result
# eliminate client from dictionary
# return response message with result or error message


#
# Suporte da criação de um ficheiro csv com o respectivo cabeçalho
#
def create_file ():
	return None
# create report csv file with header


#
# Suporte da actualização de um ficheiro csv com a informação do cliente e resultado
#
def update_file (client_id, result):
	return None
# update report csv file with the result from the client


#
# Suporte da jogada de um cliente - operação GUESS
#
def guess_client (client_sock, request):

	if request['number'] == segredo:
		response = {'op': "GUESS", 'status': True, 'result':"equals"}
		send_dict(client_sock, response)
	if request['number'] > segredo:
		response = {'op': "GUESS", 'status': True, 'result':"larger"}
		send_dict(client_sock, response)
	if request['number'] < segredo:
		response = {'op': "GUESS", 'status': True, 'result':"smaller"}
		send_dict(client_sock, response)
	return None
# obtain the client_id from his socket
# verify the appropriate conditions for executing this operation
# return response message with result or error message


#
# Suporte do pedido de terminação de um cliente - operação STOP
#
def stop_client (client_sock, request):
	response = {'op': "STATUS", 'status': 'ok'}
	send_dict(client_sock, response)
	return None
# obtain the client_id from his socket
# verify the appropriate conditions for executing this operation
# process the report file with the SUCCESS/FAILURE result
# eliminate client from dictionary
# return response message with result or error message

segredo = random.randint(0, 100)
def main():
	# validate the number of arguments and eventually print error message and exit with error
	# verify type of of arguments and eventually print error message and exit with error
	if len(sys.argv) != 2:
		sys.exit("Deve passar o porto como argumento para o servidor")
	try:
		int(sys.argv[1])
	except ValueError:
		sys.exit("Porto deve ser um numero inteiro")
	if int(sys.argv[1])<0:
		sys.exit("Porto deve ser um numero inteiro positivo")

	port = int(sys.argv[1])



	server_socket = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind (("127.0.0.1", port))
	server_socket.listen (10)

	clients = []
	create_file ()

	while True:
		try:
			available = select.select ([server_socket] + clients, [], [])[0]
		except ValueError:
			# Sockets may have been closed, check for that
			for client_sock in clients:
				#if client_sock.fileno () == -1: client_sock.remove(client) # closed
				if client_sock.fileno() == -1: client_sock.remove()
			continue # Reiterate select

		for client_sock in available:
			# New client?
			if client_sock is server_socket:
				newclient, addr = server_socket.accept ()
				clients.append (newclient)
			# Or an existing client
			else:
				# See if client sent a message
				if len (client_sock.recv (1, socket.MSG_PEEK)) != 0:
					# client socket has a message
					#print ("server" + str (client_sock))
					new_msg (client_sock)
				else: # Or just disconnected
					clients.remove (client_sock)
					clean_client (client_sock)
					client_sock.close ()
					break # Reiterate select

if __name__ == "__main__":
	main()
