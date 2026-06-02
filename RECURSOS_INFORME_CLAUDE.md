# ESPECIFICACIONES TÉCNICAS COMPLETAS PARA GENERAR EL INFORME ACADÉMICO (PROMPT CLAUDE)
Este documento resume de manera exacta, estructurada y sin rodeos toda la arquitectura, código, base de datos y lógica del proyecto **SmartCampus UTA Web**. Es ideal para que un LLM (como Claude o ChatGPT) redacte el informe formal de la universidad.

---

## 1. FICHA TÉCNICA Y TECNOLOGÍAS
*   **Tema:** Plataforma web "SmartCampus UTA Web" para la gestión de turnos, trámites, organigrama y rutas del campus.
*   **Lenguaje:** Python 3.10
*   **Framework Web:** Flask (Arquitectura por capas con Blueprints).
*   **Persistencia:** ORM SQLAlchemy sobre MySQL (servidor administrado en la nube en **Aiven** con soporte SSL).
*   **Frontend:** HTML5, CSS3 plano personalizado (Paleta institucional: dorado de la UTA y carbón/oscuro), Javascript plano y Jinja2.
*   **Despliegue PaaS:** Render (Plan gratuito).
*   **Puente de Correo:** API REST en Google Apps Script (bypassea el bloqueo de puertos de Render enviando correos vía HTTPS POST en el puerto 443).

---

## 2. ESTRUCTURA COMPLETA DEL REPOSITORIO (MAPEO DE ARCHIVOS)
```
Estructura-Datos-Web/
├── app/
│   ├── __init__.py            # Configuración de la app, Flask-Login, SQLAlchemy y conexión SSL con Aiven.
│   ├── models.py              # Definición de tablas de la base de datos (Usuario, Turno, Tramite, etc.).
│   ├── forms.py               # Formularios WTForms (Registro, Login, Edición Perfil).
│   ├── init_db.py             # Script de carga inicial de datos de prueba (Rutas, Dependencias, Categorías).
│   ├── estructuras/
│   │   ├── __init__.py
│   │   └── basicas.py         # CÓDIGO FUENTE DE LOS TDA PROPIOS (Listas, Pilas, Colas, Árboles, Grafos).
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py          # Rutas de login, registro con envío de correo de activación y recuperación.
│   ├── atencion/
│   │   ├── __init__.py
│   │   └── routes.py          # Gestión de colas de turnos, llamado de turnos y ruta de simulación.
│   ├── tramites/
│   │   ├── __init__.py
│   │   └── routes.py          # Registro de solicitudes, historial y bitácora de auditoría (Pila).
│   ├── organizacion/
│   │   ├── __init__.py
│   │   └── routes.py          # Carga del organigrama (Árbol) y clasificación de documentos.
│   └── campus/
│       ├── __init__.py
│       └── routes.py          # Carga de nodos/aristas (Grafo) y cálculo de Dijkstra.
├── frontend/
│   ├── templates/
│   │   ├── base.html          # Layout general con barra lateral, modo oscuro y notificaciones.
│   │   ├── index.html         # Dashboard principal con estadísticas rápidas.
│   │   ├── perfil.html        # Datos del perfil del usuario logueado.
│   │   ├── atencion/          # Pantalla de turnos y solicitud de tickets.
│   │   ├── tramites/          # Formularios de trámites e historial.
│   │   ├── organizacion/      # Visualización de dependencias y documentos.
│   │   ├── campus/            # Mapa interactivo de rutas de grafos.
│   │   └── admin/
│   │       └── admin_panel.html # Panel de control de roles y estados de usuario (Administrador).
│   └── static/
│       ├── css/
│       │   └── style.css      # Sistema de diseño de variables CSS (dorado/carbón).
│       └── audio/
│           └── chime.mp3      # Sonido para notificaciones de llamadas de turnos.
├── .env                       # Variables de entorno (Secret Key, DB URL, GAS URL).
├── run.py                     # Archivo de arranque del servidor.
└── requirements.txt           # Librerías necesarias (Flask, Flask-Login, Flask-WTF, SQLAlchemy, PyMySQL).
```

