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
# Quando o utilizador fizer o input do comando QUIT, esta função será chamada. Ela envia uma mensagem ao servidor e aguarda
# por uma resposta, que será retornada pela função "sendrecv_dict()", e a armazena na variável "response".
# Caso a resposta seja valida (recorrendo à função "validate_response()"), checa o 'status' da resposta. Se o status for True,
# quer dizer que o teérmino do jogo foi computado com sucesso (print mensagem de sucesso). Caso o status seja False, quer
# dizer que o o servidor não encontrou o cliente atual na lista de jogadores ativos (print mensagem de erro).
# Caso a resposta do servidor não seja vaálida, mostramos ao utilizador uma mensagem de erro correspondente.
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

# Suporte da execução do cliente

#chave de cifragem gerada e codificada no modelo Base64 para ser enviada ao servidor
cipherkey = os.urandom(16)
cipherkey_toSend = str(base64.b64encode(cipherkey), 'utf8')

# Esta é a função responsável por gerenciar o programa
def run_client (client_sock, client_id):

	# ----VARIAVEIS---
	#
	# -- emUso: enquanto ela estiver True, o cliente ira estar a espera de novos comandos. A função STOP pode encerrar o ciclo
	# ao mudar esta variável para False.
	# -- jogadas: Numero de jogadas feitas pelo jogador. Iniciada com valor 0
	# -- jogMax: numero maximo de jogadas que um jogador pode fazer. Este valor é gerado no servidor e retornado por ele
	# após o comando START, que inicia um novo jogo. é uma variável vazia até que receba o numero de jogadas do servidor.
	# -- auto: Todos os comandos, START, GUESS e QUIT, devem ser pedidos pelo utilizador através do input do teclado. O comando
	# STOP, no entanto, é feito automaticamnete após ser identificado o fim de um jogo. Portanto, quando esta variavel for
	# True, significa que o proximo comando a ser executado, será feito automaticamente pelo sistema, e quando for False,
	# o programa estará à espera de um input do utilizador.
	# -- nextCom: próximo comando a ser executado em modo automatico.
	# -- lastAttempt: Último número jogado pelo utilizador ao fazer o comando GUESS.
	emUso = True
	jogadas = 0
	jogMax = None
	auto=False
	nextCom = ""
	lastAttempt = None

	# O programa fica à espera de novos comandos enquanto estiver em uso (emUso == True)
	while emUso:
		# Se auto == False, então o próximo comando a ser executado deverá ser inserido pelo utilizador. Caso contrário,
		# o comando a ser executado automaticamente será "nextCom" (definido na execução anterior).
		if auto == False:
			inp = input("Comando: ")
			comando = inp.upper()
		else:
			comando=nextCom
			auto = False

		# Se o comando for START, o cliente envia uma mensagem ao servidor indicando a operaçao que deseja executar, o
		# id do cliente (inserido na linha de comando ao executar o programa), e a chave de cifra codificada.
		# Ao receber uma resposta do servidor, esta será validada, e caso seja válida:
		# 	1- verifica o status da resposta. Se for false, deverá printar a mensagem de erro recebida do servidor, se for
		# 	True, irá descriptografar o número máximo de jogadas para esta partida recorrendo à função "decrypt_intvalue"
		# 	e o armazenará na variàvel "jogMax".
		# 	2- inicia a contagem de jogadas, colocando a variàvel "jogadas" à zero.
		# 	3- mostra uma mensagem de confirmação ao utilizador.
		# Caso a resposta do servidor não seja válida:
		# 	1- mostra uma mensagem de erro referente ao erro identificado pelo servidor.
		if comando == "START":

			request = {'op': 'START', 'client_id': client_id, 'cipherkey':cipherkey_toSend }
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

		# Se o comando for QUIT, o programa processa o pedido do cliente recorrendo à função "quit_action()" e volta as
		# variáveis "jogadas" e "jogMax" aos seus estados iniciais.
		if comando == "QUIT":
			quit_action(client_sock, jogadas)
			jogadas = 0
			jogMax = None

		# Se o comando for GUESS, temos que inicializar duas novas variáveis para checar se o número inserido pelo utilizador
		# é de fato um número inteiro e se é válido (ou seja, dentro do intervalo de 0 a 100).
		if comando == "GUESS":
			numeroValido = False
			numeroInteiro = False
			number = ""

			#verifica se o input é um numero inteiro válido (recorrendo à "try-catch"es e "if-else"s), e enquanto não
			# for, pede um novo input ao utilizador.
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

			# Nesta parte da execução do código já temos certeza de que o número jogado é um inteiro válido. Portanto,
			# preparamos a mensagem que será enviada ao servidor contendo o número jogado após ser criptografado,
			# recorrendo à função "encrypt_intvalue()".
			request = {'op': 'GUESS', 'number': encrypt_intvalue(cipherkey,number)}

			# a variavel "lastAttempt" recebe o numero que foi jogado,
			lastAttempt = number

			# e aqui checamos se o numero de jogadas é igual ao número máximo de jogadas. Caso seja, nada é feito, e o
			# ciclo passa para a próxima execução.
			if jogadas == jogMax:
				continue

			# Caso o jogador ainda tenha jogadas disponíveis, a mensagem é enviada ao servidor, e sua resposta é validada
			# pela função "validate_response()".
			else:
				response = sendrecv_dict(client_sock, request)

				if validate_response(client_sock, response):

					# Se a resposta do servidor for válida, e se o status for True, ou seja, se o servidor não reportar erros,
					# computamos a jogada, somando 1 ao numero de jogadas e avaliamos o resultado reportado pelo servidor
					# em sua resposta.
					if response['status']:
						jogadas = jogadas + 1

						# Se o resultado for "equals", o jogador acertou o número, e portanto atribuimos True à "auto" e
						# STOP à "nextCom", tendo em vista que o jogo acabou e STOP deverá ser executado automaticamente
						# na próxima execução do ciclo While.
						if response['result'] == "equals":
							print("Parabéns, acertaste o número!")
							auto = True
							nextCom = "STOP"
							continue

						# Se o resultado for "smaller", o jogador jogou um numero menor que o numero secreto, e portanto
						# mostramos uma mensagem a dizer isso.
						elif response['result'] == "smaller":
							print("O número secreto é maior!")

						# Se o resultado for "larger", o jogador jogou um numero maior que o numero secreto, e portanto
						# mostramos uma mensagem a dizer isso.
						elif response['result'] == "larger":
							print("O número secreto é menor!")

						# Ao fim de toda jogada, relembramos ao jogador o numero maximo de jogadas que pode fazer, e o
						# número de jogadas que já fez.
						print("Max: " + str(jogMax) + " Jogadas: " + str(jogadas))

						# Caso o número de jogadas feitas for igual ao número maximo de jogadas, mostramos uma mensagem
						# ao jogador e atribuimos True à "auto" e STOP à "nextCom", tendo em vista que o jogo acabou e
						# STOP deverá encerrar a partida automaticamente na próxima execução do ciclo While.
						if jogadas == jogMax:
							print("Atingiu o limite de jogadas! Comece outro jogo para tentar novamente.")
							auto = True
							nextCom = "STOP"
							continue

					# Caso o status da mensagem recebida do servidor seja False, mostramos uma mensagem contendo o erro
					# reportado pelo servidor
					else:
						print(response['error'])

				# Caso a resposta do servidor não seja válida, mostramos a respetiva mensagem de erro ao utilizador
				else:
					print("Erro: resposta do servidor não é valida")

		# Se o comando for STOP, enviamos a mensagem que será enviada ao servidor com o valor criptografado do último
		# número jogado e do número total de jogadas (recorrendo à função "encrypt_intvalue()").
		if comando == "STOP":
			request = {'op': 'STOP', 'number': encrypt_intvalue(cipherkey, number), 'attempts': encrypt_intvalue(cipherkey, jogadas)}
			response = sendrecv_dict(client_sock, request)

			# Se a resposta de servidor ao pedido for válida, o jogo foi terminado com sucesso, e podemos terminar sua
			# execução atribuindo False à "emUso"
			if validate_response(client_sock, response):
				emUso = False
				continue

			# Caso a resposta do servidor não seja válida, mostramos a respetiva mensagem de erro ao utilizador
			else:
				print("Erro: resposta do servidor não é valida")

	return None
	
