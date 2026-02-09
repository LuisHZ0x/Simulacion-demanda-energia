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
        "capacidad_kw": 300000,      # 220 MW
        "capacidad_mw": 300,
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
def generar_ciudad(target_edificios: int = 50) -> List[Edificio]:
    """Genera la matriz de edificios ajustada al GRID_RECT y la cantidad solicitada"""
    edificios = []
    tipos = ["residencial", "comercial", "industrial"]
    pesos = [0.5, 0.3, 0.2]
    
    from config import GRID_RECT, GRID_MARGIN_X, GRID_MARGIN_Y
    
    # Área disponible para el grid
    start_x = GRID_RECT[0] + GRID_MARGIN_X
    start_y = GRID_RECT[1] + GRID_MARGIN_Y
    available_w = GRID_RECT[2] - (2 * GRID_MARGIN_X)
    available_h = GRID_RECT[3] - (2 * GRID_MARGIN_Y)

    # Calcular filas y columnas basándonos en el aspecto del área y la cantidad deseada
    aspect_ratio = available_w / available_h
    
    # cols * filas = target
    # cols / filas = aspect_ratio  => cols = filas * aspect_ratio
    # (filas * aspect_ratio) * filas = target => filas^2 = target / aspect_ratio
    
    calc_filas = math.sqrt(target_edificios / aspect_ratio)
    rows = max(2, round(calc_filas))
    cols = max(2, round(target_edificios / rows))
    
    # Recalcular para asegurar que cubrimos el target (puede sobrar un poco)
    while rows * cols < target_edificios:
        if cols / rows < aspect_ratio:
            cols += 1
        else:
            rows += 1

    # Tamaño de celda
    cell_w = available_w // cols
    cell_h = available_h // rows
    
    # Margen entre edificios
    gap = max(5, int(min(cell_w, cell_h) * 0.15)) # Gap dinámico
    edificio_w = cell_w - gap
    edificio_h = cell_h - gap

    contador_industrias = 0
    limite_industrias = (rows * cols) // 8  # Máximo 12.5% industriales
    
    count = 0
    for fil in range(rows):
        for col in range(cols):
            if count >= target_edificios: break
            
            x = start_x + (col * cell_w) + (gap // 2)
            y = start_y + (fil * cell_h) + (gap // 2)

            # Elegimos un tipo al azar
            tipo = random.choices(tipos, weights=pesos)[0]

           # CONDICIONAL: Si salió industrial pero ya hay muchas, lo cambiamos
            if tipo == "industrial":
                if contador_industrias < limite_industrias:
                    contador_industrias += 1
                else:
                    tipo = "residencial"
            
            edif = Edificio(x, y, edificio_w, edificio_h, tipo)
            edificios.append(edif)
            count += 1
    
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
        if len(self.historial_horas) > 0:
            promedio_demanda = sum(self.historial_horas) / len(self.historial_horas)
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

def simular_anio(tipo_subestacion: str, edificios: List[Edificio], 
                 dia_inicio: int = 0, hora_inicio: int = 0, 
                 probabilidad_tormenta: float = 0.0) -> ResultadoAnual:
    """
    Simula desde el momento actual hasta fin de año (365 días).
    Incluye probabilidad de tormentas.
    """
    resultado = ResultadoAnual(tipo_subestacion)
    capacidad_max = resultado.datos["capacidad_kw"]
    
    print(f"Simulando {tipo_subestacion} desde Día {dia_inicio}...")
    
    env = simpy.Environment()
    
    # Límite duro de tormentas anuales (60 máx)
    MAX_TORMENTAS = 60
    tormentas_generadas = 0
    
    def proceso_simulacion():
        nonlocal tormentas_generadas
        horas_totales = (365 * 24) - (dia_inicio * 24 + hora_inicio)
        
        # Iterar hora por hora desde el momento actual
        tiempo_actual = dia_inicio * 24 + hora_inicio
        
        # Estado de tormenta
        tiempo_tormenta_restante = 0
        
        for _ in range(int(horas_totales)):
            dia_actual = tiempo_actual // 24
            hora_dia = tiempo_actual % 24
            
            # --- CLIMA ---
            # (Lógica de estaciones igual que antes)
            if dia_actual < 90:  # Verano
                temp_base = random.uniform(28, 35)
            elif dia_actual < 180:  # Otoño
                temp_base = random.uniform(22, 28)
            elif dia_actual < 270:  # Invierno
                temp_base = random.uniform(18, 25)
            else:  # Primavera
                temp_base = random.uniform(20, 30)
            
            # Variación horaria
            if 6 <= hora_dia <= 14:
                temperatura_hora = temp_base + (hora_dia - 6) * 0.8
            elif 14 < hora_dia <= 20:
                temperatura_hora = temp_base + (20 - hora_dia) * 0.4
            else:
                temperatura_hora = temp_base - 2
            
            temperatura_hora += random.uniform(-0.5, 0.5)
            temperatura_hora = max(18.0, min(35.0, temperatura_hora))
            
            # --- TORMENTAS ---
            # Decidir si inicia tormenta (solo si no hay una activa y no pasamos el límite)
            factor_tormenta = 1.0
            if tiempo_tormenta_restante > 0:
                tiempo_tormenta_restante -= 1
                factor_tormenta = random.uniform(1.5, 2.5) # Caos
            else:
                # Probabilidad por hora de iniciar tormenta
                if tormentas_generadas < MAX_TORMENTAS and random.random() < probabilidad_tormenta:
                    tiempo_tormenta_restante = random.randint(2, 6) # Dura 2-6 horas
                    tormentas_generadas += 1
            
            # --- CONSUMO ---
            consumo_total = 0
            for edif in edificios:
                consumo = edif.calcular_consumo(hora_dia, temperatura_hora)
                consumo_total += consumo
            
            # Aplicar Tormenta
            consumo_total *= factor_tormenta
            
            # Verificar blackout
            if consumo_total > capacidad_max:
                resultado.blackouts += 1
            
            # Guardar datos
            resultado.historial_horas.append(consumo_total)
            if hora_dia % 6 == 0:
                resultado.historial_demanda.append((dia_actual, hora_dia, consumo_total, temperatura_hora))
            
            tiempo_actual += 1
            yield env.timeout(1)
    
    env.process(proceso_simulacion())
    env.run()
    
    return resultado

# ============================================================
# OPTIMIZADOR
# ============================================================
def encontrar_mejor_subestacion(edificios: List[Edificio], 
                                dia_actual: int = 0, 
                                hora_actual: int = 0,
                                historial_fallos: Dict[str, int] = None,
                                prob_tormenta: float = 0.0) -> Tuple[str, List[Dict]]:
    """
    Determina la óptima considerando:
    1. Costo Inversión + Operativo
    2. Penalización por Blackouts (evita buscar perfección si es muy cara)
    3. Historial de fallos REALES ya ocurridos
    """
    if historial_fallos is None:
        historial_fallos = {"Pequeña": 0, "Mediana": 0, "Grande": 0}

    resultados = []
    COSTO_HORA_BLACKOUT = 500  # Penalización económica por hora sin luz
    
    print(f"🏆 Iniciando comparación (Día {dia_actual}, Prob Tormenta: {prob_tormenta:.4f})...")
    
    for tipo in ["Pequeña", "Mediana", "Grande"]:
        # Simular futuro
        res = simular_anio(tipo, edificios, dia_actual, hora_actual, prob_tormenta)
        
        # Combinar con pasado real
        fallos_pasados = historial_fallos.get(tipo, 0)
        fallos_totales = fallos_pasados + res.blackouts
        
        # Calcular métricas base
        metricas = res.calcular_metricas()
        
        # --- CÁLCULO DE COSTO AJUSTADO ---
        # Costo Real = Inversión + Operativo + (Multas por Blackout)
        costo_multas = fallos_totales * COSTO_HORA_BLACKOUT
        costo_ajustado = metricas["costo_total"] + costo_multas
        
        # Actualizar métricas con datos combinados
        metricas["blackouts_totales"] = fallos_totales
        metricas["blackouts_futuros"] = res.blackouts
        metricas["fallos_pasados"] = fallos_pasados
        metricas["costo_ajustado"] = costo_ajustado
        metricas["confiabilidad_real"] = max(0, 100 * (1 - (fallos_totales / (365*24))))
        
        resultados.append(metricas)
        print(f"{tipo}: ${metricas['costo_total']:,.0f} + ${costo_multas:,.0f} (Multas) = ${costo_ajustado:,.0f}")

    # Criterio: Menor COSTO AJUSTADO
    # Pero con una restricción mínima de seguridad (95% confiabilidad)
    # 5% de 8760h = ~438 horas. Si falla más de eso, es inaceptable.
    
    candidatos_viables = [r for r in resultados if r["confiabilidad_real"] > 95.0]
    
    if candidatos_viables:
        ganadora = min(candidatos_viables, key=lambda x: x["costo_ajustado"])
    else:
        # Si todas son desastrosas, elegir la menos mala (mayor confiabilidad)
        ganadora = max(resultados, key=lambda x: x["confiabilidad_real"])
    
    print(f"\n ÓPTIMA ELEGIDA: {ganadora['tipo']}")
    
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