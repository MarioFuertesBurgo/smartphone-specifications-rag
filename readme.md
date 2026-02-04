# Memoria del proyecto: Smartphone Specifications RAG

Este documento es la memoria técnica y la guía de ejecución del proyecto. Su finalidad es permitir al profesor evaluar tanto la solución técnica como su encaje empresarial, y a la vez poder ejecutarla de principio a fin en un equipo local. 

## 1. Descripción del problema y estado del arte

El mercado de **smartphones** es extremadamente amplio y evoluciona con rapidez. Para un usuario o una empresa, comparar modelos implica leer muchas fichas técnicas con formatos distintos, lo que genera decisiones lentas, inconsistentes o poco informadas. Este problema es especialmente relevante en entornos corporativos: un departamento de compras necesita justificar decisiones, homogeneizar dispositivos y reducir costes, pero a menudo carece de un mecanismo ágil para filtrar y comparar opciones con criterios objetivos.

Los grandes modelos de lenguaje (LLM) ofrecen conversación natural, pero pueden inventar datos si no se apoyan en fuentes. Por eso, el enfoque moderno para tareas con datos concretos es **RAG (Retrieval-Augmented Generation)**, donde el LLM responde basándose en documentos recuperados. En paralelo, las **bases de datos grafo** (Neo4j) son idóneas para modelar entidades y relaciones, mientras que los **índices vectoriales** habilitan búsqueda semántica sobre texto. Este proyecto combina estas tres capas: grafo para estructura, vector para semántica y LLM para lenguaje natural.

La aportación clave es que todo el sistema se ejecuta localmente. Esto tiene valor empresarial porque elimina dependencia de servicios cloud, reduce riesgo de fuga de datos y facilita auditorías internas. El objetivo no es solo recomendar un móvil, sino demostrar un flujo reproducible y escalable de toma de decisiones basadas en datos mediante LLMs.

## 2. Problema explícito y aportación

**Problema explícito**: construir una aplicación local que recomiende **smartphones** de forma consistente, con datos verificables, que responda en lenguaje natural y que se limite al dominio de los móviles. La aplicación debe ser reproducible por un evaluador en un entorno estándar de Windows.

**Aportación**: un pipeline completo de ingesta, normalización, indexado y consulta; una **conversión automática** de precios a euros durante la carga; una **interfaz web** de estilo chatbot; y un mecanismo de control del comportamiento del modelo mediante **prompt**. A nivel empresarial, la aplicación reduce tiempos de análisis, estandariza criterios de compra y permite justificar recomendaciones con datos observables.

## 3. Proceso de desarrollo y toma de decisiones

El desarrollo se organizó por fases para reducir riesgo y asegurar verificabilidad. La primera fase consistió en validar dependencias locales: se creó un script de chequeo para confirmar conectividad con Neo4j y Ollama. La segunda fase abordó la ingesta: se definió un modelo de grafo estable y se agregó la conversión de precios **INR a EUR** para evitar incoherencias de moneda en la salida.

En la tercera fase se diseñó el texto normalizado (**key=value**) para cada teléfono. Este formato se eligió porque incrementa la calidad de recuperación semántica y reduce ambigüedades en el embedding. Una vez construido el índice vectorial, se realizaron pruebas de consulta y se detectó un sesgo: el sistema repetía siempre los mismos modelos. El diagnóstico reveló que el retriever estaba limitado a **top_k=2**. La solución fue aumentar top_k y aplicar **MMR (Maximum Marginal Relevance)** para diversificar resultados sin perder relevancia.

Otro problema observado fue el cumplimiento inconsistente de instrucciones en modelos pequeños (1B). Se concluyó que el control de comportamiento vía prompt exige un modelo con capacidad suficiente (7B o superior). Por ello, se recomienda **qwen2.5:7b** o **llama3.1:8b** para un equilibrio entre calidad y coste computacional.

Finalmente, se decidió crear una interfaz web para usuarios no técnicos. Para garantizar reproducibilidad, el servidor ejecuta automáticamente toda la canalización (scripts 00 a 03) en el arranque. Este enfoque reduce errores en evaluación porque evita que el profesor tenga que recordar el orden de pasos.

## 4. Solución propuesta (visión técnica)

La solución combina una capa de datos y una capa conversacional. El CSV se carga en Neo4j creando nodos **Phone** y categorías (**OS**, **Chipset**, **Network**, **DisplayType**, **MemoryCardType**). Paralelamente se genera un texto por modelo con campos normalizados y se construye un índice vectorial persistente. El LLM consulta este índice y genera una recomendación en lenguaje natural.

