# Integración De Takeovflow Con Telegram

> Fork de [takeovflow](https://github.com/theoffsecgirl/takeovflow) con integración completa de Telegram: alertas automáticas en tiempo real cuando se detectan posibles subdomain takeovers.

![GitHub last commit](https://img.shields.io/github/last-commit/anaa-chun/takeovflow)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)

<br>

## Descripción

**IntegracionDeTakeovflowConTelegram** es un fork del escáner de subdomain takeover [takeovflow (theoffsecgirl)](https://github.com/theoffsecgirl/takeovflow).

El repositorio original proporciona el motor de escaneo: enumeración de subdominios, resolución DNS, fingerprinting de servicios mediante patrones CNAME, análisis con nuclei, y generación de reportes en Markdown y JSON.

Este fork añade una capa de integración con Telegram a través de un nuevo script (`wrapper.py`) que coordina el escaneo y envía los resultados directamente a un canal o chat de Telegram, sin necesidad de revisar los reportes manualmente.

**Dominio objetivo de prueba:** `*.luminorgroup.com`

<br>

## Modificaciones de fork

Todo el código nuevo se encuentra en `wrapper.py`. El script original `takeovflow.py` no ha sido modificado.

| Característica | Descripción |
|----------------|-------------|
| **Bot de Telegram** | Envío automático de alertas con formato HTML (negrita, cursiva, código inline) |
| **Filtrado por severidad** | Parámetro `--min-sev` para recibir solo hallazgos CRITICAL, HIGH, MEDIUM, LOW o INFO |
| **Adjuntar el reporte Markdown** | Flag `--send-report` para enviar el `.md` completo como fichero adjunto al mensaje |
| **Automatización con cron** | Configurado para ejecutarse diariamente a las 06:00 (`/var/log/takeovflow.log`) |
| **Logs persistentes** | Toda la salida se registra en `/var/log/takeovflow.log` |
| **Credenciales seguras** | El token y el chat ID se leen de variables de entorno, nunca hardcodeados |

<br>

### ¿Qué hace `wrapper.py` exactamente?

1. Lanza `takeovflow.py` con los flags `--json-output` y `--quiet` y recoge la ruta al JSON generado.
2. Parsea el JSON para extraer el resumen del dominio: subdominios descubiertos, resueltos, servicios HTTP y takeovers potenciales.
3. Filtra los hallazgos por el umbral de severidad indicado.
4. Construye un mensaje HTML estructurado y lo envía via la API de Telegram (`sendMessage`).
5. Si se usa `--send-report`, adjunta el reporte `.md` como documento (`sendDocument`).

<br>

## Capturas de pantalla


### Prueba real del wrapper con el dominio objetivo
![Prueba wrapper](images/Ejecutar%20una%20prueba%20real%20del%20wrapper%20con%20el%20dominio%20objectivo.png) <br>
Scan básico, alertas solo HIGHT y CRITICAL

### Prueba real con envío a Telegram
![Prueba Telegram](images/Ejecutar%20una%20prueba%20real%20del%20wrapper%20con%20el%20dominio%20objectivo%20Telegram.png) <br><br>


### Escaneo adjuntando reporte Markdown
![Reporte Markdown](images/Ejecutar%20el%20scan%20adjuntando%20tambi├®n%20el%20reporte%20Markdown.png) <br>
Lo mismo adjuntando el reporte Markdown en Telegram

### Escaneo adjuntando reporte Markdown + Telegram
![Reporte Telegram](images/Ejecutar%20el%20scan%20adjuntando%20tambi├®n%20el%20reporte%20Markdown%20Telegram.png)<br>
Reporte generado: [Reporte generado en formato md](/images/takeovflow_report_20260429_1053.md) <br><br>

### Automatización con cron (escaneo diario)
![Cron](images/Automatizar%20el%20escaneo%20con%20cron%20\(escaneo%20diario\).png)

<br>

## Instalación

```bash
git clone https://github.com/anaa-chun/takeovflow.git
cd takeovflow
pip3 install requests
chmod +x wrapper.py
```

> El script original `takeovflow.py` requiere herramientas externas (subfinder, assetfinder, dnsx, httpx, nuclei…). Se consulta el [README del repositorio original](https://github.com/theoffsecgirl/takeovflow) para instalarlas.

<br>

## Configuración

Las credenciales se pasan mediante variables de entorno. Puedes definirlas en un archivo `.env` o exportarlas directamente:

```bash
export TELEGRAM_TOKEN="tu_token_del_bot"
export TELEGRAM_CHAT_ID="tu_chat_id"

# Opcional: ruta alternativa a takeovflow.py
export TAKEOVFLOW_PATH="./takeovflow.py"

# Opcional: directorio de salida para los reportes
export TAKEOVFLOW_OUTPUT="/tmp/takeovflow_reports"
```

<br>

## Uso

### Escaneo básico (solo alertas HIGH y CRITICAL)

```bash
python3 wrapper.py -d luminorgroup.com
```

### Cambiar el umbral de severidad

```bash
python3 wrapper.py -d luminorgroup.com --min-sev MEDIUM
```

### Adjuntar también el reporte Markdown

```bash
python3 wrapper.py -d luminorgroup.com --send-report
```

<br>

### Referencia completa de parámetros

| Parámetro | Descripción | Por defecto |
|-----------|-------------|-------------|
| `-d / --domain` | Dominio objetivo (**obligatorio**) | — |
| `--min-sev` | Severidad mínima a reportar (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`) | `HIGH` |
| `--send-report` | Adjuntar el `.md` como fichero en Telegram | desactivado |


<br>

## Automatización con cron

Para ejecutar el escaneo todos los días a las 06:00 y guardar los logs:

```bash
crontab -e
```

Añadir la siguiente línea:

```cron
0 6 * * * TELEGRAM_TOKEN="..." TELEGRAM_CHAT_ID="..." python3 /ruta/wrapper.py -d luminorgroup.com --send-report >> /var/log/takeovflow.log 2>&1
```

Comprobar que se ha añadido:

```bash
crontab -l
```

<br>

## Estructura del proyecto

```
takeovflow/
├── takeovflow.py        # Motor de escaneo original (sin modificar)
├── wrapper.py           # ← NUEVO: integración con Telegram
├── .env                 # Variables de entorno (no subir a git)
├── images/              # Capturas de pantalla
├── README.md            # Este archivo (español)
├── README.es.md         # README adicional en español
├── CHANGELOG.md         # Historial de cambios del proyecto original
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

<br>

## Seguridad

- Nunca incluyas el token de Telegram ni el chat ID directamente en el código.
- El archivo `.env` está en `.gitignore` para evitar que se suba accidentalmente.
- Si el bot o el chat ID están mal configurados, el wrapper lo informa por stderr sin abortar.


<br>

## Créditos

- Proyecto original: [takeovflow by theoffsecgirl](https://github.com/theoffsecgirl/takeovflow)
- Este fork añade exclusivamente la integración con Telegram (`wrapper.py`).
