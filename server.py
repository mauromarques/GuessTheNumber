#!/usr/bin/python3

import sys
import socket
import select
import json
import base64
import csv
import random
from os import path
from common_comm import send_dict, recv_dict, sendrecv_dict

from Crypto.Cipher import AES

# Dicionário com a informação relativa aos clientes
gamers = {'name':[],'sock_id':[], 'segredo':[], 'max':[], 'jogadas':[], 'resultado':[], 'cipherkey':[]}
header = ['name','sock_id','segredo','max', 'jogadas', 'resultado']

# return the client_id of a socket or None
def find_client_id (client_sock):
	peerName = client_sock.getpeername()
	return peerName[1]

# Função para encriptar valores a enviar em formato json com codificação base64
# return int data encrypted in a 16 bytes binary string and coded base64

#def encrypt_intvalue (client_id, data):
#	cipher = AES.new(cipherkey, AES.MODE_ECB)
#	data2 = cipher.encrypt(bytes("%16d" % (data), 'utf8'))
#	data_tosend = str(base64.b64encode(data2), 'utf8')
#	return data_tosend


# Função para desencriptar valores recebidos em formato json com codificação base64
# return int data decrypted from a 16 bytes binary string and coded base64
def decrypt_intvalue (client_id, data):
	for i in range(0, len(gamers['sock_id'])):
		if gamers['sock_id'][i] == client_id:
			cipherkey = gamers['cipherkey'][i]

	cipher = AES.new(cipherkey, AES.MODE_ECB)
	data1 = base64.b64decode(data)
	data2 = cipher.decrypt(data1)
	print(data2)
	data3 = int(str(data2, 'utf8'))
	return data3


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

def numberToCompare(client_sock):
	id = find_client_id(client_sock)
	for i in range(0, len(gamers['sock_id'])):
		if gamers['sock_id'][i] == id:
			return gamers['segredo'][i]

#
# Suporte da criação de um novo jogador - operação START
#
def new_client (client_sock, request):
	name = request['client_id']
	sock_id = find_client_id(client_sock)
	if name in gamers['name']:
		response = {'op': "START", 'status': False, 'error': "Cliente existente"}
		send_dict(client_sock, response)
	else:
		gamers['name'].append(name)
		gamers['sock_id'].append(sock_id)
		n = random.randint(1, 2)
		secret = random.randint(0, 100)
		gamers['segredo'].append(secret)
		gamers['max'].append(n)
		gamers['jogadas'].append(0)
		gamers['cipherkey'].append(base64.b64decode(request['cipherkey']))
		print(gamers)
		response = {'op': "START", 'status': True, 'max_attempts': n}
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
	id = find_client_id(client_sock)
	print("numero de gamers: " + str(len(gamers['sock_id'])))
	for i in range(0, len(gamers['sock_id'])):
		print("index: "+str(i))
		if gamers['sock_id'][i] == id:
			gamers['segredo'].pop(i)
			gamers['sock_id'].pop(i)
			gamers['name'].pop(i)
			gamers['max'].pop(i)
			gamers['jogadas'].pop(i)
			gamers['cipherkey'].pop(i)
			return True
	return False
# obtain the client_id from his socket and delete from the dictionary


#
# Suporte do pedido de desistência de um cliente - operação QUIT
#
def quit_client (client_sock, request):
	if find_client_id(client_sock) in gamers['sock_id']:
		response = {'op': "QUIT", 'status': True}
		send_dict(client_sock, response)
		update_file(find_client_id(client_sock), 'DESISTENCIA')
		clean_client(client_sock)
	else:
		response = {'op': "QUIT", 'status': False, 'error': "cliente inexistente"}
		send_dict(client_sock, response)
	print("CURRENT GAMERS: "+str(gamers))
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
	if path.exists('report.csv') == False:
		with open('report.csv', 'w') as fileCSV:
			writer = csv.DictWriter(fileCSV, fieldnames=header)
			writer.writeheader()
	return None
# create report csv file with header


#
# Suporte da actualização de um ficheiro csv com a informação do cliente e resultado
#
def update_file (client_id, result):
	with open('report.csv', 'a') as fileCSV:
		writer = csv.DictWriter(fileCSV, fieldnames=header)
		for i in range(0, len(gamers['sock_id'])):

			if client_id == gamers['sock_id'][i]:

				di = {'name': gamers['name'][i], 'sock_id': gamers['sock_id'][i], 'segredo': gamers['segredo'][i], 'max': gamers['max'][i],'jogadas': gamers['jogadas'][i], 'resultado': result}
		writer.writerow(di)
	return None
# update report csv file with the result from the client


#
# Suporte da jogada de um cliente - operação GUESS
#
def guess_client (client_sock, request):

	if find_client_id(client_sock) in gamers['sock_id']:
		segredo = numberToCompare(client_sock)
		jogado = decrypt_intvalue(find_client_id(client_sock),request['number'])

		if jogado == segredo:
			response = {'op': "GUESS", 'status': True, 'result':"equals"}
			send_dict(client_sock, response)
		if jogado > segredo:
			response = {'op': "GUESS", 'status': True, 'result':"larger"}
			send_dict(client_sock, response)
		if jogado < segredo:
			response = {'op': "GUESS", 'status': True, 'result':"smaller"}
			send_dict(client_sock, response)
		for i in range(0, len(gamers['sock_id'])):
			if find_client_id(client_sock) == gamers['sock_id'][i]:
				gamers['jogadas'][i] = gamers['jogadas'][i] + 1
	else:
		response = {'op': "GUESS", 'status': False, 'error': "Client inexistente"}
		send_dict(client_sock, response)

	return None
# obtain the client_id from his socket
# verify the appropriate conditions for executing this operation
# return response message with result or error message


#
# Suporte do pedido de terminação de um cliente - operação STOP
#
def stop_client (client_sock, request):
	if find_client_id(client_sock) in gamers['sock_id']:
		response = {'op': "STOP", 'status': True}
		send_dict(client_sock, response)
		for i in range(0, len(gamers['sock_id'])):
			if find_client_id(client_sock) == gamers['sock_id'][i]:
				gamers['jogadas'][i] = request['attempts']
				if gamers['segredo'][i] == request['number']:
					update_file(find_client_id(client_sock), "SUCCESS")
				else:
					update_file(find_client_id(client_sock), "FAILURE")
		clean_client(client_sock)

	else:
		response = {'op': "STOP", 'status': False, 'error': "cliente inexistente"}
		send_dict(client_sock, response)
	print("CURRENT GAMERS: " + str(gamers))
	return None
# obtain the client_id from his socket
# verify the appropriate conditions for executing this operation
# process the report file with the SUCCESS/FAILURE result
# eliminate client from dictionary
# return response message with result or error message

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
