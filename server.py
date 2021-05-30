#!/usr/bin/python3

import sys
import socket
import select
import base64
import csv
import random
from os import path
from common_comm import send_dict, recv_dict

from Crypto.Cipher import AES

# O dicionário "gamers" armazena os dados do jogadores que estão atualmente com um jogo iniciado em seus respetivos
# clientes. A informação é armazenada baseada na ordem em que cada cliente conecta-se ao servidor dentro de arrays para
# cada campo de informação que será armazenado. Por exemplo, se dois jogadores, Mauro e Patrícia, estiverem a jogar ao
# mesmo tempo, e se Mauro se conectou primeiro, seu ID pode ser consultado apartir de: gamers['sock_id'][0]; enquanto
# que o ID de Patrícia pode ser consultado a partir de: gamers['sock_id'][1].
gamers = {'name':[],'sock_id':[], 'segredo':[], 'max':[], 'jogadas':[], 'resultado':[], 'cipherkey':[]}

# Array utilizado para inicializar o header do ficheiro .CSV que será gerado pelo servidor.
header = ['name','sock_id','segredo','max', 'jogadas', 'resultado']

# A partir de cada socket de cliente, é possível extrair algumas informações únicas para o identificar. Neste caso, a
# função .getpeername() retorna um tuplo que contém o endereço do host e o porto ao qual o cliente está conectado.
# O porto então é retornado pela função find_client_id().
def find_client_id (client_sock):
	peerName = client_sock.getpeername()
	return peerName[1]

# Função para encriptar valores a enviar em formato json com codificação base64
# Cada numero inteiro comunicado entre o servidor e o cliente é encriptado por blocos usando a função AES-128 em modo ECB.
# Primeiro identificamos a chave de cifragem relativa ao cliente atual comparando o id passado como argumento da função com
# os IDs no dicionário "gamers".
# Após identificada a chave de cifra correspondente, convertemos o inteiro em uma string binaria com 128 bits e a
# codificamos no formato Base64, para que os criptogramas possam ser suportados pelo JSON.
# Por fim, este valor codificado e encriptado é retornado pela função, para que possa ser enviado.
def encrypt_intvalue (client_id, data):
	for i in range(0, len(gamers['sock_id'])):
		if gamers['sock_id'][i] == client_id:
			cipherkey = gamers['cipherkey'][i]

	cipher = AES.new(cipherkey, AES.MODE_ECB)
	data2 = cipher.encrypt(bytes("%16d" % (data), 'utf8'))
	data_tosend = str(base64.b64encode(data2), 'utf8')
	return data_tosend


# Função para desencriptar valores recebidos em formato json com codificação base64
# Cada numero inteiro comunicado entre o servidor e o cliente é encriptado por blocos usando a função AES-128 em modo ECB.
# Primeiro identificamos a chave de cifragem relativa ao cliente atual comparando o id passado como argumento da função com
# os IDs no dicionário "gamers".
# Após identificada a chave de cifra correspondente, descodificamos os dados passados à função como argumento no formato
# Base64 e descriptografamos o seu conteúdo, para que enfim possa ser codificado novamente em um valor inteiro e retornado
# pela função.
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

# Suporte de descodificação da operação pretendida pelo cliente
# Esta função é chamada sempre que o servidor recebe uma nova mensagem de um cliente, sua tarefa é identificar a função
# requisitada pelo cliente e direcioná-la para a sua respetiva função que irá processar responder ao request.
# Caso seja feito um request de uma função fora do escopo da aplicação, o servidor não faz nada.
def new_msg (client_sock):
	request = recv_dict(client_sock)
	print(request)
	if request['op'] == "START":
		new_client(client_sock, request)
	if request['op'] == "QUIT":
		quit_client(client_sock)
	if request['op'] == "STOP":
		stop_client(client_sock, request)
	if request['op'] == "GUESS":
		guess_client(client_sock, request)
	return None

# Esta função suporta o comando "GUESS", retornando o numero secreto associado ao cliente para que seja comparado.
def numberToCompare(client_sock):
	id = find_client_id(client_sock)
	for i in range(0, len(gamers['sock_id'])):
		if gamers['sock_id'][i] == id:
			return gamers['segredo'][i]

