# 🏛️ SmartCampus UTA Web

> **Proyecto Integrador Universitario**  
> Aplicativo web orientado a la gestión de atención, trámites, organización documental y rutas internas del campus universitario, desarrollado con **Arquitectura por Capas** e implementación de **Estructuras de Datos Propias** (sin librerías nativas).

---

## 📋 Índice

1. [Objetivos del Proyecto](#1-objetivos-del-proyecto)
2. [Estructuras de Datos Implementadas (Core)](#2-estructuras-de-datos-implementadas-core)
3. [Arquitectura de Software (Por Capas)](#3-arquitectura-de-software-por-capas)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Instalación y Ejecución](#5-instalación-y-ejecución)
6. [Módulos del Sistema](#6-módulos-del-sistema)
7. [Base de Datos](#7-base-de-datos)
8. [Preguntas de Defensa (Tribunal)](#8-preguntas-de-defensa-tribunal)

---

## 🎯 1. Objetivos del Proyecto

El objetivo principal de **SmartCampus UTA** es demostrar la aplicación de la teoría de **Estructuras de Datos** dentro de una solución de software real y funcional, abandonando los ejercicios aislados de consola.

El sistema resuelve la descentralización de la información en el campus mediante:
* Una **Ventanilla Virtual** para filas de atención.
* Un **Módulo de Trámites** para seguimiento de papeleo.
* Un **Directorio (Organigrama)** institucional.
* Un **Mapa de Rutas** del campus.

---

## 🧠 2. Estructuras de Datos Implementadas (Core)

> ⚠️ **Restricción Académica Cumplida:** Ninguna de las estructuras de datos utiliza colecciones nativas de Python (como `list` o `collections.deque`). Todas fueron construidas desde cero usando programación orientada a objetos (Nodos y Punteros) en `app/estructuras/basicas.py`.

| Estructura de Dato | Implementación en el Sistema | Justificación Técnica |
| :--- | :--- | :--- |
| **Cola (Queue - FIFO)** | Fila de Ventanilla Virtual (Atención) | Modela perfectamente el orden de llegada: el primer estudiante en pedir turno es el primero en ser atendido. |
| **Pila (Stack - LIFO)** | Historial de Acciones (Deshacer) | Permite registrar eventos y deshacer la última acción realizada por un administrador (último en entrar, primero en salir). |
| **Lista Simplemente Enlazada** | Catálogo de Trámites Disponibles | Facilita el crecimiento dinámico y acceso secuencial a los tipos de servicios académicos. |
| **Lista Doblemente Enlazada** | Historial Dinámico de Solicitudes | Permite navegar el expediente de un trámite tanto hacia adelante como hacia atrás. |
| **Lista Circular** | Rotación de Ventanillas | Asignación Round-Robin. Si se acaba el personal, la rotación vuelve al primer responsable automáticamente. |
| **Árbol N-Ario** | Organigrama Institucional | Modela la jerarquía natural: *Rectorado → Facultades → Carreras*, donde un nodo padre tiene múltiples hijos. |
| **Grafo No Dirigido con Pesos**| Mapa del Campus Universitario | Modela las conexiones complejas (caminos) entre edificios y facultades (nodos) para calcular rutas mediante Dijkstra. |

---

## 🏗️ 3. Arquitectura de Software (Por Capas)

El proyecto respeta el principio de separación de responsabilidades:

1. **Capa de Presentación:** Interfaz de usuario responsiva (HTML, CSS variables globales, JS modular, Jinja2).
2. **Capa de Aplicación:** Controladores y Rutas (Flask Blueprints en `routes.py`) que orquestan los flujos.
3. **Capa de Dominio:** Donde viven nuestras **Estructuras de Datos Propias** y las reglas del negocio.
4. **Capa de Persistencia:** Manejo de la BD a través del ORM SQLAlchemy.
5. **Capa de Datos:** Base de datos relacional MySQL / SQLite.

---

## 💻 4. Stack Tecnológico

*   **Backend:** Python 3.10+ con microframework **Flask**.
*   **Base de Datos:** Relacional (SQLAlchemy ORM + MySQL/SQLite).
*   **Frontend:** HTML5, CSS3 (Variables, Dark Mode), Vanilla JavaScript, Bootstrap 5.
*   **Gestor de Dependencias:** `pip` y entorno virtual `venv`.
*   **Control de Versiones:** Git y GitHub.

---

## 🚀 5. Instalación y Ejecución

1. **Clonar y preparar el entorno:**
   ```powershell
   git clone <tu-repositorio>
   cd "APP estrctura de datos Proyecto"
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Ejecutar el servidor local:**
   ```powershell
   python run.py
   ```
   > El servidor se levantará en `http://127.0.0.1:5000`. Al arrancar, creará la base de datos automáticamente si no existe.

---

## 🧩 6. Módulos del Sistema

*   `/atencion/tomar_turno` -> Módulo de **Colas** para solicitar turnos por facultad.
*   `/atencion/pantalla` -> Pantalla de la ventanilla que desencola estudiantes en orden FIFO.
*   `/organizacion/directorio` -> Renderiza el **Árbol N-Ario** demostrando la relación jerárquica de la universidad.
*   `/auth/*` -> Gestión segura de inicio de sesión y registro de usuarios institucionales.

---

## 🗄️ 7. Base de Datos

El Modelo Entidad-Relación fue diseñado para garantizar integridad referencial, derivado directamente del análisis de requisitos:

*   **Acceso:** `usuarios`, `roles`.
*   **Procesos:** `turnos` (FK a usuarios y dependencias), `tramites`.
*   **Organización:** `dependencias` (Auto-referencial para soportar el Árbol).
*   **Trazabilidad:** `historial_acciones`.
*   **Rutas:** `puntos_ruta`, `conexiones_ruta`.

---

## 🎓 8. Preguntas de Defensa (Tribunal)

Guía rápida de justificaciones técnicas para la defensa del proyecto:

1. **¿Por qué eligieron una cola para el módulo de atención y no otra estructura?**
   *Porque la atención en ventanilla es estrictamente secuencial y justa (FIFO). Un árbol o pila romperían el orden cronológico de llegada.*

2. **¿Qué ventaja ofrece la lista circular en la rotación?**
   *Permite iterar sobre el personal de forma continua e infinita. Al llegar al final de la lista, el puntero del último nodo regresa a la cabeza (cero excepciones de desbordamiento).*

3. **¿Cómo justifican el uso de árbol en la clasificación organizacional?**
   *Una estructura administrativa no es lineal. Una facultad pertenece a la universidad, y múltiples carreras pertenecen a una facultad. Un árbol N-ario representa exactamente esa ramificación sin duplicar datos.*

4. **¿De qué manera la base de datos fue construida a partir de los requerimientos?**
   *Los requerimientos funcionales (RF1-RF11) identificaron los actores (Estudiante/Admin) y los objetos (Turnos, Trámites). Estos se normalizaron en tablas físicas garantizando integridad referencial.*