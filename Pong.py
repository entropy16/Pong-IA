import pygame
import random
import math
import pickle
import os.path

NEGRO = [7,7,7]
BLANCO = [255,255,255]
AZUL = [0,0,255]
ROJO = [255,0,0]
WIDTH = 600
HEIGHT = 400

class Paleta(pygame.sprite.Sprite):
	def __init__(self, color, pos):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface([10,100])
		self.image.fill(color)
		self.rect = self.image.get_rect()
		self.rect.x = pos[0]
		self.rect.y = pos[1]
		self.vely = 0

	def update(self): ## Movimiento de la Paleta

		if self.rect.top + self.vely >= 10:
			self.rect.y += self.vely
		else: 
			self.vely = 0 
			self.rect.bottom = self.rect.height + 12	

		if self.rect.bottom + self.vely <= 390:
			self.rect.y += self.vely
		else:
			self.vely = 0
			self.rect.top = HEIGHT - self.rect.height - 10

class Pelota(pygame.sprite.Sprite):
	def __init__(self, modo):
		pygame.sprite.Sprite.__init__(self)
		self.modo = modo
		self.image = pygame.Surface([10,10])
		self.image.fill(NEGRO)
		self.rect = self.image.get_rect()
		self.rect.center = [300,200]
		self.vel = calcularVel(6, self.modo)
		self.paletas = pygame.sprite.Group()
		self.players = []
		
	def update(self): ## Movimiento de la Pelota y colisión con las paletas
		self.rect.x += self.vel[0]
		self.rect.y += self.vel[1]

		# Detección de colisión entre la pelota y las paletas
		if len(self.players) > 1:
			if self.rect.left >= (self.players[0].paddle.rect.right - 7) and self.rect.right <= (self.players[1].paddle.rect.left + 7):
				ls_col = pygame.sprite.spritecollide(self, self.paletas, False, pygame.sprite.collide_rect)
				if len(ls_col) >= 1:
					self.vel[0] = self.vel[0] * -1
					self.vel[1] = round(self.vel[1] + random.uniform(0,0.5), 1)
					for player in self.players:
						if player.paddle == ls_col[0]:
							player.reward(10,(self.rect.x, self.rect.y, self.vel[0], self.vel[1], player.paddle.rect.top))
		else: 
			if self.rect.left >= (self.players[0].paddle.rect.right - 7):
				ls_col = pygame.sprite.spritecollide(self, self.paletas, False, pygame.sprite.collide_rect)
				if len(ls_col) >= 1:
					self.vel[0] = self.vel[0] * -1
					self.vel[1] = round(self.vel[1] + random.uniform(0,0.5), 1)
					for player in self.players:
						if player.paddle == ls_col[0]:
							player.reward(10,(self.rect.x, self.rect.y, self.vel[0], self.vel[1], player.paddle.rect.top))

		# Rebote sobre los limites
		if self.rect.top <= 10:
			self.vel[1] = self.vel[1] * -1
			self.rect.bottom = self.rect.height + 10
		if self.rect.bottom >= 390:
			self.vel[1] = self.vel[1] * -1
			self.rect.top = HEIGHT - self.rect.height - 10
		# Rebote en la pared derecha, sólo para modo Entrenamiento
		if self.rect.right >= 560 and self.modo == 1:
			self.vel[0] = self.vel[0]*-1
			self.rect.right = 555

		# Reseteo cuando hay anotación
		if self.rect.left <= 10:
			self.rect.center = [300,200]
			self.vel = calcularVel(6, self.modo)
		if self.rect.right >= 590:
			self.rect.center = [300,200]
			self.vel = calcularVel(6, self.modo)

	def getState(self):
		# Obtener la información de la pelota para la definición del estado
		return (round(self.rect.x/600,2), round(self.rect.y/400,2), self.vel[0], self.vel[1])

def calcularVel(vel, modo):
	
	if modo == 1: # Modo entrenamiento
		ang = random.uniform(2.6, 3.7) + 0.1
	if modo == 2: # Modo Jugadores
		opcion = random.choice([1,2])
		if opcion == 1:
			ang = random.uniform(0.5, -0.5) + 0.1
		if opcion == 2:
			ang = random.uniform(2.6, 3.7) + 0.1

	velx = round(vel * math.cos( ang ), 1)
	vely = round(vel * math.sin( ang ), 1)

	vel = [velx,vely]

	return vel

class Player:
	def __init__(self, paddle):
		self.breed = "Humano"
		self.paddle = paddle
		self.puntaje = 0
		
	def start_game(self):
		print("\nNuevo Juego!")
		
	def move(self, board):
		pass
		
	def reward(self, value, state):
		pass		

