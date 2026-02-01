import random
import simpy
import math
from typing import List, Dict, Tuple
import pygame
from datetime import datetime, timedelta

# ============================================================
# CONFIGURACIÓN DE SUBESTACIONES
# ============================================================
SUBESTACIONES = {
    "Pequeña": {
        "capacidad_kw": 55000,       # 55 MW
        "capacidad_mw": 55,
        "costo_inversion": 50000,    # $50k instalación
        "costo_operativo_hora": 15,  # $15/hora operar
        "color": (251, 191, 36),     # Amarillo
        "nombre": "Subestación Compacta"
    },
    "Mediana": {
        "capacidad_kw": 110000,      # 110 MW
        "capacidad_mw": 110,
        "costo_inversion": 120000,   # $120k instalación
        "costo_operativo_hora": 25,  # $25/hora operar
        "color": (34, 211, 238),     # Cyan
        "nombre": "Subestación Estándar"
    },
    "Grande": {
        "capacidad_kw": 220000,      # 220 MW
        "capacidad_mw": 220,
        "costo_inversion": 250000,   # $250k instalación
        "costo_operativo_hora": 50,  # $50/hora operar
        "color": (232, 121, 249),    # Magenta
        "nombre": "Subestación Industrial"
    }
}

# ============================================================
# CLASE EDIFICIO (Versión Mejorada con Población y Tipo)
# ============================================================
class Edificio:
    def __init__(self, x: int, y: int, ancho: int, alto: int, tipo: str):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.tipo = tipo
        self.consumo_actual = 0.0
        self.brillo = 1.0
        
        # Población aleatoria según tipo (rango 100-2000)
        if self.tipo == "residencial":
            self.poblacion = random.randint(100, 800)
            self.color_base = (96, 165, 250)    # Azul neón base
            self.color_brillo = (59, 130, 246)  # Azul brillante
            self.hora_pico = 20  # 8 PM
            self.factor_tipo = 0.4  # kW por persona base
            self.forma = "casa"
            
        elif self.tipo == "comercial":
            self.poblacion = random.randint(200, 1200)
            self.color_base = (74, 222, 128)    # Verde neón base
            self.color_brillo = (34, 197, 94)   # Verde brillante
            self.hora_pico = 13  # 1 PM
            self.factor_tipo = 0.6  # Más consumo por persona
            self.forma = "oficina"
            
        else:  # industrial
            self.poblacion = random.randint(50, 400)
            self.color_base = (248, 113, 113)   # Rojo neón base
            self.color_brillo = (239, 68, 68)   # Rojo brillante
            self.hora_pico = 10  # 10 AM
            self.factor_tipo = 0.9  # Mucho consumo (maquinaria)
            self.forma = "fabrica"
        
        # Inicializar consumo
        self.consumo_actual = self.poblacion * self.factor_tipo * 0.3
    
    def calcular_consumo(self, hora_actual: int, temperatura: float) -> float:
        """
        Fórmula exacta: Consumo = (Población × FactorEdificio) × FactorHorario × FactorTemperatura
        """
        # Consumo base por población
        consumo_base = self.poblacion * self.factor_tipo
        
        # Factor horario basado en curvas de consumo realistas
        if self.tipo == "industrial":
            # Industria: operación constante con ligero pico matutino
            if 6 <= hora_actual <= 18:
                factor_hora = 0.8 + 0.2 * math.sin((hora_actual - 6) * math.pi / 12)
            else:
                factor_hora = 0.4  # Reducción nocturna
        elif self.tipo == "comercial":
            # Comercial: pico en horario laboral
            if 8 <= hora_actual <= 18:
                factor_hora = 0.6 + 0.4 * math.sin((hora_actual - 8) * math.pi / 10)
            elif 18 < hora_actual <= 22:
                factor_hora = 0.3  # Horario reducido
            else:
                factor_hora = 0.1  # Cierre nocturno
        else:  # residencial
            # Residencial: picos matutinos y nocturnos
            if 6 <= hora_actual <= 9:
                factor_hora = 0.4 + 0.3 * math.sin((hora_actual - 6) * math.pi / 3)
            elif 18 <= hora_actual <= 23:
                factor_hora = 0.5 + 0.5 * math.sin((hora_actual - 18) * math.pi / 5)
            else:
                factor_hora = 0.2  # Bajo consumo nocturno
        
        # Factor temperatura: impacto en HVAC (18-35°C)
        # Temperatura ideal: 22°C. Cada grado aumenta consumo
        if temperatura <= 22:
            # Frío: calefacción (moderado)
            factor_temperatura = 1 + ((22 - temperatura) * 0.05)
        else:
            # Calor: aire acondicionado (impacto EXTREMO)
            # Aumentamos coeficiente de 0.04 a 0.12 para forzar picos altos
            factor_temperatura = 1 + ((temperatura - 22) * 0.12)
        
        # Calcular brillo para efectos visuales (glow en horas pico)
        if abs(hora_actual - self.hora_pico) <= 1:
            self.brillo = 1.0 + (factor_hora * 0.8)
        elif abs(hora_actual - self.hora_pico) <= 3:
            self.brillo = 0.9 + (factor_hora * 0.4)
        else:
            self.brillo = 0.6 + (factor_hora * 0.2)
        
        # Aplicar fórmula exacta
        self.consumo_actual = consumo_base * factor_hora * factor_temperatura
        return self.consumo_actual
    
    def dibujar(self, screen):
        """Dibujar el edificio según su tipo"""
        color = (
            min(255, int(self.color_base[0] * self.brillo)),
            min(255, int(self.color_base[1] * self.brillo)),
            min(255, int(self.color_base[2] * self.brillo))
        )
        
        # Dibujar base del edificio
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        
        # Dibujar detalles según tipo
        if self.forma == "casa":
            # Techo triangular
            puntos = [
                (self.rect.centerx, self.rect.top - 5),
                (self.rect.left, self.rect.top + 15),
                (self.rect.right, self.rect.top + 15)
            ]
            pygame.draw.polygon(screen, color, puntos)
            # Ventanas
            for i in range(2):
                ventana_rect = pygame.Rect(
                    self.rect.left + 5 + i * 15,
                    self.rect.top + 20,
                    8, 10
                )
                pygame.draw.rect(screen, (255, 255, 200), ventana_rect)
                
        elif self.forma == "oficina":
            # Ventanas rectangulares
            for i in range(3):
                for j in range(2):
                    ventana_rect = pygame.Rect(
                        self.rect.left + 10 + i * 18,
                        self.rect.top + 15 + j * 20,
                        12, 15
                    )
                    pygame.draw.rect(screen, (255, 255, 200), ventana_rect)
                    
        else:  # fabrica
            # Chimenea
            chimenea_rect = pygame.Rect(
                self.rect.right - 15,
                self.rect.top - 20,
                8, 20
            )
            pygame.draw.rect(screen, (100, 100, 100), chimenea_rect)
            # Humo
            for i in range(3):
                pygame.draw.circle(screen, (200, 200, 200),
                                 (self.rect.right - 11, self.rect.top - 25 - i * 5), 4)

