"""
SmartCampus UTA — Estructuras de Datos Propias
Implementadas sin usar librerías de colecciones del lenguaje.
Cada estructura está ligada a un caso de uso real del sistema.
"""

# ═══════════════════════════════════════════════════════════════
# ESTRUCTURAS LINEALES
# ═══════════════════════════════════════════════════════════════

class NodoLista:
    """Nodo base para listas enlazadas"""
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None
        self.anterior = None  # Usado en lista doble


class ListaSimple:
    """
    Lista Simplemente Enlazada.
    Uso real: Catálogo dinámico de tipos de trámite disponibles.
    """
    def __init__(self):
        self.cabeza = None
        self.tamanio = 0

    def insertar_al_final(self, dato):
        nuevo = NodoLista(dato)
        if self.cabeza is None:
            self.cabeza = nuevo
        else:
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo
        self.tamanio += 1

    def eliminar(self, dato):
        actual = self.cabeza
        anterior = None
        while actual:
            if actual.dato == dato:
                if anterior:
                    anterior.siguiente = actual.siguiente
                else:
                    self.cabeza = actual.siguiente
                self.tamanio -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def buscar(self, dato):
        actual = self.cabeza
        while actual:
            if actual.dato == dato:
                return actual
            actual = actual.siguiente
        return None

    def a_lista(self):
        """Convierte a lista de Python para facilitar renderizado"""
        resultado = []
        actual = self.cabeza
        while actual:
            resultado.append(actual.dato)
            actual = actual.siguiente
        return resultado

    def esta_vacia(self):
        return self.cabeza is None

    def __len__(self):
        return self.tamanio


class ListaDoble:
    """
    Lista Doblemente Enlazada.
    Uso real: Navegación bidireccional del historial de expedientes/trámites.
    Permite avanzar y retroceder en el registro de acciones.
    """
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.tamanio = 0

    def insertar_al_final(self, dato):
        nuevo = NodoLista(dato)
        if self.cola is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
            self.cola = nuevo
        self.tamanio += 1

    def insertar_al_inicio(self, dato):
        nuevo = NodoLista(dato)
        if self.cabeza is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo
            self.cabeza = nuevo
        self.tamanio += 1

    def eliminar_ultimo(self):
        if self.cola is None:
            return None
        dato = self.cola.dato
        if self.cabeza == self.cola:
            self.cabeza = None
            self.cola = None
        else:
            self.cola = self.cola.anterior
            self.cola.siguiente = None
        self.tamanio -= 1
        return dato

    def a_lista_adelante(self):
        """Recorre de cabeza a cola"""
        resultado = []
        actual = self.cabeza
        while actual:
            resultado.append(actual.dato)
            actual = actual.siguiente
        return resultado

    def a_lista_atras(self):
        """Recorre de cola a cabeza (navegación inversa)"""
        resultado = []
        actual = self.cola
        while actual:
            resultado.append(actual.dato)
            actual = actual.anterior
        return resultado

    def esta_vacia(self):
        return self.cabeza is None

    def __len__(self):
        return self.tamanio


class ListaCircular:
    """
    Lista Circular.
    Uso real: Rotación Round-Robin de ventanillas de atención.
    Cuando llega al final de las ventanillas, regresa a la primera.
    """
    def __init__(self):
        self.cabeza = None
        self.tamanio = 0

    def insertar(self, dato):
        nuevo = NodoLista(dato)
        if self.cabeza is None:
            self.cabeza = nuevo
            nuevo.siguiente = self.cabeza
        else:
            actual = self.cabeza
            while actual.siguiente != self.cabeza:
                actual = actual.siguiente
            actual.siguiente = nuevo
            nuevo.siguiente = self.cabeza
        self.tamanio += 1

    def siguiente_turno(self):
        """
        Avanza al siguiente elemento de forma circular.
        Simula la rotación de ventanilla de atención (Round-Robin).
        """
        if self.cabeza is None:
            return None
        dato = self.cabeza.dato
        self.cabeza = self.cabeza.siguiente  # La lista rota
        return dato

    def ver_actual(self):
        if self.cabeza:
            return self.cabeza.dato
        return None

    def a_lista(self):
        if self.cabeza is None:
            return []
        resultado = []
        actual = self.cabeza
        for _ in range(self.tamanio):
            resultado.append(actual.dato)
            actual = actual.siguiente
        return resultado

    def esta_vacia(self):
        return self.cabeza is None

    def __len__(self):
        return self.tamanio


# ═══════════════════════════════════════════════════════════════
# PILA (LIFO)
# Uso real: Historial de acciones con posibilidad de "deshacer"
# ═══════════════════════════════════════════════════════════════
class Pila:
    def __init__(self):
        self._items = ListaSimple()  # Usa nuestra propia ListaSimple

    def apilar(self, item):
        self._items.insertar_al_final(item)

    def desapilar(self):
        """Elimina y retorna el último elemento (LIFO)"""
        if self.esta_vacia():
            return None
        # Recorrer hasta el penúltimo
        if self._items.cabeza.siguiente is None:
            dato = self._items.cabeza.dato
            self._items.cabeza = None
            self._items.tamanio -= 1
            return dato
        actual = self._items.cabeza
        while actual.siguiente.siguiente:
            actual = actual.siguiente
        dato = actual.siguiente.dato
        actual.siguiente = None
        self._items.tamanio -= 1
        return dato

    def ver_tope(self):
        """Ver el tope sin eliminar"""
        items = self._items.a_lista()
        return items[-1] if items else None

    def esta_vacia(self):
        return self._items.esta_vacia()

    def a_lista(self):
        return self._items.a_lista()

    def __len__(self):
        return len(self._items)


