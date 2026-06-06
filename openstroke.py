import tkinter as tk
from pynput import mouse
import ctypes
import os
import threading
import yaml
import time
from PIL import Image, ImageDraw, ImageEnhance
import math
import pystray
import traceback
import win32com.client  # Para hablar con el sistema nervioso de Windows
import urllib.parse     # Para limpiar el texto de las rutas
import pythoncom

import win32gui
import win32process
import psutil # ¡NUEVO! Para sacar el nombre exacto del .exe
import subprocess # Asegúrate de tener esto arriba del todo del archivo
import sys
import keyboard
import string  # Importamos el abecedario nativo de Python

# ==========================================
# MODO DEBUG (Resurrección de la Consola)
# ==========================================
if "--debug" in sys.argv:
    try:
        # 1. Obligamos a Windows a fabricar una consola en vivo
        ctypes.windll.kernel32.AllocConsole()

        # 2. Reconectamos los cables de texto (stdout y stderr) a la nueva consola
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)

        print("========================================")
        print("🛠️ OPENSTROKE: MODO DEBUG ACTIVADO")
        print("========================================")
    except Exception as e:
        pass
# ==========================================

# ==========================================
# EL RASTREADOR DE RECURSOS (Soporte PyInstaller)
# ==========================================
def ruta_recurso(relative_path):
    """Obtiene la ruta absoluta al recurso, ya sea en desarrollo o compilado en el .exe"""
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no estamos en el .exe, usamos la ruta normal de la carpeta
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# ==========================================

# --- IMPORTACIÓN DE NUESTROS MÓDULOS AISLADOS ---
from motor_geometrico import ReconocedorGestos
from configuracion import VentanaConfiguracion

# --- SOPORTE DPI ALTO ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