# Suporte da criação de um novo jogador - operação START
# o "client_id" passado para o servidor (inicialmente inserido pelo utilizador na linha de comando ao executar o cliente)
# é armazenado na variável "name".
# A partir do socket do cliente, identificamos seu ID (porto ao qual está conectado) com a função "find_client_id".
# Caso "name" ("client_id" enviado pelo request do cliente) já esteja presente no dicionário "gamers", o servidor irá
# comunicar isso ao cliente com uma mensagem de status: False, e uma mensagem de erro indicando que este nome já está
# a ser utilizado.
# Caso contrário, a função adiciona todos os dados necessários do cliente para iniciar um jogo aos arrays do dicionário,
# adicionando valores iniciais para todos eles (com exceção do "result", que será atribuído apenas ao fim de um jogo),
# para que a ordem seja mantida e possamos indentificar os dados de cada cliente a jogar atraves dos índices.
# Ao fim, o servidor envia uma resposa ao cliente com status: True e o valor encriptado de jogadas màximas que o cliente
# pode fazer.
def new_client (client_sock, request):
	name = request['client_id']
	sock_id = find_client_id(client_sock)
	if name in gamers['name']:
		response = {'op': "START", 'status': False, 'error': "Cliente existente"}
		send_dict(client_sock, response)
	else:
		gamers['name'].append(name)
		gamers['sock_id'].append(sock_id)
		n = random.randint(10, 30)
		secret = random.randint(0, 100)
		gamers['segredo'].append(secret)
		gamers['max'].append(n)
		gamers['jogadas'].append(0)
		gamers['cipherkey'].append(base64.b64decode(request['cipherkey']))
		print(gamers)
		response = {'op': "START", 'status': True, 'max_attempts': encrypt_intvalue(sock_id,n)}
		send_dict(client_sock, response)
	return None

# Suporte da eliminação de um cliente
# Esta função é executada sempre que for necessário excluir um cliente do dicionario "gamers", ou seja, quando o cliente
# se desconectar do servidor, quando terminar um jogo, ou quando desistir.
# A função busca pelo cliente no dicionário "gamers" e caso o encontre, exclui todos os dados relativos a ele através
# do seu índice respetivo.
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

# Suporte do pedido de desistência de um cliente - operação QUIT
# A função vai primeiro checar se o cliente que está a desistir do jogo está realmente a jogar. Para fazer isso, verifica
# se o ID do socket está presente no dicionario "gamers".
# Caso esteja, manda uma mensagem ao cliente com status: True, atualiza o ficheiro .CSV (recorrendo à função update_file())
# com o resultado do jogo sendo "DESISTENCIA", indicando que a partida foi terminada antes do jogador acertar o número,
# ou antes de atingir o limite de jogadas. Por fim, retira o cliente da sua lista de jogadores ativos recorrendo à função
# clean_client().
# Caso contrário, manda uma mensagem ao cliente com status: False, e uma mensagem de erro que explicita o fato do cliente
# não ter sido encontrado dentre os jogadores ativos.
def quit_client (client_sock):
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

# Suporte da criação de um ficheiro csv com o respectivo cabeçalho
# Esta função é chamada quando o servidor é inicializado e cria um novo ficheiro .CSV chamado "report" caso ele não
# exista no diretório em que o server.py se encontra (Para que assim o servidor não reinicie o ficheiro toda vez que for
# inicializado).
# Após criação, escreve o Header do ficheiro, com base no array "Header" criado anteriormente
def create_file ():
	if path.exists('report.csv') == False:
		with open('report.csv', 'w') as fileCSV:
			writer = csv.DictWriter(fileCSV, fieldnames=header)
			writer.writeheader()
	return None

# Suporte da actualização de um ficheiro csv com a informação do cliente e resultado
# Esta função atualiza o ficheiro .CSV com os dados de um jogador quando um jogo é terminado (com sucesso, sem sucesso,
# ou desistencia). Para isso, abre o ficheiro no modo "a" (append), para adicionar dados sem escrever por cima dos que já
# lá estavam. Para isso, procura pelo index "i", tal que o sock_id é igual ao client_id passado como parametro da função,
# e assim escreve todos os itens na posição "i" dos arrays no dicionário "gamers"
def update_file (client_id, result):
	with open('report.csv', 'a') as fileCSV:
		writer = csv.DictWriter(fileCSV, fieldnames=header)
		for i in range(0, len(gamers['sock_id'])):

			if client_id == gamers['sock_id'][i]:

				di = {'name': gamers['name'][i], 'sock_id': gamers['sock_id'][i], 'segredo': gamers['segredo'][i], 'max': gamers['max'][i],'jogadas': gamers['jogadas'][i], 'resultado': result}
		writer.writerow(di)
	return None

