import math


class ReconocedorGestos:
    def __init__(self, num_puntos=64, tamano_cuadrado=250.0):
        self.num_puntos = num_puntos
        self.tamano_cuadrado = tamano_cuadrado

    def calcular_longitud(self, puntos):
        d = 0.0
        for i in range(1, len(puntos)):
            d += math.hypot(puntos[i][0] - puntos[i - 1][0], puntos[i][1] - puntos[i - 1][1])
        return d

    def remuestrear(self, puntos):
        if not puntos or len(puntos) < 2: return []
        I = self.calcular_longitud(puntos) / (self.num_puntos - 1)
        D = 0.0
        nuevos_puntos = [puntos[0]]
        puntos_temp = puntos.copy()
        i = 1

        while i < len(puntos_temp):
            p1 = puntos_temp[i - 1]
            p2 = puntos_temp[i]
            d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

            if (D + d) >= I:
                qx = p1[0] + ((I - D) / d) * (p2[0] - p1[0])
                qy = p1[1] + ((I - D) / d) * (p2[1] - p1[1])
                q = [qx, qy]
                nuevos_puntos.append(q)
                puntos_temp.insert(i, q)
                D = 0.0
            else:
                D += d
            i += 1

        if len(nuevos_puntos) == self.num_puntos - 1:
            nuevos_puntos.append(puntos[-1])
        return nuevos_puntos[:self.num_puntos]

    def escalar(self, puntos):
        """Escalado proporcional: mantiene la forma original sin deformar."""
        if not puntos: return []
        min_x = min(p[0] for p in puntos)
        max_x = max(p[0] for p in puntos)
        min_y = min(p[1] for p in puntos)
        max_y = max(p[1] for p in puntos)

        ancho = max_x - min_x
        alto = max_y - min_y

        lado_mayor = max(ancho, alto)
        if lado_mayor == 0: lado_mayor = 0.1

        puntos_escalados = []
        for p in puntos:
            qx = p[0] * (self.tamano_cuadrado / lado_mayor)
            qy = p[1] * (self.tamano_cuadrado / lado_mayor)
            puntos_escalados.append([qx, qy])
        return puntos_escalados

    def trasladar_al_origen(self, puntos):
        if not puntos: return []
        centro_x = sum(p[0] for p in puntos) / len(puntos)
        centro_y = sum(p[1] for p in puntos) / len(puntos)

        puntos_trasladados = []
        for p in puntos:
            qx = p[0] - centro_x
            qy = p[1] - centro_y
            puntos_trasladados.append([qx, qy])
        return puntos_trasladados

    # ==========================================
    # NUEVA IA: LÓGICA DE FORMAS Y ÁNGULOS
    # ==========================================
    def calcular_proporcion(self, puntos):
        """Calcula si la forma es cuadrada, muy alargada o muy ancha."""
        if not puntos: return 1.0
        min_x = min(p[0] for p in puntos)
        max_x = max(p[0] for p in puntos)
        min_y = min(p[1] for p in puntos)
        max_y = max(p[1] for p in puntos)
        ancho = max_x - min_x
        alto = max_y - min_y
        if alto < 0.01: return 999.0  # Evita la división por cero en líneas horizontales
        return ancho / alto

    def calcular_indice_curvatura(self, puntos):
        """Diferencia líneas rectas (\\) de formas con esquinas (L) o curvas."""
        if len(puntos) < 2: return 1.0
        longitud_total = self.calcular_longitud(puntos)

        # Distancia en línea recta como el vuelo de un pájaro (Inicio a Fin)
        distancia_vuelo = math.hypot(puntos[-1][0] - puntos[0][0], puntos[-1][1] - puntos[0][1])

        if distancia_vuelo < 0.01: return longitud_total  # Para formas cerradas (como un círculo)
        return longitud_total / distancia_vuelo
    # ==========================================

    def procesar_trazo(self, puntos_crudos):
        if len(puntos_crudos) < 10: return []
        p1 = self.remuestrear(puntos_crudos)
        p2 = self.escalar(p1)
        p3 = self.trasladar_al_origen(p2)
        return p3

    def calcular_distancia_trazo(self, trazo_dibujado, trazo_plantilla):
        if len(trazo_dibujado) != len(trazo_plantilla): return float('inf')

        # 1. Distancia Euclidiana Clásica (El algoritmo base)
        distancia_total = 0.0
        for i in range(len(trazo_dibujado)):
            distancia_total += math.hypot(trazo_dibujado[i][0] - trazo_plantilla[i][0],
                                          trazo_dibujado[i][1] - trazo_plantilla[i][1])
        distancia_base = distancia_total / len(trazo_dibujado)

        # ==========================================
        # 2. ANÁLISIS ESTRUCTURAL (Los multiplicadores)
        # ==========================================
        # Diferencia de Proporción
        prop_dibujo = self.calcular_proporcion(trazo_dibujado)
        prop_plantilla = self.calcular_proporcion(trazo_plantilla)
        diferencia_proporcion = abs(prop_dibujo - prop_plantilla)

        # Diferencia de Esquinas / Ángulos
        curv_dibujo = self.calcular_indice_curvatura(trazo_dibujado)
        curv_plantilla = self.calcular_indice_curvatura(trazo_plantilla)
        diferencia_curvatura = abs(curv_dibujo - curv_plantilla)

        # 3. La Sentencia Final
        # Si la estructura geométrica no coincide, inflamos la distancia artificialmente
        # para que el motor la perciba como un dibujo incorrecto y la rechace.
        multiplicador_castigo = 1.0

        # Las esquinas son muy importantes. Un pequeño desvío castiga severamente (x2.5)
        multiplicador_castigo += (diferencia_curvatura * 2.5)

        # Suavizamos el castigo de la proporción por si el usuario dibuja un poco estirado
        if diferencia_proporcion < 100:
            multiplicador_castigo += (diferencia_proporcion * 0.5)

        return distancia_base * multiplicador_castigo


    def reconocer(self, puntos_crudos, diccionario_plantillas, umbral_porcentaje):
        trazo_limpio = self.procesar_trazo(puntos_crudos)
        if not trazo_limpio or not diccionario_plantillas:
            return None, float('inf')

        mejor_coincidencia = None
        menor_distancia = float('inf')

        for nombre_plantilla, puntos_plantilla in diccionario_plantillas.items():
            distancia = self.calcular_distancia_trazo(trazo_limpio, puntos_plantilla)
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_coincidencia = nombre_plantilla

        umbral_aceptacion = self.tamano_cuadrado * umbral_porcentaje
        if menor_distancia < umbral_aceptacion:
            return mejor_coincidencia, menor_distancia
        else:
            return None, menor_distancia