# Quando o programa é executado, devem ser passados alguns argumentos na linha de comando, nesta secção do código,
# verificamos estes argumentos.
# O programa pode ser executado de 2 modos: com 3 argumentos (ID, Porto e Maquina), ou com 2 argumentos (ID e porto).
# No caso da máquina estar omissa nos argumentos, devemos considerar a máquina local (127.0.0.1).
# A variável "instead2" controla os modos de execução do programa (2 argumentos, ou 3). Quando instead2 == True, está a
# funcionar em modo de 2 argumentos, com a maquina local automaticamente designada como destino.
def main():
	instead2 = False

	# Caso não sejam passados 3 argumentos, verificamos então se foram passados 2 (maquina omissa). Neste caso, instead2
	# recebe True, caso contrário, o programa encerra com uma mensagem a especificar como deve ser executado.
	if len(sys.argv) != 4:
		if len(sys.argv) == 3:
			instead2 = True
		else:
			print("Deve passar como argumentos: client_id, Porto, DNS")
			sys.exit(1)

	# Aqui verificamos se o argumento do Porto é um número inteiro ao tentar converter sua string para int. Caso a conversão
	# falhe, encerramos o programa com uma mensagem de erro.
	try:
		int(sys.argv[2])
	except ValueError:
		print("Porto deve ser um numero inteiro")
		sys.exit(2)

	# Aqui verificamos se o argumento do Porto é um número inteiro POSITIVO. Caso não seja, encerramos o programa com
	# uma mensagem de erro.
	if int(sys.argv[2]) < 0:
		print("Porto deve ser um numero inteiro positivo")
		sys.exit(2)

	# Se o programa estiver a ser executado em modo de 2 argumentos, a máquina designada é a máquina local 127.0.0.1.
	# Caso contrário, atribuimos à variável o valor passado na linha de comando.
	# A string da máquina é então separada em um array de strings, para que possamos analisar seus elementos separadamente.
	if instead2:
		maquina = "127.0.0.1".split(".")
	else:
		maquina = sys.argv[3].split(".")

	# Caso o array dos elementos da maquina não tenha 4 elementos, encerramos o programa com uma mensagem de erro.
	if len(maquina) != 4:
		print("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")
		sys.exit(2)

	# Para cada elemento do array, verificamos se são números inteiros ao tentar fazer uma conversão de String para int.
	# Também verificamos se os elementos estão dentro do intervalo válido (maior que 0 e menor que 255).
	# em ambos os casos, se os items do array não conformarem com os requisitos, o programa é encerrado com uma mensagem
	# de erro.
	for digito in maquina:
		try:
			int(digito)
		except ValueError:
			print("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")
			sys.exit(2)
		if int(digito) > 255 or int(digito) < 0:
			print("maquina deve ser especificada no formato x.x.x.x, com x entre 0 e 255")
			sys.exit(2)

	# Aqui, ja temos certeza que os argumentos passados na linha de comando são validos, portanto apenas os atribuímos
	# às suas respetivas variáveis, de acordo com o modo de execução (2 ou 3 argumentos)
	port = int(sys.argv[2])

	if instead2:
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