---

## 3. DICCIONARIO DE DATOS (BASE DE DATOS RELACIONAL)

### Tabla: `usuarios`
Representa a estudiantes y personal de la UTA.
*   `id` (INT, PK, Auto): ID interno.
*   `email` (VARCHAR(120), Unique): Correo institucional.
*   `password_hash` (VARCHAR(256)): Contraseña cifrada con Werkzeug.
*   `nombres` y `apellidos` (VARCHAR(100)): Datos personales.
*   `cedula` (VARCHAR(20), Unique): Identificación ecuatoriana.
*   `tipo_usuario` (ENUM: 'estudiante', 'empleado', 'admin'): Clasificación.
*   `activo` (BOOLEAN): Control de acceso administrativo.
*   `email_verificado` (BOOLEAN): Verificación de activación.

### Tabla: `turnos`
Almacena los turnos de atención de secretaría/ventanilla.
*   `id` (INT, PK, Auto)
*   `usuario_id` (INT, FK -> `usuarios.id`)
*   `dependencia_id` (INT, FK -> `dependencias.id`)
*   `codigo_turno` (VARCHAR(20)): Código secuencial (ej: SEC-001).
*   `estado` (ENUM: 'en_espera', 'atendido', 'cancelado')
*   `fecha_emision` y `fecha_atencion` (DATETIME)

### Tabla: `tramites`
Solicitudes enviadas por los estudiantes.
*   `id` (INT, PK, Auto)
*   `usuario_id` (INT, FK -> `usuarios.id`)
*   `tipo_tramite` (VARCHAR(100)): Nombre de la solicitud.
*   `estado` (ENUM: 'iniciado', 'en_revision', 'aprobado', 'rechazado')
*   `fecha_inicio` y `fecha_actualizacion` (DATETIME)
*   `observaciones` (TEXT): Notas del empleado que atiende.

### Tabla: `dependencias`
Organización de oficinas. Soporta estructura jerárquica recursiva.
*   `id` (INT, PK, Auto)
*   `nombre` (VARCHAR(150))
*   `dependencia_padre_id` (INT, FK -> `dependencias.id`, Nullable): Apunta a la oficina superior.

---

## 4. DETALLES DE IMPLEMENTACIÓN DE LOS TDA PROPIOS (`basicas.py`)

A continuación se describe la estructura exacta de los algoritmos implementados a mano:

1.  **`ListaSimple` / `ListaDoble`:** Estructuras enlazadas dinámicas que manipulan punteros de memoria a objetos `Nodo`. La `ListaDoble` cuenta con `anterior` y `siguiente` en sus nodos para permitir operaciones en ambos extremos con complejidad $O(1)$.
2.  **`ListaCircular`:** Similar a la doblemente enlazada, pero su último nodo tiene como puntero `siguiente` al primero (cabeza), facilitando iteraciones cíclicas infinitas.
3.  **`Pila`:** Estructura LIFO (*Last-In, First-Out*) que encapsula una lista. Ofrece operaciones `apilar(dato)` y `desapilar()` en $O(1)$ para guardar el histórico de eventos del sistema.
4.  **`Cola`:** Estructura FIFO (*First-In, First-Out*). Utiliza inserciones al final y extracciones al frente en $O(1)$ para la fila virtual de turnos.
5.  **`ArbolNArio`:** Estructura no lineal donde cada `NodoArbol` contiene el valor de la dependencia y una lista dinámica de hijos. El recorrido y búsqueda se realizan recursivamente.
6.  **`Grafo`:** Implementa un grafo mediante un diccionario de listas de adyacencia: `self.adyacencias = { nodo_id: { vecino_id: peso } }`. Implementa el algoritmo de **Dijkstra** utilizando una cola de prioridad (`heapq`) para hallar de forma óptima el camino de costo mínimo.

---

## 5. MAPEO DE CASOS DE USO REALES CON LOS TDAs