class QLearnPlayer(Player):
	def __init__(self, paddle, pelota, dificultad, epsilon=0.2, alpha=0.4, gamma=0.96):
		self.breed = "Qlearner"
		self.paddle = paddle
		self.pelota = pelota
		self.dificultad = dificultad - 1
		self.puntaje = 0
		self.q = self.importQ() # (state, action) keys: Q values
		self.epsilon = epsilon # e-greedy chance of random exploration
		self.alpha = alpha # learning rate
		self.gamma = gamma # discount factor for future rewards
		
	def start_game(self): 
		self.last_state = ('',)*5
		self.last_move = None
		
	def getQ(self, state, action):
		# encourage exploration; "optimistic" 1.0 initial values
		if self.q.get((state, action)) is None:
			self.q[(state, action)] = 1.0
		return self.q.get((state, action))
		
	def move(self, state):
		self.last_state = tuple(state)
		actions = self.available_moves(state)
		
		if random.random() < self.epsilon: # explore!
			self.last_move = random.choice(actions)
			return self.last_move

		qs = [self.getQ(self.last_state, a) for a in actions]
		maxQ = max(qs)
		
		if qs.count(maxQ) > 1:
			# more than 1 best option; choose among them randomly
			best_options = [i for i in range(len(actions)) if qs[i] == maxQ]
			i = random.choice(best_options)
		else:
			i = qs.index(maxQ)

		self.last_move = actions[i]
		return actions[i]

	def available_moves(self, state):
		if self.paddle.rect.top + 5*self.dificultad > self.pelota.rect.bottom:
			return [0,-1]
		if self.paddle.rect.bottom - 5*self.dificultad < self.pelota.rect.top:
			return [1,0]
		if ((self.paddle.rect.top + 5*self.dificultad <= self.pelota.rect.bottom) and 
			(self.paddle.rect.bottom - 5*self.dificultad>= self.pelota.rect.top)):
			return [1,0,-1]

	def reward(self, value, state):
		if value != 0 and modo == 1:
			print(f"{self.breed} recompensado: {value}")

		if self.last_move:
			self.learn(self.last_state, self.last_move, value, tuple(state))
	
	def learn(self, state, action, reward, result_state):
		prev = self.getQ(state, action)
		maxqnew = max([self.getQ(result_state, a) for a in self.available_moves(state)])
		self.q[(state, action)] = prev + self.alpha * ((reward + self.gamma*maxqnew) - prev)

	def exportQ(self):
		with open('Qdict.pkl', 'wb') as f:
			pickle.dump(self.q, f) 

	def importQ(self):
		if os.path.exists('Qdict.pkl'):
			with open('Qdict.pkl', 'rb') as f:
				Qdict = pickle.load(f)
			return Qdict
		else: return {}
		
