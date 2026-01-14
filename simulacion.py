import pygame
import sys
import random

### clases para la simulación de demanda de energía

class Edificio:
    def __init__(self, x, y, ancho, alto, tipo):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.tipo = tipo
        self.consumo_actual = 0

        # atributos para la simulacion

        if self.tipo == "residencial":
            self.color_base = (50, 150, 50) # verde oscuro
            self.hora_pico = 20 # 8 PM
            self.consumo_base = (alto * ancho) * 0.5 # kW

        elif self.tipo == "comercial":
            self.color_base = (50, 50, 150) # azul oscuro
            self.hora_pico = 13 # 1 PM
            self.consumo_base = (alto * ancho) * 0.8 # kw
        else: #industrial
            self.color_base = (150, 50, 50) # rojo oscuro
            self.hora_pico = 10 # 10 AM
            self.consumo_base = (alto * ancho) * 1.5 # kw
    
    def actualizar_consumo(self, hora_actual, temperatura_ambiente):
        # EL FACTOR HORARIO
        if self.tipo == "industrial":
            factor_uso = 0.8 # las fabricas operan casi todo el día
        else:
            distancia_hora_pico = abs(hora_actual - self.hora_pico) # que tan lejos estamos de la hora pico
            factor_uso = max(0.1, 1.0 - (distancia_hora_pico / 8))
        
        # EL FACTOR CLIMA (TEMPERATURA)

        factor_clima = 0
        if temperatura_ambiente > 25: # dias calurosos
            factor_clima = (temperatura_ambiente - 25) * 0.02 # aumento del 2% por grado sobre 25
        elif temperatura_ambiente < 15: # dias frios
            factor_clima = (15 - temperatura_ambiente) * 0.015 # aumento del 1.5% por grado bajo 15
        
        # CALCULO DEL CONSUMO ACTUAL
        self.consumo_actual = self.consumo_base * (factor_uso + factor_clima )

    def dibujar(self, superficie):
        brillo = min(100, int(self.consumo_actual / 10))
        
        # Sumamos el brillo al color base (R, G, B)
        r = min(255, self.color_base[0] + brillo)
        g = min(255, self.color_base[1] + brillo)
        b = min(255, self.color_base[2] + brillo)
        
        pygame.draw.rect(superficie, (r, g, b), self.rect)


### Configuración inicial de Pygame

pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulación de demanda de energía")
clock = pygame.time.Clock()
pygame.font.init()
fuente_info = pygame.font.SysFont('none', 24)
running = True

hora_global = 0
timer = 0
historial_consumo = []

# Configuración de tiempo de simulación
# `SEGUNDOS_POR_HORA_SIM` = segundos reales que equivalen a 1 hora simulada
SEGUNDOS_POR_HORA_SIM = 3000  # cambia este valor para acelerar/ralentizar la simulación
FPS = 60                     # frames por segundo esperado (coincide con clock.tick(60))
FRAMES_POR_HORA = SEGUNDOS_POR_HORA_SIM * FPS

# definimos las zonas (altura de cada panel)
ALTO_INFO = 100
ALTO_CIUDAD = 500
ALTO_GRAFICO = 200

Y_INICIO_GRAFICO = ALTO_INFO + ALTO_CIUDAD

# generacion de la ciudad

edificios = []
tipos = ["residencial", "comercial", "industrial"]

# espaciado entre edificios
filas = 6
columnas = 8
margen = 40

#se calcula el tamaño máximo de los edificios para que quepan en la pantalla

ancho_celda = WIDTH // columnas
alto_celda = ALTO_CIUDAD // filas

# crear edificios aleatorios

