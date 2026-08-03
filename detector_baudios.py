import serial
import time

PUERTO = "COM4"
BAUDIOS_PROBAR = [9600, 4800, 2400, 1200]

print("BUSCANDO VELOCIDAD EN BAUDIOS DE COMUNICACION SERIAL...")

for baud in BAUDIOS_PROBAR:
    print(f"\n--------------------------------------------------")
    print(f"👉 Probando a {baud} baudios...")
    try:
        ser = serial.Serial(
            port=PUERTO,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.5
        )
        
        # Leer 50 bytes de prueba
        trama = ser.read(60)
        ser.close()

        if trama:
            print(f"   BYTES RAW : {trama}")
            texto = trama.decode('ascii', errors='ignore').strip()
            print(f"   TEXTO     : {texto}")
            
            # Si encontramos números o el guion de negativo (-0.21)
            if any(char.isdigit() for char in texto):
                print(f"   🎉 ¡ÉXITO! La velocidad correcta es {baud} baudios.")
                break
        else:
            print("   (Sin datos recibidos en este baudrate)")

    except Exception as e:
        print(f"   Error al probar {baud}: {e}")

print("\n--------------------------------------------------")