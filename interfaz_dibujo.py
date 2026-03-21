import tkinter as tk


class CapaTransparente:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Quita bordes y botones de cerrar
        self.root.attributes("-topmost", True)  # Siempre encima
        self.root.attributes("-transparentcolor", "white")  # El blanco será invisible
        self.root.config(bg="white")

        # Ocupamos toda la pantalla
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.root.state('zoomed')  # Maximizado

        self.linea_actual = None

    def empezar_trazo(self, x, y, color):
        self.puntos = [x, y]
        # Creamos una línea con el color de la capa (F1, CTRL, etc.)
        self.linea_actual = self.canvas.create_line(x, y, x, y, fill=color, width=3, capstyle=tk.ROUND)

    def actualizar_trazo(self, x, y):
        if self.linea_actual:
            self.puntos.extend([x, y])
            self.canvas.coords(self.linea_actual, *self.puntos)

    def limpiar(self):
        self.canvas.delete("all")