| Caso de Uso en la Web | TDA Utilizado | ¿Cómo opera en la lógica? | Ubicación del Código |
| :--- | :--- | :--- | :--- |
| **Fila virtual de Ventanilla** | `Cola` (FIFO) | Al iniciar el día, el servidor consulta los turnos de la base de datos con estado `'en_espera'`, inicializa un objeto `Cola` en memoria y los inserta. Al atender, llama a `.desencolar()` para procesar el primero. | Lógica: `app/atencion/routes.py`<br>TDA: `app/estructuras/basicas.py` |
| **Rotación de Ventanillas** | `ListaCircular` | Permite asignar turnos en esquema Round-Robin rotando secuencialmente entre las ventanillas activas de forma automática. | Lógica: `app/atencion/routes.py` |
| **Bitácora y Historial LIFO** | `Pila` (LIFO) | Cada acción del usuario (crear trámite, cambiar estado) se apila. Esto permite revisar el historial en orden inverso y habilitar el botón "Deshacer". | Lógica: `app/tramites/routes.py` |
| **Directorio Organizacional** | `ArbolNArio` | Al cargar la página, se lee la tabla `dependencias`. Se construye recursivamente la jerarquía y se evalúa el número máximo de niveles (altura del árbol). | Lógica: `app/organizacion/routes.py` |
| **Cálculo de Rutas del Campus** | `Grafo` + **Dijkstra** | Los puntos físicos son nodos y los caminos son aristas. Al pulsar "Calcular", se ejecuta el Dijkstra del grafo devolviendo el arreglo de nombres de la ruta más corta. | Lógica: `app/campus/routes.py` |

---

## 6. ÚLTIMOS CAMBIOS IMPLEMENTADOS (CARACTERÍSTICAS CLAVE PARA EXPLICAR)

### A. Simulador de Avance de Turno
*   **Problema:** En un entorno local o de pruebas para la defensa, es difícil loguearse en múltiples navegadores para avanzar la cola mientras se muestra la pantalla de televisión.
*   **Solución:** Se creó un **Bypass de Permisos** y se agregó un panel de simulación en la pantalla de turnos (`pantalla.html`). Cualquier usuario puede presionar el botón "Simular Avance" para invocar `/atender`. El sistema avanza el turno, reproduce un **chime sonoro (`chime.mp3`)** y despliega una **alerta dorada visual (`¡ES TU TURNO!`)** si el ID de usuario activo coincide con el del turno llamado. La pantalla se auto-refresca cada **5 segundos**.

### B. Panel de Control de Administración (RF2, RF3, RF11)
*   **Problema:** La guía exige que el administrador pueda registrar usuarios, gestionar roles y consultar reportes.
*   **Solución:** Se creó el template `admin_panel.html` y la ruta `/admin_panel`. Cuenta con:
    1.  **Estadísticas de Reporte (RF11):** Tarjetas dinámicas que resumen el total de usuarios, estudiantes, empleados, administradores, turnos en cola y turnos atendidos.
    2.  **Gestión de Cuentas (RF3):** Tabla de usuarios con buscador rápido interactivo en JavaScript que filtra filas en el cliente.
    3.  **Gestión de Roles (RF2):** Selector dinámico para cambiar el rol de un usuario en caliente (`estudiante`, `empleado`, `admin`) y botón de activación/bloqueo de cuentas.

### C. Rediseño del Grafo de Rutas (Huachi)
*   **Problema:** La visualización del grafo sobre el mapa satelital era confusa, saturada visualmente y tapaba los nombres. Además, los edificios ubicados en el extremo sur (FEUE, Servicio Médico) quedaban recortados porque la altura de pantalla estaba bloqueada en 500px y la caja de vista del SVG era `0 0 800 800`.
*   **Solución:**
    1.  **Fondo de Consola Tecnológica:** Se eliminó la imagen de mapa de bits y se sustituyó por un fondo oscuro de grilla digital (#0f172a) con gradientes dorados radiales.
    2.  **Ampliación:** El contenedor creció a **`750px`** de alto, aprovechando todo el ancho de la tarjeta.
    3.  **ViewBox Óptimo:** Se cambió la cámara a `viewBox="150 100 600 780"`. Esto encuadra con precisión todos los nodos del campus Huachi, haciéndolos más grandes y eliminando el recorte de las dependencias del sur.