En consulta, se utiliza un retriever con diversificación **MMR** (top_k=10, alpha=0.7). Esto evita que una sola marca domine las respuestas. El modelo se controla mediante prompt: idioma, tono y formato de salida. El servidor web expone un endpoint JSON y presenta una interfaz de chat con historial visible y cuadro de entrada inferior.

## 5. Guía de ejecución detallada (requisitos y pasos)

### 5.1 Requisitos de software

El proyecto requiere **Windows 10/11**, **Python 3.10+**, **Neo4j 5.x** y **Ollama** instalado localmente. No se requiere acceso a servicios cloud.

### 5.2 Requisitos de hardware (estimaciones)

Para una experiencia fluida con modelos de 7B, se recomiendan **16 GB de RAM**. Con 8 GB puede llegar a funcionar, pero con mayor latencia y riesgo de errores de memoria. El uso de GPU no es obligatorio y la ejecución en CPU es viable, aunque más lenta. Estas cifras son estimaciones orientativas y dependen del modelo seleccionado y de la carga del sistema.

### 5.3 Puertos y servicios

Neo4j utiliza Bolt en `bolt://localhost:7687`. Ollama expone su API en `http://localhost:11434`. La aplicación web se expone en el puerto definido por `WEB_APP_PORT` (por defecto 8000).

### 5.4 Instalación

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5.5 Configuración

El archivo `.env` **se entrega con el proyecto** para la evaluación. No es necesario modificarlo.

### 5.6 Ejecución web (recomendada)

```powershell
python web-app\server.py
```

Al iniciar, el servidor ejecuta automáticamente:
1) `scripts/00_check_env.py`
2) `scripts/01_setup_models.py`
3) `scripts/02_load_neo4j.py`
4) `scripts/03_build_rag.py`

Después levanta la web en `http://localhost:<WEB_APP_PORT>`.

### 5.7 Ejecución CLI (alternativa)

```powershell
python scripts\04_chat.py
```

### 5.8 Datos y volumen

El CSV contiene 968 filas. Tras limpieza y deduplicación por modelo, el índice vectorial contiene **777 documentos únicos**. Estas cifras permiten una respuesta razonablemente rápida sin sacrificar cobertura de catálogo.

## 6. Casos de uso (escenarios)

Escenario pesimista: el usuario aporta información vaga (por ejemplo, "quiero un móvil barato"). El sistema responde con un modelo equilibrado según el dataset, evitando inventar datos. La personalización es limitada, pero la respuesta es útil y consistente.

Escenario optimista: el usuario define criterios claros (batería, 5G, presupuesto). El sistema recupera modelos relevantes y ofrece una recomendación concreta con especificaciones coherentes.

Escenario inverosímil: el usuario formula una petición fuera del dominio (política, medicina). El sistema rechaza la consulta y mantiene el ámbito de **smartphones**, evitando desviaciones.

## 7. Aplicación y valor empresarial

Desde la perspectiva empresarial, el sistema reduce el coste de comparación técnica y estandariza decisiones. En compras corporativas, esto significa que un responsable puede definir requisitos mínimos (RAM, batería, precio) y obtener recomendaciones consistentes para toda la flota. En ventas, permite responder rápidamente a consultas del cliente sin revisar catálogos manuales. En soporte, ayuda a justificar por qué un modelo es más adecuado que otro, lo cual refuerza transparencia y confianza.

La solución aporta trazabilidad: las respuestas se basan en un dataset interno, lo que facilita auditoróa. Además, al ejecutarse localmente, se reduce el riesgo de fuga de datos sensibles y se mantiene el control de costes.

## 8. Análisis de resultados y DAFO

El sistema cumple su objetivo principal: responder de forma consistente y basada en datos. La diversificación del retriever reduce la repetición de marcas y mejora la calidad percibida. La calidad final depende del modelo; con 7B se logra un equilibrio adecuado entre obediencia al prompt y consumo de recursos.

### DAFO:

- **Fortalezas:** ejecución local, reproducibilidad, integración grafo+vector, control de dominio. 

- **Debilidades:** dependencia de hardware local y sensibilidad al modelo. 

- **Oportunidades:** integración de precios actualizados y ampliación a otros dispositivos. 

- **Amenazas:** obsolescencia del dataset y cambios en la disponibilidad de modelos locales.

## 9. Aprendizajes

El desarrollo de este proyecto dejó un conjunto de aprendizajes prácticos que van más allá de la parte técnica y que son relevantes tanto para ingeniería como para negocio. En primer lugar, se comprobó que el **retriever es tan importante como el modelo generativo**. En la práctica, un LLM potente no compensa un retrieval pobre; si los documentos recuperados no representan bien el espacio de búsqueda, las recomendaciones se vuelven repetitivas o sesgadas, incluso con un prompt correcto. Esta experiencia refuerza la idea de que, en sistemas RAG, el rendimiento real depende de la calidad del índice, el top_k y la diversificación (MMR), no solo del modelo.

