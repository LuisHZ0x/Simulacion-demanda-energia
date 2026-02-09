# Simulador de Demanda Energética Urbana

Este proyecto simula la demanda de energía eléctrica en una ciudad, modelando el consumo de diferentes tipos de edificios (residencial, comercial, industrial) y la capacidad de las subestaciones eléctricas.

## 🚀 Características Principales

*   **Simulación en Tiempo Real**: Visualización dinámica del consumo energético hora a hora.
*   **Interactividad**:
    *   **Configuración Inicial**: Define la cantidad de edificios al iniciar.
    *   **Información Detallada**: Hover sobre edificios para ver población y consumo instantáneo.
    *   **Control de Tiempo**: Velocidad ajustable (1x, 2x, 4x) y pausa.
*   **Gestión de Red**:
    *   Cambio manual entre subestaciones (Pequeña, Mediana, Grande).
    *   **Modo Tormenta**: Simula eventos climáticos extremos que afectan el consumo.
    *   **Optimizador**: Algoritmo para recomendar la mejor subestación basándose en costos y confiabilidad.

## 📋 Requisitos

El proyecto requiere **Python 3.8+** y las dependencias listadas en `requeriments.txt`. Las principales son:

*   `pygame`: Motor gráfico.
*   `simpy`: Motor de simulación de eventos discretos.
*   `pandas`, `numpy`, `matplotlib`: Análisis de datos (utilizados internamente).

## 🛠️ Instalación y Ejecución

1.  **Clonar o descargar el repositorio**.
2.  **Crear un entorno virtual (recomendado)**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # En Linux/Mac
    ```
3.  **Instalar dependencias**:
    ```bash
    pip install -r requeriments.txt
    ```
4.  **Ejecutar la simulación**:
    ```bash
    python interfaz_visual.py
    ```

## 🎮 Guía de Uso

1.  Al iniciar, ingresa el número deseado de edificios (entre 10 y 400) y presiona ENTER o "INICIAR".
2.  Observa la simulación. Los edificios se iluminan según su consumo.
3.  **Pasa el mouse** sobre cualquier edificio para ver sus detalles (Tipo, Población, Consumo).
4.  Usa el panel derecho para cambiar de subestación si la barra de carga llega al rojo (riesgo de apagón).
5.  Prueba el botón "MODO TORMENTA" para ver cómo resiste la red.
6.  Usa "CALCULAR ÓPTIMO" para recibir una recomendación inteligente sobre qué infraestructura usar.

## 📂 Estructura del Proyecto

*   `interfaz_visual.py`: Punto de entrada principal. Maneja la UI y el loop de Pygame.
*   `motor_logico.py`: Lógica de simulación, clases de Edificios y algoritmos de optimización.
*   `config.py`: Configuraciones globales, paleta de colores y parámetros.
