
![splash](https://github.com/user-attachments/assets/29657696-b878-4187-8474-6aad428ba138)

# 🚀 OpenStroke

> **Ratón y teclado unidos.** Un motor avanzado de gestos de ratón para Windows, ligero, personalizable y de código abierto.

OpenStroke te permite controlar tu sistema operativo, ventanas y aplicaciones dibujando formas geométricas en la pantalla con el ratón. Incorpora atajos combinados con el teclado, poderes de manipulación de ventanas y una interfaz gráfica sin distracciones.

---

## ✨ Características Principales

* 🧠 **Motor Geométrico Inteligente:** Reconocimiento de trazos con tolerancia ajustable y soporte para "Acordes Jedi" (combinar un botón del ratón con teclas modificadoras como `Ctrl`, `Alt`, `Shift` o cualquier letra).
* 🛡️ **Escudo de Titanio (API Nativa):** Interacción a muy bajo nivel con Windows mediante `ctypes`. Discrimina procesos vitales del sistema y se protege a sí mismo de minimizaciones accidentales.
* 👻 **Poderes de Ventana:** Fija ventanas en primer plano (*Always on Top*), hazlas semitransparentes o minimízalas al instante directamente dibujando sobre ellas.
* 🎨 **Aura de Alto Contraste:** Renderizado dual del trazo. El programa dibuja un sutil halo blanco personalizable bajo tu trazo para garantizar su visibilidad sobre fondos muy oscuros o terminales.
* ⚡ **HUD Holográfico de Alto Rendimiento:** Notificaciones flotantes implementadas con *Object Pooling* (reciclaje de memoria) para evitar parpadeos y lag al encadenar gestos muy rápidos.
* 🎒 **Modo Portable:** Crea un archivo vacío llamado `portable.txt` junto al ejecutable y OpenStroke guardará tu configuración localmente sin tocar el Registro de Windows.

---

## 📦 Instalación (Para Usuarios)

1. Ve a la sección de **Releases** y descarga el instalador más reciente (`Instalar_OpenStroke.exe`) o la versión comprimida.
2. Sigue los pasos del instalador.
3. Haz clic en el icono de la bandeja del sistema (al lado del reloj de Windows) para abrir la ventana de configuración, ajustar tus colores, el grosor del trazo y añadir tus propios gestos.

---

## 🛠️ Ejecución desde el Código (Para Desarrolladores)

Si quieres clonar el proyecto, trastear con el código fuente y añadir tus propios superpoderes:

1. Clona este repositorio en tu ordenador:
   ```bash
   git clone [https://github.com/tu-usuario/open_stroke.git](https://github.com/tu-usuario/open_stroke.git)

2. Accede a la carpeta del proyecto:

Bash
    cd open_stroke
    
3.  Instala las dependencias necesarias leyendo el archivo de requisitos:

    pip install -r requirements.txt

4. Ejecuta el motor principal:

    python openstroke.py
   
(Nota: Para ver los registros internos del motor en tiempo real, puedes lanzarlo con el parámetro python openstroke.py --debug).

⚙️ Configuración Técnica
El "cerebro" de tus atajos se guarda en un archivo llamado gestos.yaml. Si lo instalas de forma tradicional, lo encontrarás en tu carpeta de usuario: %APPDATA%\OpenStroke\gestos.yaml. Si usas el Modo Portable, se creará junto al ejecutable.

📝 Licencia y Contribución
Este proyecto es de código abierto. Las contribuciones, sugerencias y reportes de errores (Issues) son más que bienvenidos. ¡Siéntete libre de hacer un Fork y mejorar el motor!