# Suporte da jogada de um cliente - operação GUESS
# Para que a função possa funcionar corretamente, temos que nos certificar de que o cliente que está tentando adivinhar
# o número tem uma sessão de jogo iniciada. Ou seja, se ele estiver no dicionaário "gamers", então prosseguimos com o guess,
# caso contrário, manda uma mensagem ao cliente com status: False e uma mensagem de erro a indicar que o cliente não
# está inserido na lista de jogadores ativos.
# Caso o cliente tenha um jogo iniciado.
# Primeiro buscamos o valor do numero secreto deste cliente através da função "numberToCompare()", que é armazenado na
# variável "segredo". Depois, descriptografamos o numero inserido pelo jogador (que é passado na mensagem enviada do cliente
# ao servidor, e que depois é encaminhada para a função pelo parametro "request") que é armazenado na variável "jogado".
# Caso o numero jogado seja igual ao segredo, o servidor envia uma mensagem ao cliente com status: True, e result: "equals",
# a indicar que o jogador acertou o número.
# Caso o número jogado seja maior que o segredo, o servidor envia uma mensagem ao cliente com status: True, e result: "larger",
# a indicar que o jogador jogou um número maior que o segredo.
# Caso o número jogado seja menor que o segredo, o servidor envia uma mensagem ao cliente com status: True, e result: "smaller",
# a indicar que o jogador jogou um número menor que o segredo.
# Por fim, atualiza no dicionário "gamers" o número de jogadas feitas.
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

# Suporte do pedido de terminação de um cliente - operação STOP
# Esta operação ocorre sempre que um jogo é terminado (quando o jogador acerta o segredo, ou quando faz mais jogadas do que
# podia).
# Para que um jogo seja encerrado, o cliente precisa estar na lista de jogadores ativos, ou seja, no dicionário "gamers".
# Caso o cliente naão esteja em um jogo ativo, a função envia uma mensagem ao cliente com status: False e uma mensagem de
# erro a indicar que o cliente não se encontra na lista de jogadores ativos.
# Caso o cliente esteja em um jogo ativo, o servidor envia uma mensagem ao cliente com status: True, a indicar que a finalização
# do jogo foi processada.
# O processamento do término de um jogo dá-se da seguinte forma:
# 1- O servidor atualiza no dicionário "gamers" o numero de jogadas que o jogador fez. Para isso, deve descriptografar o inteiro
# enviado pelo cliente, com auxílio da função decrypt_intvalue().
# 2- O servidor verifica se o último número jogado pelo utilizador (que também deve ser descriptografado) é igual ao segredo.
# Caso seja, atualiza o ficheiro .CSV com os dados do cliente e o resultado final "SUCCESS". Caso não seja, atualiza o
# ficheiro .CSV com os dados do cliente e o resultado final "FAILURE"
# 3- Por fim, elimina o cliente da lista de jogadores ativos através da função "clean_client()"
def stop_client (client_sock, request):
	if find_client_id(client_sock) in gamers['sock_id']:
		response = {'op': "STOP", 'status': True}
		send_dict(client_sock, response)
		for i in range(0, len(gamers['sock_id'])):
			if find_client_id(client_sock) == gamers['sock_id'][i]:
				gamers['jogadas'][i] = decrypt_intvalue(gamers['sock_id'][i],request['attempts'])
				if gamers['segredo'][i] == decrypt_intvalue(gamers['sock_id'][i],request['number']):
					update_file(find_client_id(client_sock), "SUCCESS")
				else:
					update_file(find_client_id(client_sock), "FAILURE")
		clean_client(client_sock)

	else:
		response = {'op': "STOP", 'status': False, 'error': "cliente inexistente"}
		send_dict(client_sock, response)
	print("CURRENT GAMERS: " + str(gamers))
	return None

def main():

	# O servidor deve ser iniciado com 1 argumento (porto), caso não seja, o programa é encerrado com uma mensagem
	# de erro.
	if len(sys.argv) != 2:
		print("Deve passar o porto como argumento para o servidor")
		sys.exit(1)

	# O porto deve ser um numero inteiro positivo, portanto, caso não seja, o programa é encerrado com uma mensagem de erro
	try:
		int(sys.argv[1])
	except ValueError:
		print("Porto deve ser um numero inteiro")
		sys.exit(2)
	if int(sys.argv[1])<0:
		print("Porto deve ser um numero inteiro positivo")
		sys.exit(2)

	# Aqui, ja temos certeza de que o porto é valido, portanto vamos apenas atribuir seu valor à variàvel.
	port = int(sys.argv[1])

	server_socket = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind (("127.0.0.1", port))
	server_socket.listen (10)

	clients = []

	# Função "create_file" é chamada sempre que o servidor é ligado
	create_file ()

	while True:
		try:
			available = select.select ([server_socket] + clients, [], [])[0]
		except ValueError:
			# Sockets may have been closed, check for that
			for client_sock in clients:
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
					new_msg (client_sock)
				else: # Or just disconnected
					clients.remove (client_sock)
					clean_client (client_sock)
					client_sock.close ()
					break # Reiterate select

if __name__ == "__main__":
	main()
