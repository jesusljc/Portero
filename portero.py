import asyncio
import socket
import sys
import time
from datetime import datetime
from typing import Optional

# =====================================================================
# PERILLAS DE OPTIMIZACIÓN (Configuración de velocidad y precisión)
# =====================================================================
# ¿Qué son y para qué sirven?
# Estas variables son como las perillas de un tablero de control:
# te permiten ajustar qué tan rápido o cuidadoso será el escaneo sin
# tener que modificar el resto del código.
#
# - NUM_TRABAJADORES: Indica cuántos puertos se revisan al mismo tiempo
#   (en paralelo). Un número más alto hace el escaneo más rápido, pero
#   si es demasiado alto puede saturar tu conexión o el sistema.
# - TIMEOUT_SCAN: Es el tiempo máximo (en segundos) que el programa
#   espera la respuesta de cada puerto antes de pasar al siguiente.
#   Un valor bajo acelera el escaneo; un valor más alto ayuda si la
#   red es lenta, para no omitir puertos abiertos por falta de tiempo.
# - TIMEOUT_BANNER: Tiempo máximo (en segundos) para intentar leer el
#   mensaje de bienvenida (banner) una vez que el puerto abrió.
NUM_TRABAJADORES = 650
TIMEOUT_SCAN = 0.3
TIMEOUT_BANNER = 0.5
RANGO_PUERTOS = range(1, 1025)

# --- Traductor de puertos comunes ---
# Asocia los números de puerto más conocidos con el nombre del servicio
# que suelen ejecutar, para mostrar resultados más fáciles de entender.
SERVICIOS_COMUNES = {
    21: "FTP (Transferencia de archivos)",
    22: "SSH (Acceso remoto seguro)",
    23: "Telnet (Acceso remoto no seguro)",
    25: "SMTP (Envío de Emails)",
    53: "DNS (Traductor de dominios)",
    80: "HTTP (Web no segura)",
    110: "POP3 (Recepción de Emails)",
    111: "RPC (Llamada a procedimiento remoto)",
    143: "IMAP (Recepción de Emails)",
    443: "HTTPS (Web Segura)",
    445: "SMB (Compartir archivos Windows)",
    500: "ISAKMP (Gestión de claves VPN)",
    3306: "MySQL (Base de datos)",
    3389: "RDP (Escritorio Remoto Windows)",
    5432: "PostgreSQL (Base de datos)",
    5900: "VNC (Control remoto gráfico)",
    8080: "HTTP Alternativo / Proxy",
}


# --- Función de escaneo asíncrono ---
async def scan_port(
    target_ip: str,
    puerto: int,
    sem: asyncio.Semaphore,
    timeout: float,
) -> Optional[str]:
    """Intenta conectar a un puerto y lee su banner si está abierto.

    Usa un semáforo para limitar cuántas conexiones simultáneas se
    realizan al mismo tiempo. Devuelve el texto formateado si el puerto
    está abierto (o si hubo un error inesperado), o None si está cerrado
    o no respondió a tiempo.
    """
    # El semáforo asegura que no superemos NUM_TRABAJADORES a la vez.
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target_ip, puerto),
                timeout=timeout,
            )

            # Si el puerto abrió, intentamos leer un "banner" (mensaje
            # de bienvenida que algunos servicios envían al conectar).
            banner = ""
            try:
                banner_data = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=TIMEOUT_BANNER,
                )
                banner = banner_data.decode("utf-8", errors="ignore").strip()
            except Exception:
                banner = "Sin Banner"
            finally:
                writer.close()
                await writer.wait_closed()

            servicio = SERVICIOS_COMUNES.get(puerto, "Desconocido")
            resultado = f"  [!] PUERTO {puerto} ({servicio}) ... ABIERTO"
            if banner:
                resultado += f"\n      - Banner: {banner}"

            return resultado

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # Puerto cerrado, filtrado o sin respuesta a tiempo.
            return None
        except Exception as exc:
            return f"  [!] PUERTO {puerto} ... ERROR: {exc}"


# --- Función principal ---
async def main() -> None:
    """Coordina la resolución del objetivo, el escaneo y el reporte."""
    target_ip_str = input("Introduce la IP o dominio a escanear: ")

    # Convertimos el dominio (si se ingresó uno) a su dirección IP real.
    try:
        loop = asyncio.get_running_loop()
        addr_info = await loop.getaddrinfo(target_ip_str, None)
        target_ip = addr_info[0][4][0]
    except socket.gaierror:
        print("Error: No se pudo resolver el nombre de dominio. Saliendo.")
        sys.exit()

    separador = "=" * 40
    total_puertos = len(RANGO_PUERTOS)

    print(f"\n{separador}")
    print(f"Iniciando escaneo ASYNC en {target_ip_str} ({target_ip})")
    print(f"Escaneando los {total_puertos} puertos más comunes...")
    print(
        f"Con {NUM_TRABAJADORES} 'permisos' concurrentes "
        f"y timeout de {TIMEOUT_SCAN}s"
    )
    print(separador)

    # Medimos el tiempo total que tarda todo el escaneo.
    tiempo_inicio = time.perf_counter()

    sem = asyncio.Semaphore(NUM_TRABAJADORES)
    tareas = [
        scan_port(target_ip, puerto, sem, TIMEOUT_SCAN)
        for puerto in RANGO_PUERTOS
    ]
    resultados = await asyncio.gather(*tareas)

    tiempo_total = time.perf_counter() - tiempo_inicio

    # asyncio.gather respeta el orden de RANGO_PUERTOS (1 a 1024),
    # así que solo filtramos los puertos que respondieron.
    resultados_abiertos = [res for res in resultados if res is not None]

    # Construimos el informe en una lista de líneas para unirlo al final
    # de una sola vez (más eficiente que concatenar strings con +=).
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lineas_reporte = [
        separador,
        f"Informe de Escaneo ASYNC para {target_ip_str} ({target_ip})",
        f"Fecha: {fecha_actual}",
        (
            f"Escaneo de {total_puertos} puertos completado "
            f"en {tiempo_total:.2f} segundos."
        ),
        f"Se encontraron {len(resultados_abiertos)} puertos abiertos.",
        separador,
        "\n[+] Resultados del Escaneo (1-1024)",
    ]

    if resultados_abiertos:
        lineas_reporte.extend(resultados_abiertos)
    else:
        lineas_reporte.append(
            "  No se encontraron puertos abiertos en el rango (1-1024)."
        )

    lineas_reporte.append(f"\n{separador}\n")
    reporte_str = "\n".join(lineas_reporte)

    # Guardamos el informe en un archivo de texto junto al script.
    nombre_limpio = target_ip_str.replace(".", "_").replace(":", "_")
    filename = f"informe_ASYNC_{nombre_limpio}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as archivo:
            archivo.write(reporte_str)
        print(f"\n[+] ¡Informe guardado exitosamente en {filename}!")
    except Exception as exc:
        print(f"\n[!!!] Error al guardar el informe: {exc} [!!!]")

    print(reporte_str)


# --- Punto de entrada ---
if __name__ == "__main__":
    asyncio.run(main())