def Pong(modo=2, dificultad=1):
	# Inicialización de Pygame
	pygame.init()
	pantalla = pygame.display.set_mode([WIDTH,HEIGHT])

	FuenteHud = pygame.font.SysFont("Cooper", 50)

	paletas = pygame.sprite.Group()
	pelotas = pygame.sprite.Group()

	pelota = Pelota(modo)

	player1 = QLearnPlayer(Paleta(AZUL, [30,100]), pelota, dificultad)
	puntaje1 = FuenteHud.render(str(player1.puntaje), 0, NEGRO)
	paletas.add(player1.paddle)
	players = [player1]

	if modo == 2: # Modo jugadores
		player2 = Player(Paleta(ROJO, [560,170]))
		puntaje2 = FuenteHud.render(str(player2.puntaje), 0, NEGRO)
		paletas.add(player2.paddle)
		players.append(player2)

	pelota.paletas = paletas
	pelota.players = players

	pelotas.add(pelota)

	fin = False
	victoria = False
	reloj = pygame.time.Clock()
	player1.start_game()
	if modo == 2: 
		player2.start_game()

	# Bucle principal
	while not fin:
		# Captador de eventos, para el movimiento por teclado
		for event in pygame.event.get(): 
			if event.type == pygame.QUIT:
				fin = True
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_UP:
					player2.paddle.vely = -5
				if event.key == pygame.K_DOWN:
					player2.paddle.vely = 5
			if event.type == pygame.KEYUP:
				if event.key == pygame.K_w or event.key == pygame.K_s:
					player1.paddle.vely = 0
				if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
					player2.paddle.vely = 0

		#Movimiento QLearnPlayer
		if player1.__class__ == QLearnPlayer:
			player1.paddle.vely = 5*player1.move(pelota.getState()+(round(player1.paddle.rect.top/400, 2),))			

		#Control de puntaje y recompensas por anotación:
		if pelota.rect.left <= 15 and modo == 2: # Recompensa negativa por que le anotaron al player1
			player2.puntaje += 1
			player1.reward(-1, pelota.getState()+(round(player1.paddle.rect.top/400, 2),))
			puntaje2 = FuenteHud.render(str(player2.puntaje), 0, NEGRO)
		else:
			player1.reward(0, pelota.getState()+(round(player1.paddle.rect.top/400, 2),))
		if pelota.rect.right >= 585: # Recompensa negativa por que le anotaron al player2
			player1.puntaje += 1
			if modo == 2:
				player2.reward(-1, pelota.getState()+(round(player2.paddle.rect.top/400, 2),))
			puntaje1 = FuenteHud.render(str(player1.puntaje), 0, NEGRO)

		# Recompensas por "perseguir" la pelota
		if pelota.rect.center[1] >= player1.paddle.rect.top - 30 and pelota.rect.center[1] <= player1.paddle.rect.bottom + 30:
			player1.reward(1, pelota.getState() + (round(player1.paddle.rect.top/400, 2),))
		if pelota.rect.center[1] >= player1.paddle.rect.top and pelota.rect.center[1] <= player1.paddle.rect.bottom:
			player1.reward(3, pelota.getState() + (round(player1.paddle.rect.top/400, 2),))
		if pelota.rect.center[1] >= player1.paddle.rect.top + 30 and pelota.rect.center[1] <= player1.paddle.rect.bottom - 30:
			player1.reward(5, pelota.getState() + (round(player1.paddle.rect.top/400, 2),))

		# Puntaje de verguenza por mvto ilegal
		if player1.paddle.rect.top < 10 or player1.paddle.rect.bottom > 390: 
			player1.reward(-99, pelota.getState() + (round(player1.paddle.rect.top/400, 2),))

		#Condicion de victoria:
		if modo == 2: # Modo Jugadores
			if player1.puntaje == 5:
				txtVictoria = FuenteHud.render("¡{} ha ganado!".format(player1.breed), 0, NEGRO)
				victoria = True
			if player2.puntaje == 5:
				txtVictoria = FuenteHud.render("¡{} ha ganado!".format(player2.breed), 0, NEGRO)
				victoria = True

		# Actualización de la pantalla
		pantalla.fill(BLANCO)
		pygame.draw.line(pantalla,NEGRO,[10,10],[590,10])
		pygame.draw.line(pantalla,NEGRO,[10,390],[590,390])
		if modo == 1: # Modo Entrenamiento
			pygame.draw.line(pantalla,NEGRO,[560,0],[560,400])

		if not(victoria):
			paletas.update()
			pelotas.update()
			paletas.draw(pantalla)
			pelotas.draw(pantalla)

			pantalla.blit(puntaje1, [50,20])
			if modo == 2:
				pantalla.blit(puntaje2, [300,20])
		else: 
			pelota.rect.center = [300,200]
			pelota.vel = [0,0]
			pantalla.blit(txtVictoria, [140,170])

		pygame.display.flip()

		# Reloj de juego
		if modo == 1: # Modo entrenamiento
			reloj.tick(1000)
		if modo == 2: # Modo jugadores
			reloj.tick(40*dificultad)

	if player1.__class__ == QLearnPlayer:
		player1.exportQ()

	pygame.quit()

if __name__ == '__main__':
	print("Iniciando Pong!")
	option = input("Ingrese una opción:\n1. Jugar\n2. Instrucciones\n3. Salir\n")

	while int(option) != 1:
		if int(option) == 2:
			print("Bienvenido a Pong para IA!\nHay dos modos de juego disponbles, el modo Entrenamiento, "+
				  "que es para ver cómo la IA juega y aprende, y un modo IA vs Jugador, en el que podrá "+
				  "enfrentar a la IA. Además, puede seleccionar la dificultad, la cual aumentará "+
				  "la velocidad del juego y la capacidad de la IA")
			option = input("Ingrese una opción:\n1. Jugar\n2. Instrucciones\n3. Salir\n")
		if int(option) == 3:
			print("Fin del juego!")
			break

	if int(option) == 1:
		modo = int(input("Ingrese el modo de juego:\n1. Modo Entrenamiento IA\n2. Modo IA vs Jugador\n"))
		if not([1,2].__contains__(modo)):
			print("Sólo hay 2 modos. Reinicie")
		else:
			dificultad = int(input("Ingrese la dificultad de la IA de 1 a 3:\n"))
			if not([1,2,3].__contains__(dificultad)):
				print("La dificultad es de 1 a 3. Reinicie")
			else: 
				Pong(modo,dificultad)
