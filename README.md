# Fastapi-MCPServe

**Fastapi-MCPServe** es un microservicio basado en FastAPI que implementa el protocolo **MCP (Model Context Protocol)**. Su objetivo es brindar herramientas y capacidades extendidas a modelos de inteligencia artificial, actuando como una capa de servicios para tareas complejas.

Actualmente, este servicio se integra con **Gemini IA**, habilitándole funciones avanzadas como:

- Acceso a bases de datos
- Generación de reportes en PDF
- Procesamiento de datos estructurados
- Entre otros servicios complementarios

## ¿Qué es MCP?

**Model Context Protocol (MCP)** es un enfoque de diseño para ampliar las capacidades de los modelos de IA, permitiéndoles interactuar con herramientas externas de manera segura y controlada. Este microservicio sigue dicho protocolo para exponer funcionalidades específicas mediante endpoints que la IA puede invocar.

## Características principales

- 🧠 Integración con **Gemini IA** como cliente principal
- 🗄️ Conectividad con bases de datos
- 🧾 Generación de reportes automáticos en PDF
- 🛡️ Diseño modular y seguro para facilitar extensibilidad

## Uso previsto

Este servicio está diseñado para ser consumido por modelos de lenguaje o agentes de IA que requieran realizar operaciones fuera de su contexto puramente textual, permitiendo ejecutar acciones del mundo real como consultas, generación de documentos o extracción de información.

## Instalación (básica)

```bash
git clone https://github.com/Alernal/Fastapi-MCPServe.git
cd Fastapi-MCPServe
pip install -r requirements.txt
uvicorn main:app --reload
