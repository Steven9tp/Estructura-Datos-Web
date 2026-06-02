# Documentación del Proyecto: SmartCampus UTA Web

## 1. Introducción
En la formación de Ingeniería de Software, el estudio de estructuras de datos adquiere mayor valor cuando se aplica dentro de soluciones completas y no únicamente como ejercicios aislados de programación. Por ello, este proyecto integrador propone que los estudiantes diseñen y construyan un aplicativo web funcional, partiendo de requerimientos iniciales, diseño de base de datos, arquitectura de software por capas e integración de estructuras de datos lineales y no lineales.
La propuesta responde a la secuencia de contenidos de la asignatura, que aborda TDA, listas, pilas, colas, árboles, recursividad y grafos, y busca que cada equipo resuelva un problema realista de gestión universitaria con criterios técnicos, de calidad y de documentación profesional.

## 2. Justificación
El proyecto permite evaluar de forma articulada la capacidad del estudiante para analizar problemas, levantar requerimientos, modelar datos, diseñar arquitectura de software y seleccionar estructuras de datos apropiadas. Además, fortalece la visión de ingeniería al exigir que cada estructura implementada tenga un uso real dentro del sistema y no sea incorporada únicamente como demostración académica.
* Integra teoría y práctica en un solo producto de software.
* Promueve decisiones técnicas justificadas y documentadas.
* Refuerza competencias de desarrollo web, base de datos y modelado.
* Facilita una evaluación más completa del desempeño del estudiante.

## 3. Problema a resolver
En el contexto universitario, procesos como la atención estudiantil, el registro de trámites, la organización documental y la localización de espacios suelen estar distribuidos en diferentes medios, lo que genera retrasos, poca trazabilidad y dificultad para visualizar relaciones entre actores, dependencias y recursos. Se requiere un sistema web que centralice estos procesos y represente la información mediante estructuras de datos adecuadas, con persistencia en base de datos y una arquitectura clara.

## 4. Tema del proyecto
Desarrollar el sistema “SmartCampus UTA Web”, un aplicativo web orientado a la gestión de atención, trámites, organización documental y rutas internas del campus universitario, aplicando estructuras de datos avanzadas, base de datos relacional y arquitectura de software por capas.

## 5. Objetivo general
Desarrollar un aplicativo web integral para la gestión de atención, trámites, documentación y rutas internas de un campus universitario, aplicando estructuras de datos lineales y no lineales, diseño de base de datos a partir de requerimientos iniciales y una arquitectura de software por capas.

## 6. Objetivos específicos
* Levantar y documentar los requerimientos funcionales y no funcionales del sistema.
* Analizar el problema y modelar los procesos principales del aplicativo.
* Diseñar la base de datos desde los requerimientos iniciales, incluyendo modelo conceptual, lógico y físico.
* Implementar estructuras de datos propias y asociarlas a funcionalidades reales del sistema.
* Diseñar una arquitectura de software web organizada por capas.
* Desarrollar el aplicativo web con interfaz, lógica de negocio, persistencia y seguridad básica.
* Validar el funcionamiento del sistema mediante pruebas funcionales y técnicas.
* Documentar y defender las decisiones tomadas en el proyecto.

## 7. Alcance del proyecto
El sistema deberá incluir, como mínimo, autenticación de usuarios, administración de roles, registro de estudiantes o usuarios institucionales, gestión de turnos de atención, gestión de solicitudes o trámites, historial de acciones, organización jerárquica de documentos o dependencias, representación de un mapa del campus, búsqueda de rutas entre ubicaciones, almacenamiento persistente en base de datos e interfaz web funcional.

## 8. Requerimientos iniciales

### 8.1 Requerimientos funcionales
| Código | Descripción |
|---|---|
| RF1 | Registrar usuarios y gestionar autenticación. |
| RF2 | Administrar roles y permisos básicos. |
| RF3 | Registrar estudiantes, personal o usuarios institucionales. |
| **RF4** | **Registrar solicitudes o trámites.** |
| **RF5** | **Gestionar turnos de atención y atenderlos en orden de cola.** |
| RF6 | Consultar historial de trámites por usuario. |
| RF7 | Organizar documentos por categorías jerárquicas. |
| RF8 | Visualizar estructura de dependencias institucionales. |
| RF9 | Registrar puntos del campus y sus conexiones. |
| RF10 | Calcular rutas entre dos ubicaciones. |
| RF11 | Generar reportes básicos y bitácora de acciones. |