for fil in range(filas):
    for col in range(columnas):

        w = ancho_celda - margen
        h = alto_celda - margen

        #posicion exacta
        x = (col * ancho_celda) + (margen // 2)
        y = ALTO_INFO + (fil * alto_celda) + (margen // 2)
        
        tipo = random.choice(tipos)

        nuevo_edificio = Edificio(x, y, w, h, tipo)
        edificios.append(nuevo_edificio)
    
    

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    timer += 1
    if timer >= FRAMES_POR_HORA:  # Cada `SEGUNDOS_POR_HORA_SIM` segundos reales
        timer = 0           # Reiniciamos el contador
        hora_global += 1    # Avanzamos una hora

        if hora_global >= 24:
            hora_global = 0
        # Temperatura simulada (simple): Más calor al mediodía (12-14)
        # Una fórmula sencilla: entre 20 y 25 grados base + hasta 10 o 13 grados extra al mediodía (simula diversos tipos de clima)
        # Usamos una función seno para que suba y baje suavemente
        import math
        temperatura_actual = (random.randint(20, 25)) + (random.randint(10, 13)) * math.sin(hora_global * math.pi / 24)

    # Actualizar cada edificio
        consumo_total_ciudad = 0
        for edificio in edificios:
            edificio.actualizar_consumo(hora_global, temperatura_actual)
            consumo_total_ciudad += edificio.consumo_actual
            historial_consumo.append(consumo_total_ciudad)

            screen.fill((20, 20, 20)) # fondo oscuro

            pygame.draw.rect(screen, (50, 50, 50), (0, 0, WIDTH, ALTO_INFO))
            pygame.draw.rect(screen, (10, 10, 10), (0, ALTO_INFO, WIDTH, ALTO_CIUDAD))
            pygame.draw.rect(screen, (0, 0, 30), (0, Y_INICIO_GRAFICO, WIDTH, ALTO_GRAFICO))

            pygame.draw.line(screen, (255, 255, 255), (0, ALTO_INFO), (WIDTH, ALTO_INFO), 2)
            pygame.draw.line(screen, (255, 255, 255), (0, Y_INICIO_GRAFICO), (WIDTH, Y_INICIO_GRAFICO), 2)

            # 1. Preparamos el texto de la Hora y Temperatura
            texto_info = f"Hora: {hora_global:02d}:00 | Temp: {int(temperatura_actual)}°C"
            superficie_info = fuente_info.render(texto_info, True, (51, 18, 255)) # Blanco

            # 2. Preparamos el texto del Consumo Total
            texto_consumo = f"Consumo Total: {int(consumo_total_ciudad)} kW"
            superficie_consumo = fuente_info.render(texto_consumo, True, (255, 255, 0)) # Amarillo


            for edificio in edificios:
                edificio.dibujar(screen)

            screen.blit(superficie_info, (10, 10))       # Esquina superior izquierda
            screen.blit(superficie_consumo, (10, 40))    # Un poco más abajo para que no

            # Configuración del gráfico
            separacion_x = 3   # Píxeles entre cada punto
            escala_y = 0.001    # Para que el gráfico no sea gigante (ajústalo si se sale)
            max_puntos = WIDTH // separacion_x
            datos_a_dibujar = historial_consumo[-max_puntos:]
    
            # Solo dibujamos si hay al menos 2 puntos para conectar
            if len(datos_a_dibujar) > 1:
                for i in range(len(datos_a_dibujar) - 1):
                    val_a = datos_a_dibujar[i]
                    val_b = datos_a_dibujar[i + 1]
            
                    # Coordenadas X
                    x_a = i * separacion_x
                    x_b = (i + 1) * separacion_x
            
                    # Coordenadas Y (Calculadas desde el fondo de la pantalla hacia arriba)
                    # HEIGHT es el piso total (800). Restamos para subir.
                    y_a = HEIGHT - 20 - (val_a * escala_y) # El -20 es un pequeño margen inferior
                    y_b = HEIGHT - 20 - (val_b * escala_y)
            
                    # Aseguramos que la linea no se salga de su zona (clamping visual opcional)
                    if y_a < Y_INICIO_GRAFICO: y_a = Y_INICIO_GRAFICO
                    if y_b < Y_INICIO_GRAFICO: y_b = Y_INICIO_GRAFICO

                    pygame.draw.line(screen, (0, 255, 255), (x_a, y_a), (x_b, y_b), 2)

        pygame.display.flip()
        clock.tick(60)

pygame.quit()
sys.exit()