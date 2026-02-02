import pygame
import random
import math
from collections import deque
from config import (Palette, SimConfig, SUBESTACIONES_CONFIG, SCREEN_WIDTH, SCREEN_HEIGHT, FPS, 
                   HEADER_RECT, SIDEBAR_RECT, GRAPH_RECT, GRID_RECT,
                   HEADER_HEIGHT, SIDEBAR_WIDTH, GRID_HEIGHT, GRAPH_HEIGHT)
from motor_logico import generar_ciudad, obtener_datos_snapshot, encontrar_mejor_subestacion, Edificio

# ============================================================
# MOTOR DE AUDIO SUAVE (SINE WAVES)
# ============================================================
class SoundEngine:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception as e:
            print(f"Audio desactivado: {e}")

    def play_click(self):
        if not self.enabled: return
        # Clic suave: Tono agudo muy corto con fade out rápido (onda seno)
        self.generate_soft_tone(800, 0.05, 0.1)

    def play_alert(self):
        if not self.enabled: return
        # Alarma suave: Tono medio pulsante, no estridente (onda seno)
        self.generate_soft_tone(400, 0.3, 0.2)

    def generate_soft_tone(self, freq, duration, volume=0.5):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        
        for i in range(n_samples):
            t = i / sample_rate
            # Onda Senoidal pura (más suave que cuadrada)
            val = math.sin(2 * math.pi * freq * t)
            
            # Envelope (Fade Out) para evitar "clicks" al cortar
            envelope = 1.0 - (i / n_samples) 
            val = val * envelope
            
            # Escalar a 16-bit
            val = int(val * 32767 * volume)
            val = max(-32767, min(32767, val))
            
            # Little Endian Stereo
            lb = val & 0xFF
            hb = (val >> 8) & 0xFF
            # L+R
            buf.append(lb); buf.append(hb)
            buf.append(lb); buf.append(hb)
            
        try:
            sound = pygame.mixer.Sound(buffer=bytes(buf))
            sound.set_volume(0.5)
            sound.play()
        except: pass

# ============================================================
# PARTICULAS DE HUMO
# ============================================================
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-1.0, -0.5)
        self.life = 255
        self.size = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 4
        self.size += 0.05
        return self.life > 0

    def draw(self, screen):
        alpha = max(0, min(255, int(self.life)))
        if alpha > 5:
            # Color gris semi-transparente
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 200, 200, alpha//2), (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (self.x - self.size, self.y - self.size))

