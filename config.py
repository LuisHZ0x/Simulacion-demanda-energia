import pygame

# ============================================================
# DIMENSIONES DE PANTALLA (Ajustado a 1100x750)
# ============================================================
SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800
FPS = 60

# ============================================================
# LAYOUT (Systema de Rects)
# ============================================================
# Cabecera
HEADER_HEIGHT = 90
HEADER_RECT = (0, 0, SCREEN_WIDTH, HEADER_HEIGHT)

# Sidebar (Derecha, pegado al borde)
SIDEBAR_WIDTH = 260
SIDEBAR_X = SCREEN_WIDTH - SIDEBAR_WIDTH
SIDEBAR_RECT = (SIDEBAR_X, HEADER_HEIGHT, SIDEBAR_WIDTH, SCREEN_HEIGHT - HEADER_HEIGHT)

# Área Principal (Resto del ancho)
MAIN_AREA_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH

# Gráfico (Abajo izquierda)
GRAPH_HEIGHT = 180
GRAPH_RECT = (0, SCREEN_HEIGHT - GRAPH_HEIGHT, MAIN_AREA_WIDTH, GRAPH_HEIGHT)

# Grid (Espacio restante entre Header y Graph)
GRID_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - GRAPH_HEIGHT
GRID_RECT = (0, HEADER_HEIGHT, MAIN_AREA_WIDTH, GRID_HEIGHT)

# Configuración Grid Sólida
GRID_FILAS = 8
GRID_COLUMNAS = 9
GRID_MARGIN_X = 30
GRID_MARGIN_Y = 15

# ============================================================
# PALETA DE COLORES (NEON VIBRANTE)
# ============================================================
class Palette:
    # Fondos profundos
    BG_DARKEST = (5, 8, 16)          # Background principal
    BG_HEADER = (10, 15, 25)         # Header background
    BG_SIDEBAR = (12, 18, 30)        # Sidebar background
    BG_PANEL = (20, 26, 40)          # Paneles internos
    
    # Colores Neón
    CYAN = (0, 240, 255)             # Energía Global
    CYAN_GLOW = (0, 255, 255)        # Brillo máximo
    
    MAGENTA = (255, 0, 255)          # Industrial / Alta tensión
    NEON_RED = (255, 40, 40)         # Alerta Blackout
    NEON_GREEN = (0, 255, 100)       # Eficiencia / Eco
    AMBER = (255, 180, 0)            # Temperatura / Warn
    
    # Texto
    WHITE = (255, 255, 255)
    GRAY = (150, 160, 170)
    DARK_GRAY = (60, 70, 80)
    
    # Edificios
    RESIDENCIAL = (0, 180, 255)      # Azul claro
    COMERCIAL = (50, 220, 100)       # Verde vivo
    INDUSTRIAL = (255, 80, 80)       # Rojo rosado

# ============================================================
# CONFIGURACIÓN DE SIMULACIÓN
# ============================================================
class SimConfig:
    SPEED_PAUSED = 0
    SPEED_1X = 60       
    SPEED_2X = 30       
    SPEED_4X = 15       
    
    TEMP_MIN = 18.0
    TEMP_MAX = 35.0

# ============================================================
# DATOS SUBESTACIONES
# ============================================================
SUBESTACIONES_CONFIG = {
    "Pequeña": {
        "color": Palette.AMBER,
        "capacidad": "55 MW",
        "capacidad_kw": 55000,
        "costo": 50000,
        "icono": "⚡"
    },
    "Mediana": {
        "color": Palette.CYAN,
        "capacidad": "110 MW",
        "capacidad_kw": 110000,
        "costo": 120000,
        "icono": "🔋"
    },
    "Grande": {
        "color": Palette.MAGENTA,
        "capacidad": "220 MW",
        "capacidad_kw": 220000,
        "costo": 250000,
        "icono": "🏭"
    }
}