# ============================================================
# GENERADOR DE CIUDAD
# ============================================================
def generar_ciudad() -> List[Edificio]:
    """Genera la matriz de edificios ajustada al GRID_RECT"""
    edificios = []
    tipos = ["residencial", "comercial", "industrial"]
    pesos = [0.5, 0.3, 0.2]
    
    from config import GRID_RECT, GRID_FILAS, GRID_COLUMNAS, GRID_MARGIN_X, GRID_MARGIN_Y
    
    # Área disponible para el grid
    start_x = GRID_RECT[0] + GRID_MARGIN_X
    start_y = GRID_RECT[1] + GRID_MARGIN_Y
    available_w = GRID_RECT[2] - (2 * GRID_MARGIN_X)
    available_h = GRID_RECT[3] - (2 * GRID_MARGIN_Y)
    
    # Tamaño de celda
    cell_w = available_w // GRID_COLUMNAS
    cell_h = available_h // GRID_FILAS
    
    # Margen entre edificios
    gap = 20
    edificio_w = cell_w - gap
    edificio_h = cell_h - gap

    contador_industrias = 0
    limite_industrias = (GRID_FILAS * GRID_COLUMNAS) // 8  # Máximo 12.5% industriales
    
    for fil in range(GRID_FILAS):
        for col in range(GRID_COLUMNAS):
            x = start_x + (col * cell_w) + (gap // 2)
            y = start_y + (fil * cell_h) + (gap // 2)

            # Elegimos un tipo al azar
            tipo = random.choices(tipos, weights=pesos)[0]

           # CONDICIONAL: Si salió industrial pero ya hay 6, lo cambiamos a residencial
            if tipo == "industrial":
                if contador_industrias < limite_industrias:
                    contador_industrias += 1
                else:
                    # Si ya llegamos al límite, forzamos que sea residencial (o comercial)
                    tipo = "residencial"
            edif = Edificio(x, y, edificio_w, edificio_h, tipo)
            edificios.append(edif)
    
    return edificios

# ============================================================
# SIMULADOR ANUAL
# ============================================================
class ResultadoAnual:
    def __init__(self, tipo_subestacion: str):
        self.tipo = tipo_subestacion
        self.datos = SUBESTACIONES[tipo_subestacion]
        self.historial_demanda = []  # Lista de (dia, hora, demanda, temperatura)
        self.historial_horas = []    # Historial por hora para gráfico
        self.blackouts = 0           # Contador de horas sin luz
        self.dias_totales = 365
        self.costo_total = 0
        
    def calcular_metricas(self) -> Dict:
        """Calcula costos y eficiencia al final del año"""
        # Costo operativo: 365 días × 24 horas × costo/hora
        costo_operativo = 365 * 24 * self.datos["costo_operativo_hora"]
        self.costo_total = self.datos["costo_inversion"] + costo_operativo
        
        # Eficiencia: promedio de uso de capacidad
        capacidad = self.datos["capacidad_kw"]
        if len(self.historial_demanda) > 0:
            promedio_demanda = sum(d[2] for d in self.historial_demanda) / len(self.historial_demanda)
            eficiencia = (promedio_demanda / capacidad) * 100
        else:
            promedio_demanda = 0
            eficiencia = 0
        
        # Calcular confiabilidad
        horas_totales = 365 * 24
        confiabilidad = max(0, 1 - (self.blackouts / horas_totales)) * 100
        
        # Puntaje de optimización (mayor es mejor)
        puntaje_optimo = (confiabilidad * 10) - (self.costo_total / 1000)
        
        return {
            "tipo": self.tipo,
            "costo_total": round(self.costo_total, 2),
            "blackouts": self.blackouts,
            "eficiencia": round(eficiencia, 1),
            "confiabilidad": round(confiabilidad, 1),
            "promedio_demanda_kw": round(promedio_demanda, 0),
            "puntaje_optimo": round(puntaje_optimo, 1),
            "capacidad_mw": self.datos["capacidad_mw"]
        }

def simular_año(tipo_subestacion: str, edificios: List[Edificio]) -> ResultadoAnual:
    """
    Simula 1 año completo (365 días × 24 horas) con una subestación específica usando SimPy.
    """
    resultado = ResultadoAnual(tipo_subestacion)
    capacidad_max = resultado.datos["capacidad_kw"]
    
    print(f"Simulando año con Subestación {tipo_subestacion}...")
    
    # Crear entorno de SimPy
    env = simpy.Environment()
    
    # Proceso de simulación
    def proceso_simulacion():
        for dia in range(365):
            # Temperatura diaria con variación estacional y aleatoria
            # Simulación de estaciones: días 0-90 verano, 91-180 otoño, 181-270 invierno, 271-364 primavera
            if dia < 90:  # Verano
                temp_base = random.uniform(28, 35)
            elif dia < 180:  # Otoño
                temp_base = random.uniform(22, 28)
            elif dia < 270:  # Invierno
                temp_base = random.uniform(18, 25)
            else:  # Primavera
                temp_base = random.uniform(20, 30)
            
            # Variación horaria de temperatura
            for hora in range(24):
                # Variación diaria de temperatura: más fresco al amanecer, más caliente al mediodía
                if 6 <= hora <= 14:
                    temperatura_hora = temp_base + (hora - 6) * 0.8  # Calentamiento
                elif 14 < hora <= 20:
                    temperatura_hora = temp_base + (20 - hora) * 0.4  # Enfriamiento gradual
                else:
                    temperatura_hora = temp_base - 2  # Noche más fresca
                
                # Añadir variación aleatoria pequeña
                temperatura_hora += random.uniform(-0.5, 0.5)
                temperatura_hora = max(18.0, min(35.0, temperatura_hora))
                
                # Calcular consumo total de todos los edificios
                consumo_total = 0
                for edif in edificios:
                    consumo = edif.calcular_consumo(hora, temperatura_hora)
                    consumo_total += consumo
                
                # Verificar blackout
                en_blackout = consumo_total > capacidad_max
                if en_blackout:
                    resultado.blackouts += 1
                
                # Guardar dato histórico (una muestra cada hora)
                resultado.historial_horas.append(consumo_total)
                
                # Guardar datos cada 6 horas para estadísticas
                if hora % 6 == 0:
                    resultado.historial_demanda.append((dia, hora, consumo_total, temperatura_hora))
                
                # Avanzar 1 hora en SimPy
                yield env.timeout(1)
    
    # Ejecutar el proceso
    env.process(proceso_simulacion())
    env.run(until=365 * 24)
    
    return resultado

# ============================================================
# OPTIMIZADOR
# ============================================================
def encontrar_mejor_subestacion(edificios: List[Edificio]) -> Tuple[str, List[Dict]]:
    """
    Corre las 3 simulaciones y determina la óptima.
    """
    resultados = []
    
    print("🏆 Iniciando comparación de subestaciones...")
    
    for tipo in ["Pequeña", "Mediana", "Grande"]:
        res = simular_año(tipo, edificios)
        metricas = res.calcular_metricas()
        resultados.append(metricas)
        print(f"  📊 {tipo}: ${metricas['costo_total']:,.0f} | "
              f"Blackouts: {metricas['blackouts']}h | "
              f"Eficiencia: {metricas['eficiencia']:.1f}%")
    
    # Criterio: 0 blackouts y menor costo
    candidatos_validos = [r for r in resultados if r["blackouts"] == 0]
    
    if candidatos_validos:
        # Entre las que no fallan, elegir la más barata
        ganadora = min(candidatos_validos, key=lambda x: x["costo_total"])
    else:
        # Si todas tienen blackouts, elegir la que menos falló
        ganadora = min(resultados, key=lambda x: x["blackouts"])
    
    print(f"\n✅ ÓPTIMA ELEGIDA: {ganadora['tipo']}")
    print(f"   Costo: ${ganadora['costo_total']:,.0f}")
    print(f"   Confiabilidad: {ganadora['confiabilidad']:.1f}%")
    
    return ganadora["tipo"], resultados

# ============================================================
# FUNCIONES AUXILIARES PARA LA INTERFAZ
# ============================================================
def obtener_datos_snapshot(edificios: List[Edificio], hora: int, temperatura: float) -> Dict:
    """Devuelve datos en tiempo real para mostrar en UI"""
    consumo_residencial = 0
    consumo_comercial = 0
    consumo_industrial = 0
    
    for ed in edificios:
        consumo = ed.calcular_consumo(hora, temperatura)
        if ed.tipo == "residencial":
            consumo_residencial += consumo
        elif ed.tipo == "comercial":
            consumo_comercial += consumo
        else:
            consumo_industrial += consumo
    
    consumo_total = consumo_residencial + consumo_comercial + consumo_industrial
    poblacion_total = sum(ed.poblacion for ed in edificios)
    
    return {
        "hora": hora,
        "temperatura": round(temperatura, 1),
        "consumo_total_kw": round(consumo_total, 0),
        "consumo_residencial": round(consumo_residencial, 0),
        "consumo_comercial": round(consumo_comercial, 0),
        "consumo_industrial": round(consumo_industrial, 0),
        "poblacion_total": poblacion_total,
        "num_edificios": len(edificios)
    }

def verificar_blackout(consumo: float, tipo_subestacion: str) -> bool:
    """Retorna True si hay apagón"""
    return consumo > SUBESTACIONES[tipo_subestacion]["capacidad_kw"]

def get_color_subestacion(tipo: str) -> Tuple[int, int, int]:
    return SUBESTACIONES[tipo]["color"]

# ============================================================
# TEST RÁPIDO
# ============================================================
if __name__ == "__main__":
    print("Testeando motor lógico...")
    
    # Crear ciudad de prueba
    pygame.init()
    eds = generar_ciudad()
    
    print(f"Generados {len(eds)} edificios")
    print(f"Población total: {sum(e.poblacion for e in eds)} personas")
    
    # Test simulación rápida
    temp = 28.0
    for h in [0, 6, 12, 18, 22]:
        datos = obtener_datos_snapshot(eds, h, temp)
        print(f"Hora {h:02d}:00 - Consumo: {datos['consumo_total_kw']:,.0f} kW")
    
    print("\n" + "="*50)
    mejor, todos = encontrar_mejor_subestacion(eds)