En segundo lugar, se confirmó que la **normalización de datos es crítica**. Transformar las filas del CSV en un texto estable con claves (key=value) mejora la coherencia semántica de los embeddings y reduce ambigüedades. En la práctica, la normalización actúa como un “contrato” entre datos y lenguaje natural: cuanto más consistente es el formato, más fiable resulta la recuperación y, por extensión, la respuesta.

Un tercer aprendizaje es que el **control del comportamiento vía prompt tiene límites reales**. Modelos pequeños tienden a ignorar restricciones complejas o a introducir saludos innecesarios, incluso cuando las reglas son explícitas. Esto evidencia que la gobernanza de un asistente no depende solo del texto del prompt, sino de la capacidad del modelo y del contexto recuperado. En términos de gestión de riesgos, el prompt no es un mecanismo de seguridad fuerte: es un mecanismo de alineamiento débil que exige validaciones externas si el uso es crítico.

También se aprendió la importancia de la **reproducibilidad operativa**. Automatizar el pipeline en el arranque del servidor evita errores humanos y asegura que todas las evaluaciones se hacen sobre el mismo estado. Esto resulta clave en un entorno académico y también en entornos empresariales donde la trazabilidad y la consistencia son requisitos. A nivel de negocio, la reproducibilidad reduce costes de soporte y evita decisiones basadas en estados inconsistentes.

Otro aprendizaje relevante es la **gestión de recursos**. En un entorno local, el consumo de memoria del LLM condiciona la experiencia de usuario y el tamaño del modelo viable. Esto obliga a equilibrar calidad y coste computacional, una decisión que en negocio se traduce en una pregunta directa: “¿cuánto valor incremental aporta un modelo más grande frente a su coste operativo?”. En este proyecto se validó que un modelo de 7B ofrece un punto de equilibrio razonable para equipos estándar.

Por último, se observó que la **capacidad de explicación** es clave para la adopción. Aunque el sistema puede recomendar un modelo, la aceptación mejora cuando el usuario entiende de qué datos se parte y por qué se llega a esa conclusión. Esto sugiere que una futura evolución debería incorporar explicabilidad explícita (por ejemplo, resaltando las tres especificaciones decisivas). En términos de aprendizaje, el valor del sistema no está solo en recomendar, sino en **justificar decisiones** de forma clara y auditable.

## 10. Líneas de futuro

Se propone incorporar actualización automática de catálogos, métricas de evaluación (recall@k, MRR), explicabilidad (por qué se recomienda un modelo) y una API pública para integraciones empresariales.

## 11. Demostración en vídeo (YouTube)

Esta sección se reserva para un vídeo breve donde se muestra la ejecución completa del proyecto: arranque del servidor, carga automática del pipeline, uso de la interfaz web y ejemplos de consultas. El objetivo es que el evaluador pueda ver el funcionamiento real en menos de 3–5 minutos.

**Nota sobre GitHub:** GitHub no permite incrustar vídeos reproducibles (no admite iframes). La forma habitual es insertar una miniatura que enlace al vídeo. 

[![Demostración del proyecto](https://img.youtube.com/vi/rNgLt6dE3PI/0.jpg)](https://www.youtube.com/watch?v=rNgLt6dE3PI)

## 12. Ciberseguridad

El sistema es local y no transmite datos a terceros. Las credenciales se almacenan en `.env`, por lo que no deben subirse a repositorios públicos (en este caso se hace, debido a que no contienen información de servicios que esten corriendo en la nube y es imposible acceder a ellos aunque tengas las claves). Neo4j debe protegerse con contraseña fuerte y no exponer el puerto Bolt a redes abiertas. Ollama debe mantenerse actualizado y su API no debe abrirse sin control. Aunque el prompt limita el dominio, el riesgo de **prompt injection** no se elimina por completo; en producción se recomendaría control de accesos, auditoría y hardening de servicios.

## 13. Anexo técnico

Estructura del proyecto:

```
app/
  config.py
  neo4j_utils.py
  rag_utils.py

scripts/
  00_check_env.py
  01_setup_models.py
  02_load_neo4j.py
  03_build_rag.py
  04_chat.py
  diagnostics/
    check_docstore.py
    query_index.py

web-app/
  server.py
  templates/
    index.html
  static/
    app.js
    styles.css

data/
  smartphone-specification.csv

index_store/
  *.json
```

Comandos clave:

```powershell
# pipeline manual
python scripts\00_check_env.py
python scripts\01_setup_models.py
python scripts\02_load_neo4j.py
python scripts\03_build_rag.py

# CLI
python scripts\04_chat.py

# Web App
python web-app\server.py
```

---