# ============================================================
# SIMULADOR PRINCIPAL UI
# ============================================================
class SimulacionUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Demanda Energética- Profesional")
        self.clock = pygame.time.Clock()
        self.audio = SoundEngine()
        
        # Estado Lógico
        self.hora = 12
        self.minuto = 0
        self.segundo = 0
        self.dia = 1
        self.temperatura = 28.0
        self.velocidad = SimConfig.SPEED_1X
        self.pausado = False
        
        # Entidades
        self.edificios = generar_ciudad()
        self.particulas = []
        
        # Datos
        self.consumo_total = 0
        self.consumo_smooth = 0
        self.sub_actual = "Mediana"
        self.blackout = False
        self.blackout_prev = False  # Para detectar cambios
        self.blackouts_session = 0  # Contador acumulativo de blackouts en sesión
        self.modo_tormenta = False
        self.tormenta_timer = 0
        self.tormentas_count = 0
        
        # Gráfica (Historial más largo para ver mejor)
        self.history_len = 800 
        self.graph_data = deque([0]*self.history_len, maxlen=self.history_len)
        
        # Luces oficinas
        self.office_state = {}
        for e in self.edificios:
            if e.tipo == 'comercial':
                self.office_state[id(e)] = [[random.choice([True, False]) for _ in range(4)] for _ in range(3)]

        # Fuentes
        self.font_xl = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_lg = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_sl = pygame.font.SysFont("Arial", 14)
        self.font_xs = pygame.font.SysFont("Arial", 11)
        
        self.init_layout()
        self.modal_active = False
        self.modal_data = None

    def init_layout(self):
        sx, sy = SIDEBAR_RECT[0], SIDEBAR_RECT[1]
        
        # Botones Subestaciones
        self.btn_subs = []
        y = sy + 60
        for t in ["Pequeña", "Mediana", "Grande"]:
            r = pygame.Rect(sx + 15, y, SIDEBAR_WIDTH - 30, 65)
            self.btn_subs.append({'id': t, 'rect': r})
            y += 75
            
        # Botón Tormenta (Nuevo)
        self.btn_storm = pygame.Rect(sx + 15, SCREEN_HEIGHT - 130, SIDEBAR_WIDTH - 30, 40)
        
        # Botón Optimizar
        self.btn_opt = pygame.Rect(sx + 15, SCREEN_HEIGHT - 70, SIDEBAR_WIDTH - 30, 50)
        
        # Controles Velocidad (Arriba derecha en Header)
        self.btn_speeds = []
        bx = SCREEN_WIDTH - 180
        for lbl, val in [("1x", SimConfig.SPEED_1X), ("2x", SimConfig.SPEED_2X), ("MAX", SimConfig.SPEED_4X)]:
            r = pygame.Rect(bx, 25, 45, 30)
            self.btn_speeds.append({'lbl': lbl, 'val': val, 'rect': r})
            bx += 50
            
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if self.modal_active:
                    # Detectar clic en el botón cerrar
                    close_btn_width, close_btn_height = 150, 35
                    close_btn_x = (SCREEN_WIDTH - close_btn_width) // 2
                    close_btn_y = (SCREEN_HEIGHT - 600)//2 + 600 - 50  # my + mh - 50
                    
                    close_rect = pygame.Rect(close_btn_x, close_btn_y, close_btn_width, close_btn_height)
                    if close_rect.collidepoint(mx, my):
                        self.modal_active = False
                        self.audio.play_click()
                        return True
                    return True  # Si se hace clic fuera del botón, no cerrar
                
                # Velocidad
                for b in self.btn_speeds:
                    if b['rect'].collidepoint(mx, my):
                        self.velocidad = b['val']
                        self.audio.play_click()
                
                # Subs
                for b in self.btn_subs:
                    if b['rect'].collidepoint(mx, my):
                        self.sub_actual = b['id']
                        self.audio.play_click()
                
                # Tormenta
                if self.btn_storm.collidepoint(mx, my):
                    self.modo_tormenta = True
                    self.tormenta_timer = 300 # 5 segundos de caos
                    self.tormentas_count += 1  # Registrar tormenta
                    self.audio.play_alert() # Sonido inicial
                    
                # Optimizar
                if self.btn_opt.collidepoint(mx, my):
                    self.audio.play_click()
                    self.run_optimization()
        return True

    def run_optimization(self):
        # Guardar la subestación actual antes de la simulación
        subestacion_actual = self.sub_actual
        
        # Loading simple
        self.screen.fill(Palette.BG_DARKEST)
        t = self.font_lg.render("CALCULANDO EFICIENCIA ANUAL...", True, Palette.CYAN)
        tr = t.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(t, tr)
        pygame.display.flip()
        
        best, res = encontrar_mejor_subestacion(self.edificios)
        self.modal_data = (best, res, subestacion_actual)  # Incluir subestación actual
        self.modal_active = True
        self.sub_actual = best

    def update(self):
        if not self.pausado:
            # Tiempo
            steps = 1
            if self.velocidad == SimConfig.SPEED_2X: steps = 2
            if self.velocidad == SimConfig.SPEED_4X: steps = 5
            
            self.minuto += steps
            if self.minuto >= 60:
                self.minuto = 0
                self.hora += 1
                if self.hora >= 24:
                    self.hora = 0
                    self.dia += 1
                    self.temperatura = random.uniform(24.0, 36.0)
            
            self.temperatura += random.uniform(-0.05, 0.05)
            
            # Modo Tormenta (Caos temporal)
            if self.modo_tormenta:
                self.tormenta_timer -= 1
                if self.tormenta_timer <= 0:
                    self.modo_tormenta = False
        
        # Datos
        data = obtener_datos_snapshot(self.edificios, self.hora, self.temperatura)
        raw = data["consumo_total_kw"]
        
        # Efecto Tormenta (Multiplicador aleatorio masivo)
        if self.modo_tormenta:
            raw *= random.uniform(1.5, 2.5)
            
        # Suavizado visual
        diff = raw - self.consumo_smooth
        self.consumo_smooth += diff * 0.15
        self.consumo_total = int(self.consumo_smooth)
        
        # Blackout
        cap = SUBESTACIONES_CONFIG[self.sub_actual]["capacidad_kw"]
        self.blackout = self.consumo_total > cap
        
        # Contar blackouts acumulativos (solo cuando inicia)
        if self.blackout and not self.blackout_prev:
            self.blackouts_session += 1
        self.blackout_prev = self.blackout
        
        if self.blackout and random.random() < 0.02:
            self.audio.play_alert()
            
        self.graph_data.append(self.consumo_total)
        
        # Partículas
        for e in self.edificios:
            if e.tipo == 'industrial':
                # Humo proporcional al consumo
                act = e.consumo_actual
                if self.modo_tormenta: act *= 2
                
                if random.random() < (act / 100000.0):
                    self.particulas.append(Particle(e.rect.right-10, e.rect.top))
                    
        self.particulas = [p for p in self.particulas if p.update()]
        
        # Luces oficinas
        if random.random() < 0.1:
            for k in self.office_state:
                r = random.randint(0,2); c = random.randint(0,3)
                self.office_state[k][r][c] = not self.office_state[k][r][c]

    def draw(self):
        self.screen.fill(Palette.BG_DARKEST)
        
        # Alarma visual ambiente (Flash Rojo o Azul en Tormenta)
        if self.blackout:
             if (pygame.time.get_ticks()//300)%2==0:
                 s = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
                 s.fill((60,0,0))
                 self.screen.blit(s,(0,0), special_flags=pygame.BLEND_ADD)
        elif self.modo_tormenta:
             if random.random() < 0.1: # Relámpagos
                 s = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
                 s.fill((50,50,70))
                 self.screen.blit(s,(0,0), special_flags=pygame.BLEND_ADD)

        self.draw_header()
        self.draw_sidebar()
        self.draw_grid()
        self.draw_graph()
        self.draw_particles()
        # Legend moved to sidebar
        
        if self.modal_active:
            self.draw_modal()
            
        pygame.display.flip()

    def draw_header(self):
        r = HEADER_RECT
        pygame.draw.rect(self.screen, Palette.BG_HEADER, r)
        pygame.draw.line(self.screen, Palette.CYAN, (0, r[3]), (SCREEN_WIDTH, r[3]), 2)
        
        # Título en ESPAÑOL
        self.screen.blit(self.font_lg.render("SIMULADOR DE DEMANDA DE ENERGÍA", True, Palette.CYAN), (25, 25))
        
        # Info Estado (texto simple sin iconos)
        info = f"DÍA {self.dia} | {self.hora:02d}:{self.minuto:02d} | {self.temperatura:.1f}°C"
        self.screen.blit(self.font_xl.render(info, True, Palette.AMBER), (25, 48))
        
        # Consumo Central con icono ⚡
        cx = SCREEN_WIDTH // 2 - 50
        lbl = self.font_md.render(" CONSUMO TOTAL", True, Palette.GRAY)
        self.screen.blit(lbl, (cx, 20))
        
        col = Palette.NEON_RED if self.blackout else Palette.CYAN_GLOW
        val = self.font_xl.render(f"  {self.consumo_total:,} kW", True, col)
        self.screen.blit(val, (cx, 40))
        
        # Botones Velocidad
        for b in self.btn_speeds:
            act = (self.velocidad == b['val'])
            bg = Palette.CYAN if act else Palette.BG_PANEL
            pygame.draw.rect(self.screen, bg, b['rect'], border_radius=4)
            c_txt = (0,0,0) if act else Palette.WHITE
            
            lbl = self.font_sl.render(b['lbl'], True, c_txt)
            tr = lbl.get_rect(center=b['rect'].center)
            self.screen.blit(lbl, tr)


    def draw_sidebar(self):
        r = SIDEBAR_RECT
        pygame.draw.rect(self.screen, Palette.BG_SIDEBAR, r)
        pygame.draw.line(self.screen, Palette.CYAN, (r[0], r[1]), (r[0], SCREEN_HEIGHT), 2)
        sx, sy = r[0], r[1]
        
        self.screen.blit(self.font_lg.render("CONTROL DE RED", True, Palette.CYAN), (sx+20, sy+20))
        
        # Barra Carga
        cap = SUBESTACIONES_CONFIG[self.sub_actual]["capacidad_kw"]
        pct = min(1.0, self.consumo_total / cap)
        
        by = sy + 50
        pygame.draw.rect(self.screen, (20,20,30), (sx+20, by-5, SIDEBAR_WIDTH-40, 15)) # Background track
        col = Palette.NEON_GREEN if pct < 0.7 else (Palette.AMBER if pct < 0.9 else Palette.NEON_RED)
        pygame.draw.rect(self.screen, col, (sx+20, by-5, int((SIDEBAR_WIDTH-40)*pct), 15))
        
        self.screen.blit(self.font_sl.render(f"CARGA: {int(pct*100)}%", True, Palette.WHITE), (sx+20, by+10))

        # Botones Subs
        for b in self.btn_subs:
            tid = b['id']
            cfg = SUBESTACIONES_CONFIG[tid]
            act = (self.sub_actual == tid)
            
            bg = cfg['color'] if act else Palette.BG_PANEL
            pygame.draw.rect(self.screen, bg, b['rect'], border_radius=6)
            if act: pygame.draw.rect(self.screen, Palette.WHITE, b['rect'], 2, border_radius=6)
            
            ct = (0,0,0) if act else Palette.WHITE
            self.screen.blit(self.font_lg.render(tid, True, ct), (b['rect'].x+10, b['rect'].y+8))
            self.screen.blit(self.font_sl.render(f"{cfg['capacidad']} | ${cfg['costo']//1000}k", True, ct), (b['rect'].x+10, b['rect'].y+35))

        # LEYENDA (En el espacio vacío entre Subs y Tormenta)
        ly = sy + 300
        self.screen.blit(self.font_md.render("LEYENDA EDIFICIOS", True, Palette.CYAN), (sx+20, ly))
        
        items = [("Residencial", Palette.RESIDENCIAL), 
                 ("Comercial", Palette.COMERCIAL), 
                 ("Industrial", Palette.INDUSTRIAL)]
        
        ly += 30
        for name, col in items:
            pygame.draw.rect(self.screen, col, (sx+20, ly, 20, 20), border_radius=4)
            self.screen.blit(self.font_sl.render(name, True, Palette.GRAY), (sx+50, ly+2))
            ly += 30

        # Botón Tormenta
        scol = (100, 50, 50) if not self.modo_tormenta else (200, 50, 50)
        pygame.draw.rect(self.screen, scol, self.btn_storm, border_radius=5)
        
        st_txt = self.font_md.render("MODO TORMENTA", True, Palette.WHITE)
        
        tr = st_txt.get_rect(center=self.btn_storm.center)
        self.screen.blit(st_txt, tr)

        # Botón Optimizar
        pygame.draw.rect(self.screen, Palette.NEON_GREEN, self.btn_opt, border_radius=8)
        ot = self.font_md.render("CALCULAR ÓPTIMO", True, (0,0,0))
        tr = ot.get_rect(center=self.btn_opt.center)
        self.screen.blit(ot, tr)

    def draw_grid(self):
        for e in self.edificios:
            x, y, w, h = e.rect
            act = e.consumo_actual / (e.poblacion * 2.5) if e.poblacion else 0
            is_on = act > 0.2
            
            # Glow aura
            if is_on:
                s = pygame.Surface((w+10, h+10), pygame.SRCALPHA)
                c_aura = (*Palette.AMBER, 50) if e.tipo == 'residencial' else ((*Palette.CYAN, 40))
                pygame.draw.rect(s, c_aura, (0,0,w+10,h+10), border_radius=10)
                self.screen.blit(s, (x-5, y-5))

            if e.tipo == 'residencial': # Casa
                c = Palette.RESIDENCIAL
                pygame.draw.rect(self.screen, c, (x+5, y+10, w-10, h-10))
                # Techo
                pygame.draw.polygon(self.screen, (100, 180, 255), [(x, y+10), (x+w/2, y), (x+w, y+10)])
                if is_on: # Ventana amarilla
                    pygame.draw.rect(self.screen, (255,255,100), (x+w/2-4, y+15, 8, 8))
                    
            elif e.tipo == 'comercial': # Oficina
                c = Palette.COMERCIAL
                pygame.draw.rect(self.screen, c, (x+6, y+4, w-12, h-4))
                # Ventanas dinámicas
                st = self.office_state.get(id(e))
                cw, ch = (w-16)/4, (h-10)/3
                for r in range(3):
                    for c in range(4):
                        col_win = (200,255,200) if (st[r][c] and is_on) else (30,50,30)
                        pygame.draw.rect(self.screen, col_win, (x+8+c*cw, y+6+r*ch, cw-1, ch-1))
                        
            elif e.tipo == 'industrial': # Fabrica
                c = Palette.INDUSTRIAL
                pygame.draw.rect(self.screen, c, (x+3, y+15, w-6, h-15))
                pygame.draw.rect(self.screen, (120,80,80), (x+w-12, y, 8, 15)) # Chimenea
                # Dientes
                p = [(x+3, y+15), (x+10, y+5), (x+10,y+15), (x+17,y+5), (x+17,y+15)]
                pygame.draw.lines(self.screen, (200,100,100), False, p, 2)

    def draw_particles(self):
        for p in self.particulas:
            p.draw(self.screen)

    def draw_graph(self):
        # Gráfica Tipo "Área" con degradado y smooth
        gx, gy, gw, gh = GRAPH_RECT
        # Background
        pygame.draw.rect(self.screen, (10,12,20), GRAPH_RECT)
        pygame.draw.rect(self.screen, Palette.GRAY, GRAPH_RECT, 2)
        
        # Grid visual
        for i in range(1,4):
            ly = gy + i*(gh/4)
            pygame.draw.line(self.screen, (30,40,50), (gx, ly), (gx+gw, ly))
            
        if len(self.graph_data) < 2: return
        
        cap = SUBESTACIONES_CONFIG[self.sub_actual]["capacidad_kw"]
        mx = max(cap*1.1, max(self.graph_data)*1.1, 1000)
        
        pts = []
        step = gw / (len(self.graph_data)-1)
        
        for i, val in enumerate(self.graph_data):
            px = gx + i*step
            py = (gy+gh) - ((val / mx) * gh)
            pts.append((px, int(py)))
            
        # Draw Area (Cyan transparente)
        poly = pts + [(pts[-1][0], gy+gh), (pts[0][0], gy+gh)]
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*Palette.CYAN, 50), poly)
        self.screen.blit(s, (0,0))
        
        # Draw Line
        pygame.draw.lines(self.screen, Palette.CYAN, False, pts, 2)
        
        # Draw Cap Line
        cpy = (gy+gh) - ((cap/mx)*gh)
        pygame.draw.line(self.screen, Palette.NEON_RED, (gx, cpy), (gx+gw, cpy), 2)
        self.screen.blit(self.font_sl.render(f"LÍMITE: {cap//1000} MW", True, Palette.NEON_RED), (gx+10, cpy-15))

        # Leyenda fija para el gráfico (esquina derecha)
        legend_x = gx + gw - 220



    def draw_modal(self):
        # Modal simplificado con mejor espaciado
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,200))
        self.screen.blit(s, (0,0))

        mw, mh = 800, 600
        mx, my = (SCREEN_WIDTH-mw)//2, (SCREEN_HEIGHT-mh)//2
        pygame.draw.rect(self.screen, Palette.BG_PANEL, (mx, my, mw, mh), border_radius=12)
        pygame.draw.rect(self.screen, Palette.CYAN, (mx, my, mw, mh), 2, border_radius=12)

        win, res, current_sub = self.modal_data

        # Título principal
        title = self.font_xl.render(f"SUBESTACIÓN ÓPTIMA: {win.upper()}", True, Palette.NEON_GREEN)
        tr = title.get_rect(center=(SCREEN_WIDTH//2, my + 35))
        self.screen.blit(title, tr)

        # Subtítulo con subestación actual
        subtitle = self.font_md.render(f"Simulación realizada con subestación: {current_sub}", True, Palette.AMBER)
        sr = subtitle.get_rect(center=(SCREEN_WIDTH//2, my + 65))
        self.screen.blit(subtitle, sr)

        # Mostrar cada subestación en columnas ordenadas
        col_width = 220
        start_x = mx + 40
        start_y = my + 90

        for i, r in enumerate(res):
            col_x = start_x + (i * col_width)
            is_winner = r['tipo'] == win
            is_current = r['tipo'] == current_sub  # Subestación usada en la simulación

            # Nombre de subestación
            color = Palette.NEON_GREEN if is_winner else Palette.WHITE
            name_text = f"{r['tipo']} ({r['capacidad_mw']} MW)"
            self.screen.blit(self.font_lg.render(name_text, True, color), (col_x, start_y))

            # Indicadores
            indicator_y = start_y + 28
            if is_winner:
                winner_text = self.font_sl.render("✓ RECOMENDADA", True, Palette.NEON_GREEN)
                self.screen.blit(winner_text, (col_x, indicator_y))
                indicator_y += 18
            
            if is_current:
                current_text = self.font_sl.render("x ACTUAL", True, Palette.AMBER)
                self.screen.blit(current_text, (col_x, indicator_y))

            # Estadísticas principales
            stats_y = start_y + 70  # Ajustado para dar espacio a los indicadores
            
            # Ajustar valores para la subestación actual basada en blackouts de sesión
            costo = r['costo_total']
            blackouts = r['blackouts']
            confiabilidad = r['confiabilidad']
            eficiencia = r['eficiencia']
            
            if is_current and self.blackouts_session > 0:
                # Calcular horas totales (simulación + sesión)
                horas_simulacion = 365 * 24
                horas_session = (self.dia - 1) * 24 + self.hora + self.minuto / 60.0
                horas_totales = horas_simulacion + horas_session
                
                # Blackouts totales
                blackouts_total = r['blackouts'] + self.blackouts_session
                
                # Recalcular confiabilidad (más sensible a blackouts)
                downtime_ratio = blackouts_total / horas_totales
                confiabilidad = max(0, (1 - downtime_ratio * 10) * 100)  # Factor 10x más penalizante
                
                # Mantener eficiencia igual (no se recalcula fácilmente en tiempo real)
                blackouts = blackouts_total
            
            stats = [
                f"Costo: ${costo:,.0f}",
                f"Blackouts: {blackouts}h",
                f"Confiabilidad: {confiabilidad:.1f}%",
                f"Eficiencia: {eficiencia:.1f}%"
            ]

            for stat in stats:
                self.screen.blit(self.font_md.render(stat, True, Palette.GRAY), (col_x, stats_y))
                stats_y += 25

            # Barra de confiabilidad visual
            bar_y = stats_y + 15
            bar_width = 180
            bar_height = 26
            conf_pct = confiabilidad / 100

            # Background bar
            pygame.draw.rect(self.screen, (40,40,50), (col_x, bar_y, bar_width, bar_height), border_radius=8)
            # Fill bar
            fill_color = Palette.NEON_GREEN if conf_pct > 0.95 else (Palette.AMBER if conf_pct > 0.8 else Palette.NEON_RED)
            pygame.draw.rect(self.screen, fill_color, (col_x, bar_y, int(bar_width * conf_pct), bar_height), border_radius=8)

            # Percentage text
            pct_text = f"{confiabilidad:.1f}%"
            pt = self.font_sl.render(pct_text, True, Palette.WHITE)
            self.screen.blit(pt, (col_x + bar_width//2 - 20, bar_y + 2))


        # Resumen comparativo abajo
        summary_y = my + 380
        pygame.draw.line(self.screen, Palette.CYAN, (mx + 30, summary_y), (mx + mw - 30, summary_y), 1)

        summary_title = self.font_md.render("RESUMEN DE ANÁLISIS", True, Palette.CYAN)
        self.screen.blit(summary_title, (mx + 40, summary_y + 15))

        # Calcular estadísticas simples
        total_blackouts = sum(r['blackouts'] for r in res)
        best_conf = max(r['confiabilidad'] for r in res)
        worst_conf = min(r['confiabilidad'] for r in res)
        
        # Estadísticas de la sesión actual
        horas_session = (self.dia - 1) * 24 + self.hora + self.minuto / 60.0
        if horas_session > 0:
            downtime_session = self.blackouts_session / horas_session
            confiabilidad_session = max(0, (1 - downtime_session * 10) * 100)
        else:
            confiabilidad_session = 100.0

        summary_lines = [
            f"Tormentas simuladas: {self.tormentas_count}",
            f"Subestación seleccionada: {current_sub}",
            f"Blackouts en sesión: {self.blackouts_session} horas",
            f"Confiabilidad sesión: {confiabilidad_session:.1f}% ({horas_session:.1f}h simuladas)"
        ]

        for i, line in enumerate(summary_lines):
            self.screen.blit(self.font_sl.render(line, True, Palette.GRAY), (mx + 40, summary_y + 40 + i * 20))

        # Gráfico de torta único: distribución del promedio de demanda entre subestaciones
        try:
            sizes = [float(r.get('promedio_demanda_kw', 0)) for r in res]
            total = sum(sizes)
            pie_size = 140
            pie_surf = pygame.Surface((pie_size, pie_size), pygame.SRCALPHA)
            cx_p = cy_p = pie_size // 2

            if total > 0:
                start_angle = -90.0
                for idx, s in enumerate(sizes):
                    pct = s / total
                    end_angle = start_angle + pct * 360.0
                    pts = [(cx_p, cy_p)]
                    steps = max(6, int(abs(end_angle - start_angle) / 6))
                    a = start_angle
                    while a <= end_angle:
                        rad = math.radians(a)
                        x = cx_p + math.cos(rad) * (pie_size // 2)
                        y = cy_p + math.sin(rad) * (pie_size // 2)
                        pts.append((x, y))
                        a += max(1.0, abs(end_angle - start_angle) / steps)
                    color = SUBESTACIONES_CONFIG[res[idx]['tipo']]['color']
                    pygame.draw.polygon(pie_surf, color, pts)
                    start_angle = end_angle
            else:
                pygame.draw.circle(pie_surf, (80,80,80), (cx_p, cy_p), pie_size//2)

            pygame.draw.circle(pie_surf, Palette.BG_PANEL, (cx_p, cy_p), pie_size//2, 2)

            pie_x = mx + mw - pie_size - 40
            pie_y = summary_y + 30
            self.screen.blit(pie_surf, (pie_x, pie_y))

            # Leyenda al lado del pie (colores = subestaciones)
            lx = pie_x - 170
            base_ly = pie_y
            self.screen.blit(self.font_sl.render("Leyenda (colores = subestaciones):", True, Palette.CYAN), (lx, base_ly))
            for idx, r_ in enumerate(res):
                perc = 0.0 if total == 0 else (sizes[idx] / total) * 100.0
                txt = f"{r_['tipo']}: {int(sizes[idx]):,} kW ({perc:.0f}%)"
                y = base_ly + 18 + idx * 18
                # Caja de color
                col_box = SUBESTACIONES_CONFIG[r_['tipo']]['color']
                pygame.draw.rect(self.screen, col_box, (lx, y, 12, 12), border_radius=3)
                self.screen.blit(self.font_sl.render(txt, True, Palette.WHITE), (lx + 18, y))
        except Exception:
            pass

        # Botón cerrar
        close_btn_width, close_btn_height = 150, 35
        close_btn_x = (SCREEN_WIDTH - close_btn_width) // 2
        close_btn_y = my + mh - 50

        pygame.draw.rect(self.screen, Palette.NEON_GREEN, (close_btn_x, close_btn_y, close_btn_width, close_btn_height), border_radius=6)
        close_text = self.font_md.render("CERRAR", True, (0,0,0))
        ct_rect = close_text.get_rect(center=(close_btn_x + close_btn_width//2, close_btn_y + close_btn_height//2))
        self.screen.blit(close_text, ct_rect)

if __name__ == "__main__":
    app = SimulacionUI()
    r = True
    while r:
        r = app.handle_events()
        app.update()
        app.draw()
        app.clock.tick(FPS)
    pygame.quit()