class OpenStrokeApp:


    def __init__(self):
        print("Iniciando OpenStroke v.0.4.9.6 Alpha....")
        self.root = tk.Tk()
        self.root.withdraw()  # 1. Nos ocultamos en las sombras inmediatamente

        # ==========================================
        # EL MOTOR DE RUTAS (PORTABLE VS INSTALADO)
        # ==========================================
        # 1. Averiguamos dónde está nuestro .exe o .py físicamente
        if getattr(sys, 'frozen', False):
            # Si estamos compilados con PyInstaller
            carpeta_local = os.path.dirname(sys.executable)
        else:
            # Si estamos ejecutando desde PyCharm
            carpeta_local = os.path.dirname(os.path.abspath(__file__))

        # 2. Buscamos la bandera "portable.txt" a nuestro lado
        self.modo_portable = os.path.exists(os.path.join(carpeta_local, "portable.txt"))

        if self.modo_portable:
            print("🎒 MODO PORTABLE DETECTADO: Guardando datos en la carpeta local.")
            carpeta_datos = carpeta_local
        else:
            print("🏠 MODO INSTALADO: Guardando datos en AppData.")
            carpeta_datos = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), "OpenStroke")
            if not os.path.exists(carpeta_datos):
                try:
                    os.makedirs(carpeta_datos)
                except Exception as e:
                    print(f"Error al crear la carpeta en AppData: {e}")

        # 3. Fijamos la ruta definitiva de nuestro cerebro
        self.ruta_yaml = os.path.join(carpeta_datos, "gestos.yaml")
        # ==========================================

        self.motor = ReconocedorGestos()

        # Inicialización de variables de estado
        self.offset_x = ctypes.windll.user32.GetSystemMetrics(76)
        self.offset_y = ctypes.windll.user32.GetSystemMetrics(77)
        self.presionado = False
        self.gesto_activado = False
        self.gesto_cancelado = False
        self.puntos = []
        self.pos_inicial = (0, 0)
        self.tiempo_inicio = 0
        self.pausado = False
        self.simulando_clic = False

        self.modificador_actual = 'default'
        self.color_trazo_actual = '#FF0000'
        self.boton_presionado = None
        self.mouse_controller = mouse.Controller()

        # Variables que luego rellenará el YAML
        self.plantillas = {}
        self.gestos_globales = {}
        self.gestos_app = {}
        self.excepciones = []

        self.tiempo_maximo_s = 3.0
        self.color_linea = "#FF0000"
        self.grosor_linea = 4
        self.umbral_tolerancia = 0.35

        # Cargamos los ajustes (Aquí se decide si es la 'primera_vez')
        self.cargar_configuracion()

        # Construimos el icono de la bandeja del sistema (Systray)
        self.icon = None
        self.setup_tray()

        # Arrancamos el radar del ratón
        self.listener = mouse.Listener(on_click=self.al_hacer_clic, on_move=self.al_mover)
        self.listener.start()

        self.verificar_timeout()
        self.root.protocol("WM_DELETE_WINDOW", self.salir_total)

        # ==========================================
        # EL DESVÍO INTELIGENTE (Arranque Delegado)
        # ==========================================
        if getattr(self, 'primera_vez', False) or getattr(self, 'mostrar_splash', False):
            self.mostrar_splash_screen()
        else:
            self.arrancar_lienzo_principal()

        print("¡Módulo Jedi cargado! Haz clic derecho en Maximizar o Minimizar.")
        self.root.mainloop()

    def arrancar_lienzo_principal(self):
        """Construye y despliega el lienzo invisible maestro"""
        w = ctypes.windll.user32.GetSystemMetrics(78)
        h = ctypes.windll.user32.GetSystemMetrics(79)
        x_start = ctypes.windll.user32.GetSystemMetrics(76)
        y_start = ctypes.windll.user32.GetSystemMetrics(77)

        self.root.geometry(f"{w}x{h}+{x_start}+{y_start}")

        # ==========================================
        # ¡LA CURA! Añadimos "-toolwindow", True
        # ==========================================
        self.root.attributes("-topmost", True, "-transparentcolor", "white", "-toolwindow", True)
        self.root.config(bg="white")
        self.root.overrideredirect(True)

        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.deiconify()  # Salimos de las sombras

    def mostrar_splash_screen(self):
        """Ventana independiente super ligera para la pantalla de carga"""
        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        splash.config(bg="#1E1E1E")

        try:
            from PIL import Image, ImageTk
            ruta_img = ruta_recurso("splash.jpg")
            img = Image.open(ruta_img)
            # Redimensionado inteligente (cambia los números si la quieres más grande o pequeña)
            img.thumbnail((600, 350), Image.Resampling.LANCZOS)
            self.logo_splash = ImageTk.PhotoImage(img)
            tk.Label(splash, image=self.logo_splash, bg="#1E1E1E").pack(padx=2, pady=2)
        except Exception as e:
            tk.Label(splash, text="🚀 OPENSTROKE", font=("Segoe UI", 30, "bold"), fg="white", bg="#1E1E1E").pack(padx=50,
                                                                                                                pady=50)

        # Centramos la imagen milimétricamente en el monitor
        splash.update_idletasks()
        w_splash = splash.winfo_width()
        h_splash = splash.winfo_height()
        w_pantalla = splash.winfo_screenwidth()
        h_pantalla = splash.winfo_screenheight()
        x = (w_pantalla // 2) - (w_splash // 2)
        y = (h_pantalla // 2) - (h_splash // 2)
        splash.geometry(f"+{x}+{y}")

        def terminar_splash():
            splash.destroy()  # Aniquilamos la pantalla de carga
            self.arrancar_lienzo_principal()  # Despertamos al lienzo maestro

        # 2500 milisegundos (2.5 segundos) de espera antes de arrancar
        self.root.after(2500, terminar_splash)

    # ==========================================
    # LOS PODERES JEDI (MANIPULACIÓN NATIVA)
    # ==========================================
    def fijar_ventana(self, hwnd):
        """Activa o desactiva el 'Always on Top'"""
        GWL_EXSTYLE = -20
        WS_EX_TOPMOST = 0x00000008

        # ¡LA CURA DEL BUG! Forzamos a Python a usar Punteros de 64 bits (c_void_p)
        HWND_TOPMOST = ctypes.c_void_p(-1)
        HWND_NOTOPMOST = ctypes.c_void_p(-2)

        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001

        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        if ex_style & WS_EX_TOPMOST:
            # Si ya está fijada, la soltamos
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            print("⚓ Ventana liberada (Normal)")
        else:
            # Si es normal, la fijamos arriba
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            print("📌 Ventana fijada (Always on Top)")

    def hacer_transparente(self, hwnd):
        """Activa o desactiva el modo Fantasma (50% opacidad)"""
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        LWA_ALPHA = 0x00000002

        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if ex_style & WS_EX_LAYERED:
            # Le quitamos el estado fantasma
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_LAYERED)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
            print("👻 Transparencia desactivada")
        else:
            # La volvemos translúcida (150 sobre 255 de opacidad)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 150, LWA_ALPHA)
            print("👻 Transparencia activada (50%)")

    def teletransportar_ruta(self):
        """Lee la carpeta activa de fondo e inyecta la ruta en la ventana actual usando Z-Order"""
        print("🌌 Intentando teletransporte de ruta (Estilo Listary)...")
        try:
            import pythoncom
            pythoncom.CoInitialize()

            import win32com.client
            import urllib.parse
            import keyboard as kb
            import time
            import os
            import win32gui  # ¡NUEVO! Nuestro escáner de la dimensión Z

            # 1. FASE DE RECOLECCIÓN: Guardamos todas las carpetas y sus DNIs (HWND)
            shell = win32com.client.Dispatch("Shell.Application")
            carpetas_abiertas = {}

            for win in shell.Windows():
                try:
                    if os.path.basename(win.FullName).upper() == "EXPLORER.EXE":
                        hwnd = win.HWND
                        ruta_bruta = win.LocationURL
                        if ruta_bruta:
                            ruta_limpia = urllib.parse.unquote(ruta_bruta)
                            if ruta_limpia.startswith("file:///"):
                                ruta_final = ruta_limpia.replace("file:///", "").replace("/", "\\")
                            elif ruta_limpia.startswith("file:"):
                                ruta_final = ruta_limpia.replace("file:", "").replace("/", "\\")
                            else:
                                continue
                            carpetas_abiertas[hwnd] = ruta_final
                except Exception:
                    pass  # Si una ventana da error, pasamos a la siguiente en silencio

            if not carpetas_abiertas:
                print("⚠️ No hay ninguna ventana del Explorador abierta de fondo.")
                return

            # 2. FASE DE ESCANEO Z-ORDER: Leemos la pila de ventanas de arriba a abajo
            hwnds_en_orden = []

            # Esta sub-función es un "callback". Windows nos irá pasando las ventanas una a una.
            def escanear_ventana(hwnd, lista_hwnds):
                if win32gui.IsWindowVisible(hwnd):  # Solo nos interesan las que no están ocultas
                    lista_hwnds.append(hwnd)
                return True

            win32gui.EnumWindows(escanear_ventana, hwnds_en_orden)

            # 3. EL CRUCE DE DATOS: Buscamos el primer DNI que coincida
            ruta_objetivo = None
            for hwnd in hwnds_en_orden:
                if hwnd in carpetas_abiertas:
                    ruta_objetivo = carpetas_abiertas[hwnd]
                    break  # ¡Lo encontramos! Detenemos la búsqueda.

            if ruta_objetivo:
                print(f"📍 Ruta capturada (Z-Order): {ruta_objetivo}")

                # Inyectamos los atajos de teclado
                kb.send('ctrl+l')
                time.sleep(0.1)
                kb.write(ruta_objetivo)
                time.sleep(0.1)
                kb.send('enter')
                time.sleep(0.1)
                kb.send('alt+n')
                print("✨ ¡Teletransporte completado!")
            else:
                print("⚠️ No pudimos emparejar ninguna carpeta visible.")

        except Exception as e:
            print(f"❌ Error en el teletransporte: {e}")
        finally:
            pythoncom.CoUninitialize()

    def obtener_ejecutable_activo(self):
        """Devuelve el nombre del .exe que está en primer plano, siempre en MAYÚSCULAS."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return ""

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proceso = psutil.Process(pid)
            nombre_exe = proceso.name().strip().upper()

            if nombre_exe == "APPLICATIONFRAMEHOST.EXE":
                pass

            return nombre_exe
        except Exception as e:
            # ¡NUEVO CHIVATO! Si algo falla, que nos diga el porqué.
            print(f"⚠️ Error en el escáner de ejecutables: {e}")
            return ""


    def obtener_zona_ventana(self, x, y):
        """El Radar: Descubre qué parte de la ventana estás tocando"""

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        pt = POINT(int(x), int(y))

        # 1. ¿Qué ventana está bajo el ratón?
        hwnd = ctypes.windll.user32.WindowFromPoint(pt)
        # 2. Obtenemos la ventana principal, no el botón interno (GA_ROOT = 2)
        hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)

        # 3. Lanzamos el radar WM_NCHITTEST (0x0084)
        lparam = ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)
        zona = ctypes.windll.user32.SendMessageW(hwnd, 0x0084, 0, lparam)
        return hwnd, zona

    def ejecutar_accion(self, comando):
        # ==========================================
        # 1. LIMPIEZA: Quitamos espacios vacíos y comillas fantasma
        # ==========================================
        comando = comando.strip(' "\'')

        # ==========================================
        # 2. INTERCEPTOR WEB: Soporte para 'www.' automático
        # ==========================================
        if comando.startswith("http://") or comando.startswith("https://") or comando.startswith("www."):
            import webbrowser

            # Si el usuario solo escribió "www.google.es", le construimos la URL completa por debajo
            url = comando if comando.startswith("http") else f"https://{comando}"

            webbrowser.open(url)
            return  # Terminamos aquí, no ejecutamos nada más

        print(f"⚡ Ejecutando acción: {comando}")

        if comando.startswith("teclas:"):
            from pynput.keyboard import Controller, Key
            import time

            # 1. Respiro vital (150ms) para asimilar el fin del trazo del ratón
            time.sleep(0.15)

            teclas_crudas = comando.split(":")[1].split(",")
            teclado = Controller()

            # 2. El Gran Diccionario: Traducimos tu YAML a objetos nativos de pynput
            mapa_teclas = {
                "win": Key.cmd,
                "windows": Key.cmd,
                "shift": Key.shift,
                "ctrl": Key.ctrl,
                "alt": Key.alt,
                "left": Key.left,
                "right": Key.right,
                "up": Key.up,
                "down": Key.down,
                "enter": Key.enter,
                "space": Key.space,
                "tab": Key.tab,
                "esc": Key.esc
            }

            teclas_a_pulsar = []
            for t in teclas_crudas:
                tecla_str = t.strip().lower()

                # Si es un modificador o flecha, usamos el objeto de Windows
                if tecla_str in mapa_teclas:
                    teclas_a_pulsar.append(mapa_teclas[tecla_str])
                else:
                    # Si es una letra normal (ej: 'c', 'v'), la dejamos como texto
                    teclas_a_pulsar.append(tecla_str)

            # 3. Disparo Orientado a Objetos (El método infalible)
            try:
                # Fase A: Anclamos las teclas al fondo una a una (con un micro-retraso de seguridad)
                for tecla in teclas_a_pulsar:
                    teclado.press(tecla)
                    time.sleep(0.02)

                # Fase B: Mantener la tensión del acorde
                time.sleep(0.05)

                # Fase C: Soltar los muelles en orden inverso
                for tecla in reversed(teclas_a_pulsar):
                    teclado.release(tecla)

                print(f"⌨️ Inyección limpia con pynput: {' + '.join([t.strip() for t in teclas_crudas])}")
            except Exception as e:
                print(f"⚠️ Error crítico en la inyección: {e}")

        # ==========================================

        elif comando.startswith("ventana:"):
            accion = comando.split(":")[1].strip().lower()

            # ==========================================
            # NUEVO: REDIRECCIÓN INTELIGENTE AL MOTOR DE TECLADO
            # Reutilizamos el poder de pynput para los atajos del sistema
            # ==========================================
            if accion == "minimizar_todas":
                self.ejecutar_accion("teclas:win,m")
                return
            elif accion == "restaurar_todas":
                self.ejecutar_accion("teclas:shift,win,m")
                return
            elif accion == "escritorio":
                self.ejecutar_accion("teclas:win,d")
                return
            # ==========================================

            import win32gui
            import ctypes
            import os

            # ==========================================
            # LÓGICA DE RESCATE (Inmune al Escudo)
            # Actúa antes de leer qué ventana está en primer plano
            # ==========================================
            if accion == "restaurar_una":
                if hasattr(self, 'historial_minimizadas') and self.historial_minimizadas:
                    ultimo_hwnd = self.historial_minimizadas.pop()
                    if win32gui.IsWindow(ultimo_hwnd):
                        ctypes.windll.user32.ShowWindow(ultimo_hwnd, 9)  # 9 es Restaurar
                        try:
                            # Forzamos a Windows a darle el foco a la ventana rescatada
                            ctypes.windll.user32.SetForegroundWindow(ultimo_hwnd)
                        except:
                            pass
                        print(f"🪄 Ventana rescatada. (Quedan {len(self.historial_minimizadas)} en memoria)")
                    else:
                        print("⚠️ La ventana que tocaba rescatar ya no existe.")
                else:
                    print("⚠️ No hay ventanas en la memoria para rescatar.")

                # IMPORTANTÍSIMO: Salimos de la función aquí para saltarnos el Escudo
                return
                # ==========================================

            hwnd = ctypes.windll.user32.GetForegroundWindow()

            # ==========================================
            # EL ESCUDO DE TITANIO (Puro Ctypes nativo)
            # ==========================================

            try:
                clase_ventana = win32gui.GetClassName(hwnd)

                # Interrogamos a Windows usando la API nativa, esto NUNCA falla
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                # Si es el escritorio, la barra, o el DNI coincide con el de OpenStroke:
                if clase_ventana in ["Progman", "WorkerW", "Shell_TrayWnd"] or pid.value == os.getpid():
                    print(f"🛡️ Escudo activado: Protegiendo el sistema o el propio OpenStroke (Clase: {clase_ventana})")
                    self.root.after(0, lambda: self.desvanecer_linea("trazo", 1.0))
                    return  # Abortamos la misión de minimizar

            except Exception as e:
                # Si el escudo falla por algún motivo extraño, ahora nos enteraremos
                print(f"⚠️ ERROR CRÍTICO EN EL ESCUDO: {e}")
            # ==========================================

            if accion == "minimizar":
                # 1. MEMORIA LIFO: Creamos la lista si no existe y guardamos el DNI de la ventana
                if not hasattr(self, 'historial_minimizadas'):
                    self.historial_minimizadas = []
                self.historial_minimizadas.append(hwnd)

                # 2. Hundimos la ventana
                ctypes.windll.user32.ShowWindow(hwnd, 6)
                print(f"⏬ Ventana minimizada y guardada en memoria (Total: {len(self.historial_minimizadas)})")

            elif accion == "maximizar":
                # ==========================================
                # Inteligencia de Maximizar / Restaurar
                # ==========================================
                if ctypes.windll.user32.IsZoomed(hwnd):
                    ctypes.windll.user32.ShowWindow(hwnd, 9)  # 9 es Restaurar
                else:
                    ctypes.windll.user32.ShowWindow(hwnd, 3)  # 3 es Maximizar

            elif accion == "restaurar":
                ctypes.windll.user32.ShowWindow(hwnd, 9)
            elif accion == "cerrar":
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            elif accion == "fijar":
                self.fijar_ventana(hwnd)
            elif accion == "transparente":
                self.hacer_transparente(hwnd)
            elif accion == "siguiente":
                # Simulamos un toque rápido de Alt+Tab
                import keyboard as kb
                kb.send('alt+tab')
                print("⏭️ Salto a la ventana siguiente.")
            elif accion == "atras":
                # Simulamos Alt+Shift+Tab
                import keyboard as kb
                kb.send('alt+shift+tab')
                print("⏮️ Salto a la ventana anterior (inverso).")
            elif accion == "arriba":
                import keyboard as kb
                kb.send('backspace')
                print("📁 Subiendo un nivel en el directorio.")
                # ==========================================

        else:
            # Si es un programa o archivo normal:
            try:
                # Popen lanza el programa y le devuelve el control a Python INMEDIATAMENTE
                subprocess.Popen(comando, shell=True)
            except Exception as e:
                print(f"Error al ejecutar: {e}")

    # ==========================================
    # CÓDIGO BÁSICO (CONFIGURACIÓN, RAYOS X Y DIBUJO)
    # ==========================================

    def cargar_configuracion(self):
        self.primera_vez = not os.path.exists(self.ruta_yaml)

        # ==========================================
        # INTERROGATORIO AL REGISTRO DE WINDOWS
        # ==========================================
        if getattr(self, 'modo_portable', False):
            self.arranque_automatico = False  # En modo portable no arrancamos con Windows
        else:
            import winreg
            try:
                ruta_reg = r"Software\Microsoft\Windows\CurrentVersion\Run"
                clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_reg, 0, winreg.KEY_READ)
                winreg.QueryValueEx(clave, "OpenStroke")
                winreg.CloseKey(clave)
                self.arranque_automatico = True  # Windows dice que SÍ estamos matriculados
            except FileNotFoundError:
                self.arranque_automatico = False  # Windows dice que NO
        # ==========================================

        if self.primera_vez:
            self.plantillas = {}
            self.gestos_app = {'GLOBAL': {}}
            self.gestos_globales = self.gestos_app['GLOBAL']
            self.excepciones = []
            self.poderes_jedi = True
            self.mostrar_splash = False
            self.sigilo = []
            self.grosor_borde = 6  # Valor por defecto del borde
            return

        try:
            with open(self.ruta_yaml, "r", encoding="utf-8") as archivo:
                datos = yaml.safe_load(archivo) or {}
                ajustes = datos.get('ajustes') or {}
                self.tiempo_maximo_s = float(ajustes.get('tiempo_cancelacion', 3.0))
                self.color_linea = ajustes.get('color', '#FF0000')
                self.grosor_linea = int(ajustes.get('grosor', 4))
                self.grosor_borde = int(ajustes.get('borde', 6))  # <-- ¡NUEVO! Leemos el borde

                self.geometria_config = ajustes.get('geometria_config', '1800x1100')
                self.geometria_guia = ajustes.get('geometria_guia', '1000x1400')
                self.geometria_grabar = ajustes.get('geometria_grabar', '500x500')

                self.umbral_tolerancia = float(ajustes.get('tolerancia', 0.35))

                # Ya NO leemos el arranque_automatico del YAML, mandan las llaves de Windows
                self.poderes_jedi = ajustes.get('poderes_jedi', True)
                self.mostrar_splash = ajustes.get('mostrar_splash', False)

                paleta_por_defecto = {
                    "normal": "#FF0000", "letras": "#FF00FF",
                    "middle": "#00FFFF", "right": "#008080", "x1": "#800080", "x2": "#000080",
                    "ctrl": "#00FF00", "shift": "#0000FF", "alt": "#FF9800", "space": "#FFFF00"
                }
                self.colores = datos.get('colores', paleta_por_defecto) if datos else paleta_por_defecto

                self.plantillas = datos.get('plantillas', {})
                self.gestos_app = datos.get("gestos") or {}
                if 'GLOBAL' not in self.gestos_app: self.gestos_app['GLOBAL'] = {}
                self.gestos_globales = self.gestos_app['GLOBAL']
                self.excepciones = datos.get("excepciones") or []
                self.sigilo = datos.get('sigilo', [])

        except Exception as e:
            print(f"⚠️ ERROR AL LEER YAML: {e}")
            self.plantillas = {}
            self.gestos_app = {'GLOBAL': {}}
            self.gestos_globales = self.gestos_app['GLOBAL']
            self.colores = paleta_por_defecto
            self.excepciones = []
            self.poderes_jedi = True
            self.grosor_borde = 6


    def obtener_exe_activo(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            pid = ctypes.c_ulong(0)
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h_process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
            if h_process:
                buffer = ctypes.create_unicode_buffer(512)
                size = ctypes.c_ulong(512)
                if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_process, 0, buffer, ctypes.byref(size)):
                    ctypes.windll.kernel32.CloseHandle(h_process)
                    return os.path.basename(buffer.value).upper()
                ctypes.windll.kernel32.CloseHandle(h_process)
        except Exception:
            pass
        return "DESCONOCIDO"

    def abrir_ventana_configuracion(self):
        if hasattr(self, 'ventana_config_activa') and self.ventana_config_activa.ventana.winfo_exists():
            self.ventana_config_activa.ventana.focus()
        else:
            self.ventana_config_activa = VentanaConfiguracion(self)

    def mostrar_hud(self, mensaje):
        """Crea o recicla un holograma flotante en pantalla sin parpadeos"""

        # 1. LA MAGIA DEL RECICLAJE: Si no existe, la creamos UNA sola vez en las sombras
        if not hasattr(self, 'hud_window') or not self.hud_window.winfo_exists():
            self.hud_window = tk.Toplevel(self.root)
            self.hud_window.withdraw()  # La mandamos a dormir inmediatamente
            self.hud_window.overrideredirect(True)

            # ==========================================
            # ¡LA CURA! Añadimos "-toolwindow", True al HUD
            # ==========================================
            self.hud_window.attributes("-topmost", True, "-toolwindow", True)
            self.hud_window.config(bg="#282C34")

            # Creamos la etiqueta una sola vez y la dejamos lista
            self.hud_label = tk.Label(self.hud_window, font=("Segoe UI", 20, "bold"), fg="#61AFEF", bg="#282C34",
                                      padx=30, pady=15)
            self.hud_label.pack()
            self.hud_after_id = None

        # 2. Si el usuario hace gestos muy rápido, cancelamos la animación anterior para que no se pisen
        if getattr(self, 'hud_after_id', None) is not None:
            self.hud_window.after_cancel(self.hud_after_id)
            self.hud_after_id = None

        # 3. Actualizamos el texto con la nueva orden
        self.hud_label.config(text=mensaje)

        # 4. La hacemos 100% transparente ANTES de sacarla a la luz para evitar el flash de Windows
        self.hud_window.attributes("-alpha", 0.0)
        self.hud_window.deiconify()

        # 5. Recalculamos posición matemática al vuelo
        self.hud_window.update_idletasks()
        ancho = self.hud_window.winfo_width()
        alto = self.hud_window.winfo_height()
        x = (self.hud_window.winfo_screenwidth() // 2) - (ancho // 2)
        y = self.hud_window.winfo_screenheight() - alto - 150
        self.hud_window.geometry(f"+{x}+{y}")

        # 6. ¡Luz! Encendemos la opacidad de golpe ahora que ya está posicionada y formateada
        self.hud_window.attributes("-alpha", 0.9)

        # 7. Desvanecimiento suave
        def desvanecer():
            if not self.hud_window.winfo_exists(): return
            alfa_actual = self.hud_window.attributes("-alpha")
            if alfa_actual > 0.05:
                self.hud_window.attributes("-alpha", alfa_actual - 0.05)
                self.hud_after_id = self.hud_window.after(40, desvanecer)
            else:
                self.hud_window.withdraw()  # En vez de matarla (destroy), la mandamos a dormir al cajón

        self.hud_after_id = self.hud_window.after(1000, desvanecer)
    def analizar_y_ejecutar(self):
        exe_activo = self.obtener_exe_activo()
        if exe_activo in self.excepciones:
            # Cámbialo en los dos sitios donde aparece dentro de analizar_y_ejecutar
            self.root.after(0, lambda: self.desvanecer_linea("trazo", 1.0))
            return

        nombre_gesto, distancia = self.motor.reconocer(self.puntos, self.plantillas, self.umbral_tolerancia)
        if nombre_gesto:
            print(f"🕵️ Detectado: {nombre_gesto} (Capa: {self.modificador_actual})")
            comando = None
            opciones = None

            # 1. Buscamos en el diccionario de la App actual o en el Global
            if exe_activo in self.gestos_app and nombre_gesto in self.gestos_app[exe_activo]:
                opciones = self.gestos_app[exe_activo][nombre_gesto]
            elif hasattr(self, 'gestos_globales') and nombre_gesto in self.gestos_globales:
                opciones = self.gestos_globales[nombre_gesto]

            # 2. EL CEREBRO INTELIGENTE: Separación estricta por acordes
            if opciones:
                if isinstance(opciones, dict):
                    # Solo ejecutamos si hay un comando EXACTO para la tecla pulsada
                    comando = opciones.get(self.modificador_actual)

                    if not comando:
                        print(
                            f"⚠️ Gesto '{nombre_gesto}' detectado, pero no hay acción para la capa '{self.modificador_actual}'.")
                else:
                    # Si es un gesto normal (antiguo), solo se activa si NO pulsas ninguna tecla extra
                    comando = str(opciones) if self.modificador_actual == 'default' else None
                    if not comando:
                        print(f"⚠️ Ignorando gesto normal porque estás pulsando la capa '{self.modificador_actual}'.")

            # 3. La ejecución final y el holograma
            if comando:
                self.ejecutar_accion(comando)

                # ==========================================
                # ¡EL TOQUE PREMIUM! Encendemos el HUD Holográfico
                self.mostrar_hud(f"🚀 {comando.upper()}")
                # ==========================================
        # Cámbialo en los dos sitios donde aparece dentro de analizar_y_ejecutar
        self.root.after(0, lambda: self.desvanecer_linea("trazo", 1.0))


    def verificar_timeout(self):
        if self.presionado and not self.pausado and not getattr(self, 'gesto_cancelado', False):
            if time.time() - self.tiempo_inicio >= self.tiempo_maximo_s:
                self.gesto_cancelado = True
                self.puntos = []
                self.canvas.delete("all")
        self.root.after(100, self.verificar_timeout)

    def al_hacer_clic(self, x, y, button, pressed):
        if self.pausado or getattr(self, 'simulando_clic', False): return
        botones_permitidos = [mouse.Button.right, mouse.Button.middle, mouse.Button.x1, mouse.Button.x2]

        if button in botones_permitidos:
            if pressed:
                # ==========================================
                # NUEVO: EL ESCUDO DE LAS EXCEPCIONES (BLINDADO)
                # ==========================================
                # 1. Capturamos lo que vemos y lo limpiamos de espacios
                exe_actual = str(self.obtener_ejecutable_activo()).strip().upper()
                self.exe_activo = exe_actual  # <--- ¡AÑADE ESTA LÍNEA PARA MEMORIZARLO!
                # 2. Limpiamos también tu lista negra entera por si acaso
                lista_negra_limpia = [str(exe).strip().upper() for exe in self.excepciones]

                print(f"🕵️ Escáner: '{exe_actual}' | Lista limpia: {lista_negra_limpia}")

                # 3. La comprobación a prueba de fallos
                if exe_actual in lista_negra_limpia:
                    print(f"🛡️ ESCUDO ACTIVADO: Bloqueando OpenStroke para {exe_actual}")

                    # ¡EL CAMBIO CLAVE! Le decimos al clon exactamente qué botón debe pulsar
                    self.boton_presionado = button

                    self.presionado = False
                    self.gesto_activado = False
                    self.puntos = []  # Vaciamos la memoria de dibujo

                    # ¡CURA DEL DOBLE CLIC! Ya no mandamos al clon, Windows hace el clic real
                    return  # Abortamos la misión de OpenStroke
                # ==========================================


                # --- INTERCEPTACIÓN DEL RADAR (PODERES JEDI) ---
                if getattr(self, 'poderes_jedi', False):
                    hwnd, zona = self.obtener_zona_ventana(x, y)

                    # Trucos del Clic Derecho
                    if button == mouse.Button.right:
                        if zona == 8:  # Botón Minimizar
                            self.hacer_transparente(hwnd)
                            return
                        elif zona == 9:  # Botón Maximizar
                            self.fijar_ventana(hwnd)
                            return

                    # Truco de la Rueda (Teletransporte multihilo)
                    elif button == mouse.Button.middle:
                        if zona == 2:  # Volvemos a poner el seguro: SOLO en la barra de título
                            print(f"🔍 Radar: ¡Diana en la barra de título (Zona 2)!")
                            import threading
                            # Lanzamos a un clon a hacer el trabajo sucio en segundo plano
                            threading.Thread(target=self.teletransportar_ruta, daemon=True).start()
                            return  # Soltamos el ratón al instante

                    # --- INICIO DEL GESTO NORMAL ---
                    self.boton_presionado = button

                    # Por defecto, usamos el color Normal
                    self.modificador_actual = 'default'
                    self.color_trazo_actual = self.colores.get("normal", "#FF0000")

                    if button == mouse.Button.middle:
                        self.modificador_actual = 'middle'
                        self.color_trazo_actual = self.colores.get("middle", "#00FFFF")
                    elif button == mouse.Button.x1:
                        self.modificador_actual = 'x1'
                        self.color_trazo_actual = self.colores.get("x1", "#800080")
                    elif button == mouse.Button.x2:
                        self.modificador_actual = 'x2'
                        self.color_trazo_actual = self.colores.get("x2", "#000080")

                    elif button == mouse.Button.right:
                        # --- 1. MODIFICADORES CLÁSICOS ---
                        if keyboard.is_pressed('ctrl'):
                            self.modificador_actual = 'ctrl'
                            self.color_trazo_actual = self.colores.get("ctrl", "#00FF00")
                        elif keyboard.is_pressed('shift'):
                            self.modificador_actual = 'shift'
                            self.color_trazo_actual = self.colores.get("shift", "#0000FF")
                        elif keyboard.is_pressed('alt'):
                            self.modificador_actual = 'alt'
                            self.color_trazo_actual = self.colores.get("alt", "#FF9800")

                        # --- 2. ACORDES JEDI (La Lista Blanca) ---
                        elif keyboard.is_pressed('space'):
                            self.modificador_actual = 'space'
                            self.color_trazo_actual = self.colores.get("space", "#FFFF00")
                        else:
                            # 3. Escaneamos de la 'a' a la 'z'.
                            for letra in string.ascii_lowercase:
                                if keyboard.is_pressed(letra):
                                    self.modificador_actual = letra
                                    self.color_trazo_actual = self.colores.get("letras", "#FF00FF")
                                    break  # En cuanto detecta la tecla, detiene el bucle para ahorrar CPU

                    self.presionado = True

                self.presionado = True
                self.gesto_activado = False
                self.gesto_cancelado = False
                self.tiempo_inicio = time.time()
                self.pos_inicial = (x, y)
                self.puntos = []


            else:
                # --- FIN DEL GESTO ---
                if getattr(self, 'boton_presionado', None) == button:
                    try:
                        self.presionado = False
                        if self.gesto_cancelado:
                            self.root.after(0, lambda: self.canvas.delete("all"))
                            return

                        if self.gesto_activado:
                            # El propio analizador se encargará de lanzar el Fade-Out
                            self.analizar_y_ejecutar()
                        else:
                            # ¡CURA DEL DOBLE CLIC! Eliminamos la llamada a self.hacer_clic_real()
                            # Si fue un clic normal, solo borramos los puntitos residuales
                            self.root.after(0, lambda: self.canvas.delete("all"))
                    except Exception as e:
                        print(f"❌ Error crítico al ejecutar el gesto: {e}")
                        self.root.after(0, lambda: self.canvas.delete("all"))
                    finally:
                        self.boton_presionado = None

    def al_mover(self, x, y):
        if self.presionado and not self.pausado and not getattr(self, 'gesto_cancelado', False):
            dx = x - self.pos_inicial[0]
            dy = y - self.pos_inicial[1]
            if not self.gesto_activado and math.hypot(dx, dy) > 15:
                self.gesto_activado = True
                self.puntos.append([self.pos_inicial[0] - self.offset_x, self.pos_inicial[1] - self.offset_y])

            if self.gesto_activado:
                self.puntos.append([x - self.offset_x, y - self.offset_y])
                self.root.after(0, self.dibujar)

    def dibujar(self):
        # ==========================================
        # ESCUDO SIGILO: Si somos ninjas, abortamos el renderizado
        # ==========================================
        if getattr(self, 'exe_activo', '') in getattr(self, 'sigilo', []):
            return
        # ==========================================

        if len(self.puntos) >= 2:
            # 1. Limpiamos el fotograma anterior
            self.canvas.delete("trazo")
            self.canvas.delete("borde_trazo")

            puntos_planos = [c for p in self.puntos for c in p]

            # Leemos tu variable de la memoria (con un salvavidas de valor 6 por si acaso)
            grosor_extra = getattr(self, 'grosor_borde', 6)

            # 2. Dibujamos el Borde (SOLO si el usuario lo tiene activado)
            if grosor_extra > 0:
                grosor_total_borde = int(self.grosor_linea) + grosor_extra
                self.canvas.create_line(puntos_planos, fill="#FEFEFE", width=grosor_total_borde,
                                        smooth=True, capstyle=tk.ROUND, tags="borde_trazo")

            # 3. Dibujamos el Trazo Principal (Color elegido) justo encima
            self.canvas.create_line(puntos_planos, fill=self.color_trazo_actual, width=int(self.grosor_linea),
                                    smooth=True, capstyle=tk.ROUND, tags="trazo")


    def desvanecer_linea(self, tag, opacidad):
        # ¡NUEVO! En el primer fotograma de la animación (1.0), fulminamos el borde blanco
        if opacidad == 1.0:
            self.canvas.delete("borde_trazo")

        if opacidad > 0:
            gris = int(255 * (1 - opacidad))
            color_fade = f'#{gris:02x}{gris:02x}{gris:02x}'
            self.canvas.itemconfig(tag, fill=color_fade)
            self.root.after(40, lambda: self.desvanecer_linea(tag, opacidad - 0.1))
        else:
            self.canvas.delete(tag)


    def hacer_clic_real(self):
        self.simulando_clic = True
        self.root.withdraw()
        self.mouse_controller.press(self.boton_presionado)
        self.mouse_controller.release(self.boton_presionado)
        self.root.after(150, lambda: self.root.deiconify())
        self.root.after(200, lambda: setattr(self, 'simulando_clic', False))

    def obtener_imagen_estado(self, pausado=False):
        """Carga los iconos Premium de alta resolución según el estado del programa"""
        from PIL import Image
        try:
            # Elegimos qué archivo cargar según si estamos en pausa o no
            nombre_archivo = "pausado.ico" if pausado else "activo.ico"
            ruta = ruta_recurso(nombre_archivo)

            # PIL es capaz de leer .ico con todas sus capas de resolución
            return Image.open(ruta)
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo cargar {nombre_archivo}. Usando fallback. Error: {e}")
            # Paracaídas de emergencia: si borras el archivo sin querer, crea un cuadrado de color
            return Image.new('RGB', (64, 64), color='gray' if pausado else 'blue')

    def abrir_ventana_acerca_de(self):
        # Escudo Anti-Clones
        if hasattr(self, 'ventana_acerca') and self.ventana_acerca.winfo_exists():
            self.ventana_acerca.focus_force()
            return

        import tkinter as tk
        from tkinter import ttk

        self.ventana_acerca = tk.Toplevel(self.root)
        self.ventana_acerca.title("Acerca de OpenStroke")
        self.ventana_acerca.geometry("500x450")
        self.ventana_acerca.attributes("-topmost", True)
        self.ventana_acerca.configure(bg="#f0f0f0")

        # Inyectamos tu logotipo
        try:
            self.ventana_acerca.iconbitmap(ruta_recurso("logo.ico"))
        except Exception:
            pass

        # Cabecera Premium
        tk.Label(self.ventana_acerca, text="OpenStroke", font=("Segoe UI", 20, "bold"), bg="#f0f0f0",
                 fg="#2196F3").pack(pady=(15, 0))
        tk.Label(self.ventana_acerca, text="Versión 4.9.5 Alpha | Build: 2026.03.17", font=("Segoe UI", 10),
                 bg="#f0f0f0", fg="#555").pack(pady=(0, 10))
        tk.Label(self.ventana_acerca, text="Ratón y Teclado Unidos, Multi-entrada, Código Abierto",
                 font=("Segoe UI", 9, "italic"), bg="#f0f0f0", fg="#888").pack(pady=(0, 15))

        # El Visor del Changelog
        frame_texto = tk.Frame(self.ventana_acerca, padx=20, pady=10, bg="#f0f0f0")
        frame_texto.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(frame_texto, font=("Consolas", 10), bg="#2d2d2d", fg="#a9b7c6", wrap=tk.WORD, padx=10, pady=10)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame_texto, command=txt.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=scrollbar.set)

        # ==========================================
        # EL LECTOR DEL HISTORIAL
        # ==========================================
        ruta_changelog = ruta_recurso("changelog.txt")
        if os.path.exists(ruta_changelog):
            try:
                with open(ruta_changelog, "r", encoding="utf-8") as f:
                    contenido = f.read()
            except Exception as e:
                contenido = f"Error al leer el archivo: {e}"
        else:
            contenido = "=== HISTORIAL DE CAMBIOS ===\n\nNo se ha encontrado el archivo 'changelog.txt'.\nCrea este archivo en la carpeta de tu código para ver aquí tus notas de versión."

        txt.insert(tk.END, contenido)
        txt.config(state="disabled")  # Lo bloqueamos para que el usuario no pueda borrar el texto

    def setup_tray(self):
        def pedir_configuracion(icon, item): self.root.after(0, self.abrir_ventana_configuracion)

        # NUEVO: La llamada segura desde el hilo de pystray al hilo de Tkinter
        def pedir_acerca_de(icon, item): self.root.after(0, self.abrir_ventana_acerca_de)

        def toggle_pausa(icon, item):
            self.pausado = not self.pausado
            # Cambiamos el icono en tiempo real usando nuestra nueva función
            self.root.after(10, lambda: setattr(icon, 'icon', self.obtener_imagen_estado(self.pausado)))

        menu = pystray.Menu(
            pystray.MenuItem("Pausar / Reanudar", toggle_pausa, default=True),
            pystray.MenuItem("Configuración", pedir_configuracion),
            pystray.MenuItem("Acerca de...", pedir_acerca_de),
            pystray.MenuItem("Salir", self.salir_total)
        )

        # Le inyectamos el icono "activo" para que sea el que muestre al arrancar
        self.icon = pystray.Icon("OpenStroke", self.obtener_imagen_estado(pausado=False), "OpenStroke", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def salir_total(self, icon=None, item=None):
        if self.icon: self.icon.stop()
        self.root.quit()
        self.root.destroy()
        os._exit(0)


if __name__ == "__main__":
    # ==========================================
    # ESCUDO ANTI-CLONES (MutEx Única Instancia)
    # ==========================================
    # Creamos un "ticket" único en el kernel de Windows para nuestro programa
    mutex_nombre = "OpenStroke_App_Mutex_Definitivo"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_nombre)

    # 183 es el código de Windows para ERROR_ALREADY_EXISTS
    if ctypes.windll.kernel32.GetLastError() == 183:
        print("⚠️ OpenStroke ya está en ejecución. Cerrando clon silenciosamente...")
        sys.exit(0) # Aniquilamos esta instancia antes de que nazca
    # ==========================================

    app = OpenStrokeApp()