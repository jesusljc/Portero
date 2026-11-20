# Portero

Escáner asíncrono de puertos TCP y extractor de *banners* (*banner grabbing*) desarrollado en Python estándar (`asyncio` y `socket`) con parámetros de concurrencia y tiempos de espera configurables según la latencia de red.

## Características principales

- **Escaneo asíncrono de alta concurrencia:** Utiliza `asyncio` y `asyncio.Semaphore` para auditar múltiples puertos en paralelo sin bloquear el hilo de ejecución.
- **Identificación de servicios y *Banner Grabbing*:** Mapea los puertos más habituales y captura el mensaje de bienvenida de los servicios activos para facilitar el reconocimiento de versiones.
- **Perillas de calibración de rendimiento:** Permite ajustar desde el encabezado del script la cantidad de trabajadores simultáneos (`NUM_TRABAJADORES`) y los tiempos máximos de espera (`TIMEOUT_SCAN` y `TIMEOUT_BANNER`) para equilibrar velocidad y precisión según el *ping* y el ancho de banda.
- **Resolución DNS asíncrona y reportes:** Acepta tanto direcciones IP como nombres de dominio y exporta automáticamente los resultados con marca temporal a un archivo `.txt`.

## Calibración de parámetros (Perillas de optimización)

| Perfil de red | `NUM_TRABAJADORES` | `TIMEOUT_SCAN` | `TIMEOUT_BANNER` | Escenario recomendado |
| :--- | :---: | :---: | :---: | :--- |
| **Red local / Laboratorio** | `650 - 1000` | `0.2s - 0.3s` | `0.5s` | Máxima velocidad en redes LAN o máquinas virtuales con latencia mínima. |
| **Internet / Latencia media** | `250 - 500` | `0.5s - 1.0s` | `1.0s` | Balance entre rapidez y fiabilidad en conexiones externas. |
| **Enlace lento / Alta latencia** | `100 - 200` | `1.5s - 2.5s` | `1.5s` | Evita falsos negativos y saturación en redes con *ping* elevado. |

## Requisitos y ejecución

No requiere dependencias externas; funciona únicamente con la biblioteca estándar de **Python 3.10+**:

```bash
git clone [https://github.com/jesusljc/Portero.git](https://github.com/jesusljc/Portero.git)
cd Portero
python portero.py
Al iniciar, ingresá la dirección IP o dominio autorizado a auditar (por ejemplo, 127.0.0.1 o localhost).
```

Aviso de uso autorizado

Esta herramienta fue desarrollada con fines educativos y de auditoría defensiva. Debe utilizarse únicamente sobre redes, servidores o entornos de laboratorio propios o para los cuales se cuente con autorización explícita.
