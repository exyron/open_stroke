from PIL import Image, ImageDraw
import os


def fabricar_iconos():
    # Nos aseguramos de guardar los archivos en la carpeta actual
    ruta_base = os.path.dirname(os.path.abspath(__file__))

    # --- 1. ICONO ACTIVO (Verde con símbolo de 'Play') ---
    # Creamos un lienzo transparente de 64x64 (RGBA)
    img_activa = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d_activa = ImageDraw.Draw(img_activa)

    # Dibujamos un círculo verde
    d_activa.ellipse([4, 4, 60, 60], fill=(76, 175, 80))
    # Dibujamos un triángulo blanco en el centro
    d_activa.polygon([(24, 18), (46, 32), (24, 46)], fill="white")

    ruta_activa = os.path.join(ruta_base, "icon_active.png")
    img_activa.save(ruta_activa)
    print(f"✅ Creado: {ruta_activa}")

    # --- 2. ICONO PAUSADO (Rojo con símbolo de 'Pausa') ---
    img_pausa = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d_pausa = ImageDraw.Draw(img_pausa)

    # Dibujamos un círculo rojo
    d_pausa.ellipse([4, 4, 60, 60], fill=(244, 67, 54))
    # Dibujamos las dos barras blancas verticales
    d_pausa.rectangle([22, 20, 28, 44], fill="white")
    d_pausa.rectangle([36, 20, 42, 44], fill="white")

    ruta_pausa = os.path.join(ruta_base, "icon_paused.png")
    img_pausa.save(ruta_pausa)
    print(f"✅ Creado: {ruta_pausa}")


if __name__ == "__main__":
    fabricar_iconos()
    print("¡Iconos generados con éxito! Ya puedes borrar este script si quieres.")