# ═══════════════════════════════════════════════════════════════
# COLA (FIFO)
# Uso real: Fila de atención estudiantil (Ventanilla Virtual)
# ═══════════════════════════════════════════════════════════════
class Cola:
    def __init__(self):
        self._items = ListaDoble()  # Usa nuestra ListaDoble (eficiente para cola)

    def encolar(self, item):
        """Agrega al final"""
        self._items.insertar_al_final(item)

    def desencolar(self):
        """Saca del frente (FIFO)"""
        if self.esta_vacia():
            return None
        dato = self._items.cabeza.dato
        if self._items.cabeza == self._items.cola:
            self._items.cabeza = None
            self._items.cola = None
        else:
            self._items.cabeza = self._items.cabeza.siguiente
            self._items.cabeza.anterior = None
        self._items.tamanio -= 1
        return dato

    def ver_frente(self):
        if self._items.cabeza:
            return self._items.cabeza.dato
        return None

    def esta_vacia(self):
        return self._items.esta_vacia()

    def a_lista(self):
        return self._items.a_lista_adelante()

    def __len__(self):
        return len(self._items)


# ═══════════════════════════════════════════════════════════════
# NODO DE ÁRBOL N-ARIO
# Uso real: Organigrama institucional (Rectorado → Facultad → Carrera)
# ═══════════════════════════════════════════════════════════════
class NodoArbol:
    def __init__(self, dato, id_ref=None):
        self.dato = dato
        self.id_ref = id_ref
        self.hijos = []

    def agregar_hijo(self, nodo_hijo):
        self.hijos.append(nodo_hijo)


class ArbolNArio:
    """
    Árbol N-Ario para representar la jerarquía organizacional.
    Cada nodo puede tener N hijos.
    """
    def __init__(self):
        self.raiz = None

    def establecer_raiz(self, nodo):
        self.raiz = nodo

    def buscar_nodo(self, nodo_actual, id_buscado):
        """Búsqueda recursiva por ID"""
        if nodo_actual is None:
            return None
        if nodo_actual.id_ref == id_buscado:
            return nodo_actual
        for hijo in nodo_actual.hijos:
            resultado = self.buscar_nodo(hijo, id_buscado)
            if resultado:
                return resultado
        return None

    def altura(self, nodo=None):
        """Calcula la altura del árbol recursivamente"""
        if nodo is None:
            nodo = self.raiz
        if nodo is None or not nodo.hijos:
            return 0
        return 1 + max(self.altura(h) for h in nodo.hijos)

    def contar_nodos(self, nodo=None):
        """Cuenta todos los nodos del árbol"""
        if nodo is None:
            nodo = self.raiz
        if nodo is None:
            return 0
        return 1 + sum(self.contar_nodos(h) for h in nodo.hijos)


# ═══════════════════════════════════════════════════════════════
# GRAFO (No dirigido, con pesos)
# Uso real: Mapa del campus — cálculo de rutas con Dijkstra
# ═══════════════════════════════════════════════════════════════
class Grafo:
    def __init__(self):
        self.nodos = {}

    def agregar_nodo(self, valor):
        if valor not in self.nodos:
            self.nodos[valor] = []

    def agregar_arista(self, desde, hacia, peso=1):
        if desde in self.nodos and hacia in self.nodos:
            self.nodos[desde].append({'destino': hacia, 'peso': float(peso)})
            self.nodos[hacia].append({'destino': desde, 'peso': float(peso)})

    def dijkstra(self, inicio, fin):
        """
        Algoritmo de Dijkstra para la ruta más corta.
        Complejidad: O((V + E) log V)
        """
        import heapq
        if inicio not in self.nodos or fin not in self.nodos:
            return None, float('infinity')

        distancias = {nodo: float('infinity') for nodo in self.nodos}
        distancias[inicio] = 0
        padres = {nodo: None for nodo in self.nodos}
        visitados = set()
        cola_prioridad = [(0, inicio)]

        while cola_prioridad:
            distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)

            if nodo_actual in visitados:
                continue
            visitados.add(nodo_actual)

            if nodo_actual == fin:
                break

            for vecino in self.nodos[nodo_actual]:
                destino = vecino['destino']
                if destino in visitados:
                    continue
                distancia = distancia_actual + vecino['peso']
                if distancia < distancias[destino]:
                    distancias[destino] = distancia
                    padres[destino] = nodo_actual
                    heapq.heappush(cola_prioridad, (distancia, destino))

        # Reconstruir camino
        ruta = []
        actual = fin
        while actual is not None:
            ruta.insert(0, actual)
            actual = padres[actual]

        if distancias[fin] == float('infinity'):
            return None, float('infinity')

        return ruta, distancias[fin]

    def total_nodos(self):
        return len(self.nodos)

    def total_aristas(self):
        total = sum(len(v) for v in self.nodos.values())
        return total // 2  # No dirigido, cada arista cuenta doble
