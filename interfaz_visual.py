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
        pygame.display.set_caption("Simulador de Demanda Energética - Profesional")
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
        self.modo_tormenta = False
        self.tormenta_timer = 0
        
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
                    self.modal_active = False
                    self.audio.play_click()
                    return True
                
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
                    self.audio.play_alert() # Sonido inicial
                    
                # Optimizar
                if self.btn_opt.collidepoint(mx, my):
                    self.audio.play_click()
                    self.run_optimization()
        return True

    def run_optimization(self):
        # Loading simple
        self.screen.fill(Palette.BG_DARKEST)
        t = self.font_lg.render("CALCULANDO EFICIENCIA ANUAL...", True, Palette.CYAN)
        tr = t.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(t, tr)
        pygame.display.flip()
        
        best, res = encontrar_mejor_subestacion(self.edificios)
        self.modal_data = (best, res)
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
        
        # Info Estado
        info = f"DÍA {self.dia} | {self.hora:02d}:{self.minuto:02d} | {self.temperatura:.1f}°C"
        self.screen.blit(self.font_xl.render(info, True, Palette.AMBER), (25, 50))
        
        # Consumo Central
        cx = SCREEN_WIDTH // 2 - 50
        lbl = self.font_md.render("CONSUMO TOTAL", True, Palette.GRAY)
        self.screen.blit(lbl, (cx, 20))
        
        col = Palette.NEON_RED if self.blackout else Palette.CYAN_GLOW
        val = self.font_xl.render(f"{self.consumo_total:,} kW", True, col)
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



    def draw_modal(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,200)) # Dim background
        self.screen.blit(s, (0,0))
        
        mw, mh = 650, 450
        mx, my = (SCREEN_WIDTH-mw)//2, (SCREEN_HEIGHT-mh)//2
        pygame.draw.rect(self.screen, Palette.BG_PANEL, (mx, my, mw, mh), border_radius=12)
        pygame.draw.rect(self.screen, Palette.CYAN, (mx, my, mw, mh), 2, border_radius=12)
        
        win, res = self.modal_data
        
        self.screen.blit(self.font_lg.render(f"MEJOR SUBESTACIÓN: {win.upper()}", True, Palette.NEON_GREEN), (mx+30, my+30))
        
        ty = my+90
        for r in res:
            color = Palette.NEON_GREEN if r['tipo'] == win else Palette.WHITE
            txt = f"{r['tipo']}: ${r['costo_total']:,} | Apagones: {r['blackouts']}h | Efic: {r['eficiencia']:.1f}%"
            self.screen.blit(self.font_md.render(txt, True, color), (mx+30, ty))
            ty += 50
            
        self.screen.blit(self.font_sl.render("[CLIC PARA CERRAR]", True, Palette.GRAY), (mx+mw/2-60, my+mh-40))

if __name__ == "__main__":
    app = SimulacionUI()
    r = True
    while r:
        r = app.handle_events()
        app.update()
        app.draw()
        app.clock.tick(FPS)
    pygame.quit()