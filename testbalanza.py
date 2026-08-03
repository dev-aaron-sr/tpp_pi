import serial
import serial.tools.list_ports
import time

# 1. MUESTRA TODOS LOS PUERTOS COM DISPONIBLES EN TU PC
print("🔍 Buscando puertos COM activos...")
ports = list(serial.tools.list_ports.comports())

if not ports:
    print("❌ No se detectó ningún puerto COM. Revisa el cable o falta instalar el driver USB-Serial.")
else:
    print("--------------------------------------------------")
    for p in ports:
        print(f"📌 Puerto detectado: {p.device} - {p.description}")
    print("--------------------------------------------------\n")

# 2. CONFIGURA AQUÍ TU PUERTO COM (ejemplo: 'COM3', 'COM4', etc.)
PUERTO = "COM4"      # 👈 Cambia esto por el puerto de tu adaptador
BAUDIOS = 1200       # Velocidad por defecto del Yaohua T7+

try:
    print(f"🔌 Intentando abrir {PUERTO} a {BAUDIOS} baudios...")
    ser = serial.Serial(
        port=PUERTO,
        baudrate=BAUDIOS,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1.0
    )

    print(f"✅ ¡Conectado a {PUERTO}! Esperando tramas de la balanza (Presiona Ctrl+C para salir):\n")

    while True:
        # Lee bytes directos del puerto
        raw_bytes = ser.readline()
        
        if raw_bytes:
            # 1. Muestra bytes en crudo (ideal para ver caracteres de control como \r \n =)
            print(f"BYTES RAW : {raw_bytes}")
            
            # 2. Decodifica a texto legible
            texto = raw_bytes.decode('ascii', errors='ignore').strip()
            print(f"TEXTO     : {texto}")
            print("-" * 50)
        else:
            print("⏳ Esperando datos... (puerto abierto pero no recibe bytes)")
            time.sleep(0.5)

except serial.SerialException as e:
    print(f"\n❌ Error al acceder al puerto {PUERTO}: {e}")
    print("💡 Consejos:")
    print("   1. Revisa en el Administrador de Dispositivos (devmgmt.msc) qué número de COM tiene tu adaptador.")
    print("   2. Asegúrate de haber instalado el driver del cable (CH340, FTDI, PL2303, CP2102).")
except KeyboardInterrupt:
    print("\n\n⏹️ Lectura detenida por el usuario.")
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Puerto cerrado correctamente.")