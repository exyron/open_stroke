import tkinter as tk
from tkinter import colorchooser, ttk, simpledialog, messagebox,filedialog
import yaml
import winreg  # Para operar el Registro de Windows
import sys
import os
import string # Asegúrate de que esto está arriba del todo del archivo o aquí
from tkinter import filedialog
import ctypes # <-- Importante añadir esta librería nativa
from tkinter import colorchooser

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
# ==========================================
# EL ESCUDO DE RESOLUCIÓN (DPI AWARENESS)
# ==========================================
try:
    # Le decimos a Windows 10/11 que nuestra app es de alta resolución
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        # Modo de compatibilidad para versiones de Windows más antiguas
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass # Si falla (por ejemplo en Linux o Mac), lo ignoramos silenciosamente
# ==========================================

class VentanaConfiguracion:
    def __init__(self, app):
        self.app = app

        self.app.pausado = True
        if self.app.icon:
            self.app.icon.icon = self.app.obtener_imagen_estado(pausado=True)

        self.ventana = tk.Toplevel(self.app.root)
        self.ventana.title("Ajustes de OpenStroke v4.9.6")

        # 1. Tamaño por defecto si no hay YAML (Formato amplio para 4K)
        self.ventana.geometry(getattr(self.app, 'geometria_config', "1800x1100"))

        # ==========================================
        # ESTÉTICA: Icono de la ventana de Ajustes
        # ==========================================
        try:
            self.ventana.iconbitmap(ruta_recurso("logo.ico"))
        except Exception as e:
            print(f"Aviso icono ajustes: {e}")
        # ==========================================

        # 2. Ajustamos la segunda llamada de seguridad al mismo tamaño
        self.ventana.geometry(getattr(self.app, 'geometria_config', "1800x1100"))

        # 3. EL CAMBIO CLAVE: Bajamos el minsize regulatorio.
        # Al ponerlo en 1200x700, permitimos que la ventana se abra a 1800x1100 sin restricciones,
        # pero impedimos que el usuario la encoja demasiado por accidente.
        self.ventana.minsize(1200, 700)
        self.ventana.configure(bg="#f0f0f0")
        self.ventana.attributes("-topmost", True)

        self.ventana.protocol("WM_DELETE_WINDOW", self.al_cerrar_x)

        self.construir_interfaz()

    def al_cerrar_x(self):
        # 1. LA CAPA DE INVISIBILIDAD: Ocultamos la ventana al instante (UX Perfecta)
        self.ventana.withdraw()

        # ==========================================
        # NUEVO: RECOLECTOR DE BASURA DE VENTANAS HIJAS
        # ==========================================
        # Si el usuario se deja la guía de comandos abierta, la cerramos de forma proactiva
        if hasattr(self, 'ven_guia_activa') and self.ven_guia_activa.winfo_exists():
            try:
                self.ven_guia_activa.destroy()
            except Exception as e:
                print(f"Aviso al limpiar ventana de guia: {e}")
        # ==========================================

        # 2. Apagamos los proyectores de cine para que no queden bucles huérfanos
        if hasattr(self, 'id_animacion'):
            try:
                self.ventana.after_cancel(self.id_animacion)
            except:
                pass
        if hasattr(self, 'id_anim_grabar'):
            try:
                self.ventana.after_cancel(self.id_anim_grabar)
            except:
                pass

        # 3. Desconectamos el deslizador (Suele ser el culpable del TclError al morir)
        try:
            self.escala_grosor.config(command="")
        except:
            pass

        # 4. Guardamos los datos en la memoria
        self.app.geometria_config = self.ventana.geometry()
        self.app.pausado = False
        if self.app.icon:
            self.app.icon.icon = self.app.obtener_imagen_estado(pausado=self.app.pausado)

        # 5. Destrucción en la sombra
        try:
            self.ventana.destroy()
        except tk.TclError:
            # Si Tcl se atraganta limpiando la memoria, nos da igual porque la ventana ya es invisible
            pass

        if hasattr(self.app, 'ventana_config_activa'):
            del self.app.ventana_config_activa

    # ==========================================
    # EL CIRUJANO DEL REGISTRO Y EL GUARDADO YAML
    # ==========================================
    def aplicar_cambios(self, silencioso=False):
        try:
            self.app.tiempo_maximo_s = float(self.entry_tiempo.get().replace(',', '.'))
        except ValueError:
            pass

        # === CAPTURAMOS LOS VALORES DE LA INTERFAZ ===
        self.app.grosor_linea = self.escala_grosor.get()
        self.app.grosor_borde = self.escala_borde.get()  # <-- ¡NUEVO! Atrapamos el valor del deslizador del borde
        self.app.umbral_tolerancia = self.escala_tolerancia.get() / 100.0

        self.app.arranque_automatico = self.var_arranque.get()
        self.app.poderes_jedi = self.var_jedi.get()
        self.app.mostrar_splash = self.var_splash.get()

        # === 1. CONSTRUIMOS EL DICCIONARIO PARA EL YAML ===
        datos = {
            'ajustes': {
                'tiempo_cancelacion': self.app.tiempo_maximo_s,
                'color': self.app.color_linea,
                'grosor': self.app.grosor_linea,
                'borde': self.app.grosor_borde,  # <-- ¡NUEVO! Lo inyectamos en la memoria
                'tolerancia': self.app.umbral_tolerancia,
                'arranque_automatico': self.app.arranque_automatico,
                'poderes_jedi': self.app.poderes_jedi,
                'mostrar_splash': self.app.mostrar_splash,
                # --- LÍNEAS PARA LA MEMORIA VISUAL ---
                'geometria_config': getattr(self.app, 'geometria_config', self.ventana.geometry()),
                'geometria_guia': getattr(self.app, 'geometria_guia', "450x550"),
                'geometria_grabar': getattr(self.app, 'geometria_grabar', "500x500")
            },
            'plantillas': self.app.plantillas,
            'gestos': self.app.gestos_app,
            'excepciones': self.app.excepciones,
            'sigilo': getattr(self.app, 'sigilo', []),
            'colores': getattr(self.app, 'colores', {})
        }

        try:
            with open(self.app.ruta_yaml, "w", encoding="utf-8") as archivo:
                yaml.dump(datos, archivo, default_flow_style=False)
            if not silencioso: print("👉 YAML guardado con éxito.")
        except Exception as e:
            print(f"❌ Error al guardar el YAML: {e}")

            # === 2. INSCRIBIMOS A OPENSTROKE EN EL ARRANQUE DE WINDOWS ===
            if getattr(self.app, 'modo_portable', False):
                print("🎒 Modo Portable Activo: Se omite la escritura en el Registro de Windows.")
            else:
                import winreg
                ruta_registro = r"Software\Microsoft\Windows\CurrentVersion\Run"
                try:
                    clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_registro, 0, winreg.KEY_ALL_ACCESS)
                    if self.app.arranque_automatico:
                        ruta_programa = os.path.abspath(sys.argv[0])
                        if not ruta_programa.endswith('.exe'):
                            comando_arranque = f'"{sys.executable}" "{ruta_programa}"'
                        else:
                            comando_arranque = f'"{ruta_programa}"'

                        winreg.SetValueEx(clave, "OpenStroke", 0, winreg.REG_SZ, comando_arranque)
                        print("✅ OpenStroke matriculado en el arranque de Windows.")
                    else:
                        try:
                            winreg.DeleteValue(clave, "OpenStroke")
                            print("❌ OpenStroke desmatriculado del arranque de Windows.")
                        except FileNotFoundError:
                            pass
                    winreg.CloseKey(clave)
                except Exception as e:
                    print(f"⚠️ No se pudo modificar el registro de Windows: {e}")


    def btn_aplicar(self):
        self.aplicar_cambios()
        self.app.pausado = False
        # ¡NUEVO! Llamamos al motor de alta resolución
        if self.app.icon: self.app.icon.icon = self.app.obtener_imagen_estado(pausado=False)

    def btn_guardar_cerrar(self):
        self.aplicar_cambios()
        self.al_cerrar_x()

    def abrir_ventana_grabacion(self):
        # ==========================================
        # NUEVO: Escudo Anti-Clones (Patrón Singleton)
        # ==========================================
        if hasattr(self, 'ven_grabar_activa') and self.ven_grabar_activa.winfo_exists():
            # Si ya existe y está abierta, la traemos al frente y cancelamos la creación
            self.ven_grabar_activa.focus_force()
            return

        self.ven_grabar_activa = tk.Toplevel(self.ventana)
        ven_grabar = self.ven_grabar_activa  # Referencia corta para no cambiar el resto del código

        # ==========================================
        # ESTÉTICA: Icono de la Grabadora
        # ==========================================
        try:
            ven_grabar.iconbitmap(ruta_recurso("logo.ico"))
        except Exception:
            pass
        # ==========================================


        ven_grabar.attributes("-topmost", True)

        def al_cerrar_grabar():
            self.app.geometria_grabar = ven_grabar.geometry()
            ven_grabar.destroy()

        ven_grabar.protocol("WM_DELETE_WINDOW", al_cerrar_grabar)

        tk.Label(ven_grabar,
                 text="Dibuja UNA SOLA LÍNEA continua.\nAl soltar el ratón, verás la lectura del motor en bucle.",
                 font=("Arial", 10, "bold")).pack(pady=10)
        lienzo = tk.Canvas(ven_grabar, bg="#e8f4f8", cursor="crosshair")
        lienzo.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # ==========================================
        # NUEVO: Panel inferior sin Popups molestos
        # ==========================================
        frame_guardar = tk.Frame(ven_grabar)
        frame_guardar.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(frame_guardar, text="Nombre:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        entry_nombre = tk.Entry(frame_guardar, font=("Arial", 10), justify="center")
        entry_nombre.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        puntos_grabados = []
        self.trazo_limpio_actual = []

        # ==========================================
        # NUEVO: Bucle gigante de previsualización
        # ==========================================
        def reproducir_bucle_grabar():
            if not self.trazo_limpio_actual or not lienzo.winfo_exists(): return
            lienzo.delete("animacion")

            # Escalado matemático al tamaño actual de la ventana
            xs = [p[0] for p in self.trazo_limpio_actual];
            ys = [p[1] for p in self.trazo_limpio_actual]
            min_x, max_x = min(xs), max(xs);
            min_y, max_y = min(ys), max(ys)
            w, h = lienzo.winfo_width(), lienzo.winfo_height()
            if w < 10 or h < 10: w, h = 460, 300  # Red de seguridad si no ha cargado

            escala = min((w - 40) / (max_x - min_x if max_x != min_x else 1),
                         (h - 40) / (max_y - min_y if max_y != min_y else 1))
            cx, cy = w / 2, h / 2

            puntos_norm = []
            for x, y in self.trazo_limpio_actual:
                nx = cx + (x - (min_x + max_x) / 2) * escala
                ny = cy + (y - (min_y + max_y) / 2) * escala
                puntos_norm.append((nx, ny))

            self.paso_grabar = 0

            def animar():
                if not lienzo.winfo_exists(): return
                if self.paso_grabar < len(puntos_norm) - 1:
                    p1 = puntos_norm[self.paso_grabar]
                    p2 = puntos_norm[self.paso_grabar + 1]
                    # Pintamos el resultado del motor en un morado espectacular
                    lienzo.create_line(p1[0], p1[1], p2[0], p2[1], fill="#9c27b0", width=4, capstyle=tk.ROUND,
                                       smooth=True, tags="animacion")
                    self.paso_grabar += 1
                    self.id_anim_grabar = lienzo.after(10, animar)
                else:
                    self.id_anim_grabar = lienzo.after(1000, reproducir_bucle_grabar)

            animar()

        def al_presionar(event):
            if hasattr(self, 'id_anim_grabar'): lienzo.after_cancel(self.id_anim_grabar)
            puntos_grabados.clear()
            lienzo.delete("all")
            puntos_grabados.append([event.x, event.y])

        def al_arrastrar(event):
            puntos_grabados.append([event.x, event.y])
            x_ant, y_ant = puntos_grabados[-2]
            # La línea que dibujas a mano es azul
            lienzo.create_line(x_ant, y_ant, event.x, event.y, fill="blue", width=3, smooth=True)

        def al_soltar(event):
            self.trazo_limpio_actual = self.app.motor.procesar_trazo(puntos_grabados)
            if not self.trazo_limpio_actual:
                messagebox.showwarning("Aviso", "Trazo muy corto.", parent=ven_grabar)
                return

            lienzo.delete("all")
            ven_grabar.update_idletasks()  # Forzamos el cálculo de pantalla

            # ==========================================
            # NUEVO: IA de Autocompletado (Reconocimiento en vivo)
            # ==========================================
            # Le preguntamos al motor: "¿Se parece esto a algo que ya conozcas?"
            nombre_reconocido, distancia = self.app.motor.reconocer(puntos_grabados, self.app.plantillas,
                                                                    self.app.umbral_tolerancia)

            entry_nombre.delete(0, tk.END)
            # Si el motor lo reconoce, escribimos el nombre automáticamente
            if nombre_reconocido:
                entry_nombre.insert(0, nombre_reconocido)
            # ==========================================

            reproducir_bucle_grabar()  # Encendemos el cine
            entry_nombre.focus()  # Ponemos el cursor en la caja de texto, por si quiere cambiar el nombre

        def guardar_forma():
            nombre = entry_nombre.get().strip().upper()
            if not nombre:
                return messagebox.showwarning("Aviso", "Ponle un nombre a la forma.", parent=ven_grabar)
            if not self.trazo_limpio_actual:
                return messagebox.showwarning("Aviso", "Dibuja un trazo primero.", parent=ven_grabar)

            if hasattr(self, 'id_anim_grabar'): lienzo.after_cancel(self.id_anim_grabar)
            self.app.plantillas[nombre] = self.trazo_limpio_actual
            self.actualizar_desplegable_plantillas()
            self.actualizar_lista_gestor()

            # ==========================================
            # NUEVO: Auto-cargar en el visor holográfico
            # ==========================================
            try:
                # 1. Seleccionamos el nombre recién creado en el combobox
                self.combo_plantillas.set(nombre)
                # 2. Simulamos un "clic" fantasma para despertar la animación
                self.combo_plantillas.event_generate("<<ComboboxSelected>>")
            except Exception:
                pass
            # ==========================================

            al_cerrar_grabar()


        tk.Button(frame_guardar, text="💾 Guardar", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                  command=guardar_forma).pack(side=tk.RIGHT)

        lienzo.bind("<ButtonPress-1>", al_presionar)
        lienzo.bind("<B1-Motion>", al_arrastrar)
        lienzo.bind("<ButtonRelease-1>", al_soltar)


    def abrir_guia_comandos(self):
        # ==========================================
        # NUEVO: Control Singleton y Vinculación Parental
        # ==========================================
        # 1. Si ya existe y está abierta, la traemos al frente
        if hasattr(self, 'ven_guia_activa') and self.ven_guia_activa.winfo_exists():
            self.ven_guia_activa.lift()
            self.ven_guia_activa.focus_force()
            return

        # 2. Creamos la ventana hija pasándole self.ventana como "Padre"
        # Si cierras la configuración, esta se cerrará automáticamente.
        self.ven_guia_activa = tk.Toplevel(self.ventana)
        ven_guia = self.ven_guia_activa
        ven_guia.title("📚 Guía de Comandos")

        # ==========================================
        # ESTÉTICA: Icono de la Guía
        # ==========================================
        try:
            ven_guia.iconbitmap(ruta_recurso("logo.ico"))
        except Exception:
            pass
        # ==========================================

        ven_guia.geometry(getattr(self.app, 'geometria_guia', "2000x2000"))

        # Le decimos que cuando se cierre, guarde su posición actual en la memoria
        def al_cerrar_guia():
            self.app.geometria_guia = ven_guia.geometry()
            ven_guia.destroy()

        ven_guia.protocol("WM_DELETE_WINDOW", al_cerrar_guia)
        ven_guia.attributes("-topmost", True)

        texto_guia = """
    ======================================================================
                      GUÍA DE COMANDOS DE OPENSTROKE
    ======================================================================

    1. PROGRAMAS Y ARCHIVOS (Por defecto)
    Escribe el nombre del ejecutable o la ruta nativa del archivo.
    • notepad
    • calc
    • chrome.exe https://google.es
    • C:\\Windows\\System32

    2. ATAJOS DE TECLADO (Prefijo "teclas:")
    Simula la pulsación física de un acorde de teclas en el sistema.
    • teclas:ctrl,c            (Copiar)
    • teclas:ctrl,v            (Pegar)
    • teclas:shift,win,left    (Mover ventana al monitor izquierdo)

    [ TECLAS ESPECIALES DISPONIBLES ]
    • Modificadores: win, windows, ctrl, shift, alt
    • Direccionales: up, down, left, right
    • Sistema:       enter, space, tab, esc

    3. VENTANAS NATIVAS (Prefijo "ventana:")
    Manipula el entorno de escritorio y la ventana que esté en primer plano.
    • ventana:minimizar        (Minimiza la ventana actual)
    • ventana:maximizar        (Maximiza o restaura la ventana actual)
    • ventana:cerrar           (Cierra la ventana activa - Alt+F4)
    • ventana:fijar            (Mantiene la ventana siempre al frente)
    • ventana:transparente     (Aplica un efecto fantasma al 50%)
    • ventana:siguiente        (Salto rápido a la siguiente ventana)
    • ventana:atras            (Salto inverso a la ventana anterior)
    • ventana:arriba           (Sube un nivel de carpeta / Backspace)
    • ventana:minimizar_todas  (Esconde todo el espacio de trabajo)
    • ventana:restaurar_todas  (Recupera todas las ventanas minimizadas)
    • ventana:escritorio       (Muestra u oculta el escritorio - Toggle)
    ======================================================================"""

        txt = tk.Text(ven_guia, font=("Consolas", 10), bg="#2d2d2d", fg="#a9b7c6", padx=15, pady=15)
        txt.insert(tk.END, texto_guia)
        txt.config(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)


    def actualizar_desplegable_plantillas(self):
        opciones = list(self.app.plantillas.keys())
        if not opciones: opciones = ["(Graba una plantilla)"]
        self.combo_plantillas['values'] = opciones
        self.combo_plantillas.set(opciones[-1] if self.app.plantillas else opciones[0])

    def actualizar_lista_gestos(self):
        # Limpiamos la tabla
        for item in self.tree_gestos.get_children():
            self.tree_gestos.delete(item)

        ctx = self.combo_contexto.get()

        if ctx == "EXCEPCIONES":
            for exe in self.app.excepciones:
                self.tree_gestos.insert("", tk.END, values=("🚫 Excepción", "Ninguna", exe))
        elif ctx == "MODO SIGILO":
            for exe in getattr(self.app, 'sigilo', []):
                self.tree_gestos.insert("", tk.END, values=("👻 Modo Sigilo", "Tinta Invisible", exe))
        else:
            diccionario = self.app.gestos_app.get(ctx, {})
            for g, cmds in diccionario.items():
                if isinstance(cmds, dict):
                    for mod, cmd in cmds.items():
                        mod_visual = mod.upper() if mod != 'default' else 'NORMAL'
                        self.tree_gestos.insert("", tk.END, values=(g, mod_visual, cmd))
                else:
                    self.tree_gestos.insert("", tk.END, values=(g, 'NORMAL', cmds))

    def actualizar_lista_gestor(self):
        self.listbox_plantillas.delete(0, tk.END)
        for p in sorted(self.app.plantillas.keys()):
            self.listbox_plantillas.insert(tk.END, p)



    def construir_interfaz(self):
        frame_botones = tk.Frame(self.ventana, bg="#dcdcdc", pady=10)
        frame_botones.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Button(frame_botones, text="Guardar y Cerrar", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                  command=self.btn_guardar_cerrar).pack(side=tk.RIGHT, padx=10)
        tk.Button(frame_botones, text="Cancelar", bg="#f44336", fg="white", command=self.al_cerrar_x).pack(
            side=tk.RIGHT, padx=5)
        tk.Button(frame_botones, text="Aplicar", bg="#2196F3", fg="white", command=self.btn_aplicar).pack(side=tk.RIGHT,
                                                                                                          padx=5)

        # ==========================================
        # NUEVO: El botón de RESET
        # ==========================================
        def btn_reset_ajustes():
            if messagebox.askyesno("Resetear Ajustes", "¿Volver a los valores por defecto del motor de dibujo?",
                                   parent=self.ventana):
                self.escala_grosor.set(3)  # Grosor por defecto
                self.escala_tolerancia.set(25)  # 25% de tolerancia
                self.entry_tiempo.delete(0, tk.END)
                self.entry_tiempo.insert(0, "1.5")  # 1.5 segundos
                self.var_arranque.set(False)
                self.var_jedi.set(True)
                actualizar_preview_grosor()  # Actualizamos el visor visual

        tk.Button(frame_botones, text="🔄 Reset", bg="#FF9800", fg="white", command=btn_reset_ajustes).pack(side=tk.LEFT,
                                                                                                           padx=10)
        # ==========================================

        notebook = ttk.Notebook(self.ventana)

        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ==========================================
        # NACIMIENTO DE LAS 4 PESTAÑAS
        # ==========================================
        tab_atajos = ttk.Frame(notebook)
        notebook.add(tab_atajos, text="🚀 Atajos y Config")

        tab_plantillas = ttk.Frame(notebook)
        notebook.add(tab_plantillas, text="📐 Gestor Plantillas")

        tab_colores = ttk.Frame(notebook)
        notebook.add(tab_colores, text="🎨 Colores")

        tab_preferencias = ttk.Frame(notebook)
        notebook.add(tab_preferencias, text="⚙️ Preferencias")

        # ==========================================
        # RESTAURACIÓN: Contenido de la Pestaña COLORES
        # ==========================================
        if not hasattr(self.app, 'colores') or not getattr(self.app, 'colores'):
            self.app.colores = {
                "normal": "#FF0000", "letras": "#FF00FF",
                "middle": "#00FFFF", "right": "#008080", "x1": "#800080", "x2": "#000080",
                "ctrl": "#00FF00", "shift": "#0000FF", "alt": "#FF9800", "space": "#FFFF00"
            }

        frame_colores = tk.Frame(tab_colores, padx=20, pady=20)
        frame_colores.pack(fill=tk.BOTH, expand=True)

        def cambiar_color(clave, boton_visual):
            # Semáforo para evitar que se abran múltiples ventanas de color a la vez
            if getattr(self.app, 'dialogo_color_abierto', False):
                return

            self.app.dialogo_color_abierto = True
            color_actual = self.app.colores.get(clave, "#FFFFFF")
            # Necesitas tener 'from tkinter import colorchooser' arriba del todo
            _, nuevo_hex = colorchooser.askcolor(title=f"Elige color para {clave}", initialcolor=color_actual)

            if nuevo_hex:
                self.app.colores[clave] = nuevo_hex
                boton_visual.config(bg=nuevo_hex)

            self.app.dialogo_color_abierto = False

        nombres_colores = [
            ("Trazo Normal", "normal"), ("Letras (A-Z)", "letras"),
            ("Clic Central", "middle"),
            ("Botón X1", "x1"), ("Botón X2", "x2"),
            ("Tecla Ctrl", "ctrl"), ("Tecla Shift", "shift"),
            ("Tecla Alt", "alt"), ("Espaciadora", "space")
        ]

        # El truco matemático de la cuadrícula para alinear los botones
        for i, (nombre_bonito, clave_interna) in enumerate(nombres_colores):
            fila = i // 2
            columna_base = (i % 2) * 2

            tk.Label(frame_colores, text=nombre_bonito, font=("Arial", 9, "bold")).grid(row=fila, column=columna_base,
                                                                                        pady=10, sticky="w")

            color_guardado = self.app.colores.get(clave_interna, "#FFFFFF")
            btn_color = tk.Button(frame_colores, width=6, bg=color_guardado, relief="ridge", cursor="hand2")
            btn_color.config(command=lambda c=clave_interna, b=btn_color: cambiar_color(c, b))
            btn_color.grid(row=fila, column=columna_base + 1, padx=(10, 30), pady=10)
        # ==========================================

        # ==========================================
        # CONTENIDO DE LA PESTAÑA PREFERENCIAS
        # ==========================================
        frame_pref = tk.Frame(tab_preferencias, padx=20, pady=20)
        frame_pref.pack(fill=tk.BOTH, expand=True)

        self.var_arranque = tk.BooleanVar(value=getattr(self.app, 'arranque_automatico', False))
        tk.Checkbutton(frame_pref, text="Arrancar OpenStroke con Windows", variable=self.var_arranque,
                       font=("Arial", 10, "bold")).pack(anchor="w", pady=10)

        self.var_jedi = tk.BooleanVar(value=getattr(self.app, 'poderes_jedi', True))
        tk.Checkbutton(frame_pref, text="Poderes Jedi (Manipular ventanas con clic derecho)", variable=self.var_jedi,
                       font=("Arial", 10, "bold"), fg="#FF5722").pack(anchor="w", pady=10)

        self.var_splash = tk.BooleanVar(value=getattr(self.app, 'mostrar_splash', False))
        tk.Checkbutton(frame_pref, text="Mostrar Pantalla de Carga (Splash Screen) al iniciar",
                       variable=self.var_splash, font=("Arial", 10, "bold"), fg="#2196F3").pack(anchor="w", pady=10)

        # ==========================================
        # NUEVA ZONA: APARIENCIA DEL TRAZO
        # ==========================================
        frame_apariencia = tk.LabelFrame(frame_pref, text="🎨 Apariencia del Trazo", font=("Arial", 10, "bold"), padx=15,
                                         pady=10)
        frame_apariencia.pack(fill=tk.X, pady=15)

        # Deslizador de Grosor Principal
        tk.Label(frame_apariencia, text="Grosor de la Línea:", font=("Arial", 9)).grid(row=0, column=0, sticky="e",
                                                                                       pady=5)
        self.escala_grosor = tk.Scale(frame_apariencia, from_=1, to=15, orient="horizontal", length=150, showvalue=0)
        self.escala_grosor.set(self.app.grosor_linea)
        self.escala_grosor.grid(row=0, column=1, padx=10)

        # Deslizador del Borde Blanco
        tk.Label(frame_apariencia, text="Aura Blanca (0 = Apagado):", font=("Arial", 9)).grid(row=1, column=0,
                                                                                              sticky="e", pady=5)
        self.escala_borde = tk.Scale(frame_apariencia, from_=0, to=12, orient="horizontal", length=150, showvalue=0)
        self.escala_borde.set(getattr(self.app, 'grosor_borde', 6))
        self.escala_borde.grid(row=1, column=1, padx=10)

        # El Visor Holográfico Oscuro
        self.canvas_preview = tk.Canvas(frame_apariencia, width=80, height=50, bg="#282C34", highlightthickness=0)
        self.canvas_preview.grid(row=0, column=2, rowspan=2, padx=30)

        # Primero el borde blanco por debajo, luego el trazo magenta por encima
        g_linea = self.app.grosor_linea
        g_borde = getattr(self.app, 'grosor_borde', 6)
        self.borde_preview = self.canvas_preview.create_line(10, 25, 70, 25, fill="#FEFEFE", width=g_linea + g_borde,
                                                             capstyle=tk.ROUND)
        self.linea_preview = self.canvas_preview.create_line(10, 25, 70, 25, fill="#FF00FF", width=g_linea,
                                                             capstyle=tk.ROUND)

        def actualizar_preview_apariencia(*args):
            g = self.escala_grosor.get()
            b = self.escala_borde.get()
            self.canvas_preview.itemconfig(self.linea_preview, width=g)
            if b > 0:
                self.canvas_preview.itemconfig(self.borde_preview, width=g + b, state="normal")
            else:
                self.canvas_preview.itemconfig(self.borde_preview, state="hidden")

        self.escala_grosor.config(command=actualizar_preview_apariencia)
        self.escala_borde.config(command=actualizar_preview_apariencia)
        # ==========================================


        # ==========================================
        # --- PESTAÑA 1 (ATAJOS) REDISEÑADA ---
        frame_top = tk.Frame(tab_atajos)
        frame_top.pack(fill=tk.X, pady=15, padx=10)

        tk.Label(frame_top, text="Tolerancia (%):", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(5, 0))
        self.escala_tolerancia = tk.Scale(frame_top, from_=10, to=60, orient="horizontal", length=120)
        self.escala_tolerancia.set(int(self.app.umbral_tolerancia * 100))
        self.escala_tolerancia.pack(side=tk.LEFT, padx=5)

        tk.Label(frame_top, text="Tiempo(s):", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(20, 0))
        self.entry_tiempo = tk.Entry(frame_top, justify="center", width=6)
        self.entry_tiempo.insert(0, str(self.app.tiempo_maximo_s))
        self.entry_tiempo.pack(side=tk.LEFT)

        tk.Button(frame_top, text="✏️ Grabar Forma", bg="#9c27b0", fg="white", font=("Arial", 9, "bold"),
                  command=self.abrir_ventana_grabacion).pack(side=tk.RIGHT, padx=5)

        tk.Frame(tab_atajos, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=5)
        # --- FIN DEL REDISEÑO DE PESTAÑAS ---

        # --- SECCIÓN: APP ACTIVA ---
        frame_contexto = tk.Frame(tab_atajos)
        frame_contexto.pack(fill=tk.X, pady=2)
        tk.Label(frame_contexto, text="App Activa:", font=("Arial", 10, "bold"), fg="#2196F3").pack(side=tk.LEFT)

        self.combo_contexto = ttk.Combobox(frame_contexto, state="readonly", justify="center", font=("Arial", 10))

        def refrescar_combo():
            self.combo_contexto['values'] = ["GLOBAL", "EXCEPCIONES", "MODO SIGILO"] + [a for a in
                                                                                        self.app.gestos_app.keys() if
                                                                                        a != "GLOBAL"]

        refrescar_combo()
        self.combo_contexto.set("GLOBAL")
        self.combo_contexto.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def btn_nueva_app():
            ctx = self.combo_contexto.get()
            if ctx == "EXCEPCIONES":
                exe = simpledialog.askstring("Excepción", "Programa a ignorar (Ej: notepad.exe):", parent=self.ventana)
                if exe:
                    exe = exe.strip().upper()
                    if not exe.endswith(".EXE"): exe += ".EXE"
                    if exe not in self.app.excepciones:
                        self.app.excepciones.append(exe)
                        self.actualizar_lista_gestos()
            else:
                nueva = simpledialog.askstring("Nueva App", "Nombre del programa (Ej: chrome.exe):",
                                               parent=self.ventana)
                if nueva:
                    nueva = nueva.strip().upper()
                    if not nueva.endswith(".EXE"): nueva += ".EXE"
                    if nueva not in self.app.gestos_app: self.app.gestos_app[nueva] = {}
                    refrescar_combo()
                    self.combo_contexto.set(nueva)
                    self.actualizar_lista_gestos()

        tk.Button(frame_contexto, text="➕", bg="#4CAF50", fg="white", command=btn_nueva_app).pack(side=tk.RIGHT)

        # ==========================================
        # EL BUSCADOR DE EJECUTABLES (La Carpetita)
        # ==========================================
        def explorar_nueva_app():
            from tkinter import filedialog
            import os
            import win32com.client

            ruta_archivo = filedialog.askopenfilename(
                title="Selecciona el programa (.exe o .lnk)",
                filetypes=[("Programas y Accesos", "*.exe *.lnk"), ("Todos", "*.*")]
            )

            if ruta_archivo:
                # 1. MAGIA DESENCRIPTADORA
                if ruta_archivo.lower().endswith('.lnk'):
                    try:
                        shell = win32com.client.Dispatch("WScript.Shell")
                        acceso = shell.CreateShortCut(ruta_archivo)
                        ruta_archivo = acceso.Targetpath
                    except Exception as e:
                        print(f"Error al leer .lnk: {e}")

                # 2. Extraemos el nombre en mayúsculas
                exe = os.path.basename(ruta_archivo).upper()

                # 3. Escudo por si es un acceso raro de la Windows Store sin extensión
                if not exe.endswith(".EXE") and "." not in exe:
                    exe += ".EXE"

                ctx = self.combo_contexto.get()

                # 4. LA LÓGICA CORREGIDA
                if ctx == "EXCEPCIONES":
                    if exe not in self.app.excepciones:
                        self.app.excepciones.append(exe)
                        self.actualizar_lista_gestos()

                elif ctx == "MODO SIGILO":
                    if exe not in getattr(self.app, 'sigilo', []):
                        self.app.sigilo.append(exe)
                        self.actualizar_lista_gestos()

                else:  # <--- ¡AQUÍ ESTABA EL BUG! Antes bloqueábamos el GLOBAL
                    if exe not in self.app.gestos_app:
                        self.app.gestos_app[exe] = {}
                    refrescar_combo()
                    self.combo_contexto.set(exe)
                    self.actualizar_lista_gestos()

        tk.Button(frame_contexto, text="📁", bg="#FFC107", fg="black", command=explorar_nueva_app).pack(side=tk.RIGHT,
                                                                                                       padx=5)

        # ==========================================                                                                                               padx=5)

        # ==========================================

        # ==========================================
        # NUEVO: Botón de eliminar App con escudo protector
        # ==========================================
        def btn_borrar_app():
            ctx = self.combo_contexto.get()

            # El escudo: Protegemos el núcleo del programa
            if ctx in ["GLOBAL", "EXCEPCIONES", "MODO SIGILO"]:
                messagebox.showwarning("Aviso", f"🚫 La zona '{ctx}' es vital y no se puede borrar.")
                return

            # Preguntamos por seguridad antes de fulminar los datos
            if messagebox.askyesno("Confirmar",
                                   f"¿Estás seguro de eliminar el perfil para '{ctx}' y perder todos sus atajos?",
                                   parent=self.ventana):
                del self.app.gestos_app[ctx]  # Lo borramos de la memoria
                refrescar_combo()  # Actualizamos el desplegable
                self.combo_contexto.set("GLOBAL")  # Volvemos a la zona segura
                self.actualizar_lista_gestos()

        tk.Button(frame_contexto, text="➖", bg="#f44336", fg="white", command=btn_borrar_app).pack(side=tk.RIGHT,
                                                                                                   padx=5)

        # ==========================================

        def al_cambiar_contexto(event):
            self.actualizar_lista_gestos()
            estado = "disabled" if self.combo_contexto.get() in ["EXCEPCIONES", "MODO SIGILO"] else "readonly"
            estado_cmd = "disabled" if self.combo_contexto.get() in ["EXCEPCIONES", "MODO SIGILO"] else "normal"
            self.combo_modificador.config(state=estado)
            self.entry_comando.config(state=estado_cmd)


        # ¡OJO AQUÍ! Esta línea ya está correctamente alienada fuera de la función superior
        self.combo_contexto.bind("<<ComboboxSelected>>", al_cambiar_contexto)

        # --- SECCIÓN: NUEVO GESTO / ACORDES ---
        frame_gestos = tk.Frame(tab_atajos)
        frame_gestos.pack(pady=10)

        tk.Label(frame_gestos, text="Capa / Botón", font=("Arial", 8, "bold")).grid(row=0, column=0)
        tk.Label(frame_gestos, text="Forma", font=("Arial", 8, "bold")).grid(row=0, column=1)
        tk.Label(frame_gestos, text="Comando", font=("Arial", 8, "bold")).grid(row=0, column=2)


        self.combo_modificador = ttk.Combobox(frame_gestos, state="readonly", justify="center", width=16)

        # Generamos la lista del abecedario
        teclas_letras = [f"Tecla {letra.upper()}" for letra in string.ascii_lowercase]

        # Agrupamos los botones del ratón (Sin el izquierdo, que es sagrado)
        botones_raton = ["Clic Central",  "Botón X1", "Botón X2"]

        # Sumamos todo: Clásicos + Ratón + Abecedario
        self.combo_modificador['values'] = ["Normal", "Ctrl", "Shift", "Alt", "Espacio"] + botones_raton + teclas_letras
        self.combo_modificador.set("Normal")
        self.combo_modificador.grid(row=1, column=0, padx=5)





        self.combo_plantillas = ttk.Combobox(frame_gestos, state="readonly", justify="center", width=15)
        self.actualizar_desplegable_plantillas()
        self.combo_plantillas.grid(row=1, column=1, padx=5)

        frame_input_comando = tk.Frame(frame_gestos)
        frame_input_comando.grid(row=1, column=2, padx=5)

        self.entry_comando = tk.Entry(frame_input_comando, width=30, justify="center")
        self.entry_comando.pack(side=tk.LEFT)

        # ==========================================
        # NUEVO: El Explorador de Archivos Visual
        # ==========================================
        def buscar_archivo():
            import win32com.client  # La librería mágica

            ruta = filedialog.askopenfilename(
                title="Selecciona un programa o archivo",
                # AÑADIMOS SOPORTE PARA .LNK
                filetypes=(("Ejecutables y Accesos", "*.exe *.lnk"), ("Todos los archivos", "*.*"))
            )
            if ruta:
                # ==========================================
                # MAGIA DESENCRIPTADORA
                # ==========================================
                if ruta.lower().endswith('.lnk'):
                    try:
                        shell = win32com.client.Dispatch("WScript.Shell")
                        acceso = shell.CreateShortCut(ruta)
                        ruta = acceso.Targetpath
                    except Exception:
                        pass
                # ==========================================

                self.entry_comando.config(state="normal")
                self.entry_comando.delete(0, tk.END)
                self.entry_comando.insert(0, f'"{ruta}"')

        tk.Button(frame_input_comando, text="📁", bg="#FFC107", fg="black", font=("Arial", 8),
                  command=buscar_archivo).pack(side=tk.LEFT, padx=(5, 0))
        # ==========================================

        tk.Button(frame_input_comando, text="❓", bg="#2196F3", fg="white", font=("Arial", 8, "bold"),
                  command=self.abrir_guia_comandos).pack(side=tk.LEFT, padx=(5, 0))

        # ==========================================
        # NUEVO: Visor de Animación Holográfica
        # ==========================================
        # 1. Creamos la pantallita (Canvas) a la derecha del todo
        self.canvas_animacion = tk.Canvas(frame_gestos, width=80, height=80, bg="#1e1e1e", highlightthickness=1,
                                          highlightbackground="#4CAF50")
        self.canvas_animacion.grid(row=0, column=4, rowspan=2, padx=15)
        self.canvas_animacion.create_text(40, 40, text="Visor", fill="#555555", font=("Arial", 8, "bold"))

        # 2. El motor matemático que anima el trazo (Ahora en Bucle)
        def reproducir_animacion(nombre_forma):
            # Escudo de seguridad: Cancelamos el bucle anterior si cambias de forma rápido
            if hasattr(self, 'id_animacion'):
                self.ventana.after_cancel(self.id_animacion)

            self.canvas_animacion.delete("all")
            puntos = self.app.plantillas.get(nombre_forma)

            if not puntos or len(puntos) < 2:
                self.canvas_animacion.create_text(40, 40, text="Sin\ndatos", fill="#ff5555", font=("Arial", 8))
                return

            xs = [p[0] for p in puntos];
            ys = [p[1] for p in puntos]
            min_x, max_x = min(xs), max(xs);
            min_y, max_y = min(ys), max(ys)
            ancho_p = max_x - min_x if max_x != min_x else 1
            alto_p = max_y - min_y if max_y != min_y else 1

            escala = min(60 / ancho_p, 60 / alto_p)
            cx, cy = 40, 40

            puntos_norm = []
            for x, y in puntos:
                nx = cx + (x - (min_x + max_x) / 2) * escala
                ny = cy + (y - (min_y + max_y) / 2) * escala
                puntos_norm.append((nx, ny))

            self.anim_step = 0

            def dibujar_paso():
                # Escudo protector: Si el lienzo fue destruido, abortamos la animación
                if not hasattr(self, 'canvas_animacion') or not self.canvas_animacion.winfo_exists(): return

                if self.anim_step < len(puntos_norm) - 1:

                    p1 = puntos_norm[self.anim_step]
                    p2 = puntos_norm[self.anim_step + 1]
                    self.canvas_animacion.create_line(p1[0], p1[1], p2[0], p2[1], fill="#00FF00", width=3,
                                                      capstyle=tk.ROUND, smooth=True)
                    self.anim_step += 1
                    self.id_animacion = self.canvas_animacion.after(15, dibujar_paso)
                else:
                    # ¡MAGIA! Cuando termina, borra la pantalla y vuelve a empezar tras 1 segundo
                    self.id_animacion = self.canvas_animacion.after(1000, lambda: reproducir_animacion(nombre_forma))

            dibujar_paso()
        # 3. Activamos el proyector si el usuario cambia el desplegable a mano
        self.combo_plantillas.bind("<<ComboboxSelected>>", lambda e: reproducir_animacion(self.combo_plantillas.get()))

        # ==========================================
        def guardar_nuevo_elemento():
            ctx = self.combo_contexto.get()
            g = self.combo_plantillas.get()
            c = self.entry_comando.get().strip()
            mod_visual = self.combo_modificador.get()

            if ctx != "EXCEPCIONES":
                if not g or g.startswith("("): return messagebox.showwarning("Aviso", "Graba una Forma primero.",
                                                                             parent=self.ventana)
                if not c: return messagebox.showwarning("Aviso", "Escribe un comando.", parent=self.ventana)

                # ==========================================
                # EL TRADUCTOR (Con la indentación corregida)
                # ==========================================
                if mod_visual == "Normal":
                    mod_interno = "default"
                elif mod_visual == "Espacio":
                    mod_interno = "space"
                elif mod_visual == "Clic Central":
                    mod_interno = "middle"
                elif mod_visual == "Clic Derecho":
                    mod_interno = "right"
                elif mod_visual == "Botón X1":
                    mod_interno = "x1"
                elif mod_visual == "Botón X2":
                    mod_interno = "x2"
                elif mod_visual.startswith("Tecla "):
                    # Extrae la letra exacta. Ej: "Tecla H" -> "h"
                    mod_interno = mod_visual.replace("Tecla ", "").lower()
                else:
                    mod_interno = mod_visual.lower()  # Para Ctrl, Shift y Alt
                # ==========================================

            if ctx == "EXCEPCIONES":
                exe = simpledialog.askstring("Excepción", "Ejecutable a ignorar:")
                if exe:
                    exe = exe.strip().upper()
                    if not exe.endswith(".EXE"): exe += ".EXE"
                    if exe not in self.app.excepciones: self.app.excepciones.append(exe)
            else:
                if ctx not in self.app.gestos_app: self.app.gestos_app[ctx] = {}
                if g not in self.app.gestos_app[ctx]: self.app.gestos_app[ctx][g] = {}
                if not isinstance(self.app.gestos_app[ctx][g], dict):
                    self.app.gestos_app[ctx][g] = {'default': self.app.gestos_app[ctx][g]}
                self.app.gestos_app[ctx][g][mod_interno] = c
                self.entry_comando.delete(0, tk.END)

            self.actualizar_lista_gestos()


        tk.Button(frame_gestos, text="Añadir ↓", command=guardar_nuevo_elemento).grid(row=1, column=3, padx=5)

        # ==========================================
        # ESTILOS PREMIUM PARA LA TABLA Y COMBOBOX
        # ==========================================
        estilo = ttk.Style()
        estilo.theme_use("default")

        # 1. Cabeceras y Filas
        estilo.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#e0e0e0")
        estilo.configure("Treeview", font=("Arial", 10), rowheight=35)

        # 2. ¡EL TRUCO VISUAL! Forzamos el fondo blanco en los Combobox 'readonly'
        estilo.map('TCombobox', fieldbackground=[('readonly', 'white')], selectbackground=[('readonly', '#0078D7')])
        # ==========================================

        frame_lista = tk.Frame(tab_atajos)
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=5)

        columnas = ("forma", "capa", "comando")
        self.tree_gestos = ttk.Treeview(frame_lista, columns=columnas, show="headings", height=12)

        # ==========================================
        # NUEVO: Ordenar columnas al hacer clic (SIN BUG DE TCL)
        # ==========================================
        # 1. Le damos una memoria estática a la tabla
        self.direcciones_orden = {"forma": False, "capa": False, "comando": False}

        def ordenar_columna(tv, col):
            # 2. Leemos la memoria para saber en qué dirección toca ordenar
            reverso = self.direcciones_orden[col]

            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            l.sort(reverse=reverso)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            # 3. Guardamos la dirección contraria para el siguiente clic
            self.direcciones_orden[col] = not reverso

        # 4. Asignamos los comandos UNA SOLA VEZ para no marear al recolector de basura de Tkinter
        self.tree_gestos.heading("forma", text="Forma / Gesto",
                                 command=lambda: ordenar_columna(self.tree_gestos, "forma"))
        self.tree_gestos.heading("capa", text="Tecla / Capa", command=lambda: ordenar_columna(self.tree_gestos, "capa"))
        self.tree_gestos.heading("comando", text="Acción / Comando",
                                 command=lambda: ordenar_columna(self.tree_gestos, "comando"))

        # ==========================================


        self.tree_gestos.heading("forma", text="Forma / Gesto")
        self.tree_gestos.heading("capa", text="Tecla / Capa")
        self.tree_gestos.heading("comando", text="Acción / Comando")

        self.tree_gestos.column("forma", width=120, anchor=tk.CENTER)
        self.tree_gestos.column("capa", width=120, anchor=tk.CENTER)
        self.tree_gestos.column("comando", width=350, anchor=tk.W)

        self.tree_gestos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_gestos.yview)
        self.tree_gestos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ==========================================
        # EVENTO: Clic en la Tabla (Mucho más limpio ahora)
        # ==========================================
        def al_seleccionar_gesto(event):
            seleccion = self.tree_gestos.selection()
            if not seleccion: return

            # Extraemos los valores de la fila directamente separados
            valores = self.tree_gestos.item(seleccion[0], "values")
            forma, capa_visual, comando = valores

            ctx = self.combo_contexto.get()

            if ctx == "EXCEPCIONES":
                self.entry_comando.config(state="normal")
                self.entry_comando.delete(0, tk.END)
                self.entry_comando.insert(0, comando)
                self.entry_comando.config(state="disabled")
                return

            import string


            # Añadimos los mapeos del ratón a nuestro diccionario inverso
            mods_inversos = {
                "NORMAL": "Normal", "CTRL": "Ctrl", "SHIFT": "Shift", "ALT": "Alt", "SPACE": "Espacio",
                "LEFT": "Clic Izquierdo", "MIDDLE": "Clic Central",
                "X1": "Botón X1", "X2": "Botón X2"
            }
            # Le sumamos el abecedario dinámicamente
            for letra in string.ascii_lowercase:
                mods_inversos[letra.upper()] = f"Tecla {letra.upper()}"

            mod_visual_combo = mods_inversos.get(capa_visual.upper(), "Normal")


            # Rellenamos los campos superiores
            self.combo_plantillas.set(forma)
            self.combo_modificador.set(mod_visual_combo)
            self.entry_comando.config(state="normal")
            self.entry_comando.delete(0, tk.END)
            self.entry_comando.insert(0, comando)
            # ==========================================
            # NUEVO: Encendemos el cine al hacer clic
            reproducir_animacion(forma)
            # ==========================================
        self.tree_gestos.bind("<<TreeviewSelect>>", al_seleccionar_gesto)

        # ==========================================
        # NUEVO: Borrar atajo de la tabla
        # ==========================================
        def borrar_atajo():
            seleccion = self.tree_gestos.selection()
            if not seleccion: return

            # Cogemos la fila seleccionada
            valores = self.tree_gestos.item(seleccion[0], "values")
            forma, capa_visual, comando = valores
            ctx = self.combo_contexto.get()

            if ctx == "EXCEPCIONES":
                if comando in self.app.excepciones: self.app.excepciones.remove(comando)
            elif ctx == "MODO SIGILO":
                if comando in self.app.sigilo: self.app.sigilo.remove(comando)
            else:
                mod = capa_visual.lower() if capa_visual != 'NORMAL' else 'default'
                if ctx in self.app.gestos_app and forma in self.app.gestos_app[ctx]:
                    if isinstance(self.app.gestos_app[ctx][forma], dict):
                        if mod in self.app.gestos_app[ctx][forma]:
                            del self.app.gestos_app[ctx][forma][mod]
                        if not self.app.gestos_app[ctx][forma]:
                            del self.app.gestos_app[ctx][forma]
                    else:
                        del self.app.gestos_app[ctx][forma]
            self.actualizar_lista_gestos()

        tk.Button(frame_lista, text="🗑️", bg="#f44336", fg="white", command=borrar_atajo, width=4).pack(side=tk.RIGHT,
                                                                                                        padx=5)

        self.actualizar_lista_gestos()  # Rellenamos la tabla al arrancar

        # ==========================================
        # NUEVO: Despertar el visor al iniciar
        # ==========================================
        # Si hay algo seleccionado y no es el texto por defecto, lo animamos
        forma_actual = self.combo_plantillas.get()
        if forma_actual and not forma_actual.startswith("("):
            self.ventana.after(200, lambda: self.combo_plantillas.event_generate("<<ComboboxSelected>>"))
        # ==========================================

        # --- PESTAÑA 2: GESTOR DE PLANTILLAS ---
        tk.Label(tab_plantillas, text="Gestiona las formas geométricas del motor.", pady=10).pack()
        frame_lista_plan = tk.Frame(tab_plantillas)
        frame_lista_plan.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.listbox_plantillas = tk.Listbox(frame_lista_plan, font=("Consolas", 11), justify="center")
        self.listbox_plantillas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        frame_bot_plan = tk.Frame(frame_lista_plan)
        frame_bot_plan.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        self.actualizar_lista_gestor()

        def renombrar():
            sel = self.listbox_plantillas.curselection()
            if not sel: return
            viejo = self.listbox_plantillas.get(sel[0])
            nuevo = simpledialog.askstring("Renombrar", f"Nuevo nombre para '{viejo}':", initialvalue=viejo)
            if nuevo and nuevo.strip().upper() != viejo:
                nuevo = nuevo.strip().upper()
                self.app.plantillas[nuevo] = self.app.plantillas.pop(viejo)
                for ctx in self.app.gestos_app:
                    if viejo in self.app.gestos_app[ctx]:
                        self.app.gestos_app[ctx][nuevo] = self.app.gestos_app[ctx].pop(viejo)
                self.actualizar_lista_gestor()
                self.actualizar_lista_gestos()
                self.actualizar_desplegable_plantillas()

        def eliminar():
            sel = self.listbox_plantillas.curselection()
            if not sel: return
            nombre = self.listbox_plantillas.get(sel[0])
            if messagebox.askyesno("Borrar", f"¿Borrar '{nombre}' y sus atajos?", parent=self.ventana):
                del self.app.plantillas[nombre]
                for ctx in self.app.gestos_app:
                    if nombre in self.app.gestos_app[ctx]:
                        del self.app.gestos_app[ctx][nombre]
                self.actualizar_lista_gestor()
                self.actualizar_lista_gestos()
                self.actualizar_desplegable_plantillas()

        tk.Button(frame_bot_plan, text="Renombrar ✏️", bg="#FF9800", fg="white", width=15, pady=5,
                  command=renombrar).pack(pady=5)
        tk.Button(frame_bot_plan, text="Eliminar 🗑️", bg="#f44336", fg="white", width=15, pady=5,
                  command=eliminar).pack(pady=5)