### 8.2 Requerimientos no funcionales
* El sistema debe implementarse como aplicativo web.
* Debe usar una base de datos relacional con integridad referencial.
* La solución debe organizarse con arquitectura por capas.
* Debe incluir validación de formularios y manejo básico de errores.
* La interfaz debe ser usable, consistente y claramente navegable.
* Debe existir documentación técnica y justificación del uso de estructuras de datos.

## 9. Diseño y construcción de la base de datos
La base de datos deberá construirse a partir de los requerimientos levantados por el equipo. No se aceptará un diseño creado únicamente al final del desarrollo; por tanto, cada grupo debe demostrar la trazabilidad entre requerimientos, entidades, relaciones y módulos del sistema.

### 9.1 Actividades mínimas
* Identificación de entidades, atributos y relaciones.
* Definición de cardinalidades y reglas de negocio.
* Elaboración del modelo conceptual, modelo lógico y modelo físico.
* Normalización y validación de integridad.
* Generación de script SQL y carga de datos de prueba.

### 9.2 Entidades sugeridas
* **Acceso:** Usuario, Rol
* **Personas:** Estudiante, Empleado
* **Procesos:** Trámite, Solicitud, Turno
* **Organización:** Dependencia, CategoríaDocumento, Documento
* **Rutas:** PuntoRuta, ConexiónRuta, Edificio
* **Trazabilidad:** HistorialAcción

## 10. Arquitectura de software propuesta
El sistema deberá implementarse con una arquitectura de software por capas...
* **Presentación:** Interacción con el usuario mediante navegador.
* **Aplicación:** Orquestación de casos de uso.
* **Dominio:** Reglas del negocio y estructuras de datos (ListaSimple, ListaDoble, ListaCircular, Pila, Cola, Árbol y Grafo).
* **Persistencia:** Acceso a datos y repositorios.
* **Datos:** Base de datos relacional y scripts.

## 11. Integración de estructuras de datos en el sistema
| Estructura | Aplicación sugerida | Justificación |
|---|---|---|
| **Lista secuencial** | Catálogos de tipos de trámite o edificios. | Acceso indexado y manejo compacto. |
| **Lista simplemente enlazada** | Historial dinámico de solicitudes. | Inserciones frecuentes y crecimiento flexible. |
| **Lista doblemente enlazada** | Navegación hacia adelante/atrás en expedientes. | Permite recorrido bidireccional. |
| **Lista circular** | Rotación de ventanillas o responsables. | Representa ciclos y asignación Round-Robin. |
| **Pila** | Deshacer acciones o historial LIFO. | Adecuada para reversión y seguimiento del último evento. |
| **Cola** | Fila de atención estudiantil. | Modela el orden FIFO de servicio. |
| **Árbol** | Clasificación jerárquica de documentos o dependencias. | Representa niveles y relaciones padre-hijo. |
| **Grafo** | Mapa del campus y búsqueda de rutas. | Permite modelar conexiones complejas entre nodos. |

## 12. Implementación del aplicativo web
La solución final deberá entregarse como un aplicativo web funcional...

## 13, 14, 15, 16. Metodología, Entregables, Restricciones y Rúbrica
(Detalles de evaluación, 19 puntos en total).

## 17. Preguntas sugeridas para la defensa
* ¿Por qué eligieron una cola para el módulo de atención y no otra estructura?
* ¿Qué ventaja ofrece la lista circular en la rotación de ventanillas o responsables?
* ¿Cómo justifican el uso de árbol en la clasificación documental o estructura organizacional?
* ¿Qué representación del grafo usaron y por qué resultó apropiada para el campus?
* ¿De qué manera la base de datos fue construida a partir de los requerimientos iniciales?
* ¿Qué responsabilidades asumió cada capa de la arquitectura propuesta?

## 18. Enunciado final para estudiantes
Desarrollar un aplicativo web denominado “SmartCampus UTA Web”, orientado a la gestión de atención, trámites, documentación y rutas internas de un campus universitario...
La solución deberá evidenciar el uso real de dichas estructuras dentro de módulos funcionales del sistema, incluyendo atención por turnos, historial de operaciones, organización jerárquica de documentos y búsqueda de rutas entre ubicaciones del campus.
