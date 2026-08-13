import serial
import threading
import time
import re
from decimal import Decimal, InvalidOperation

class ScaleService:
    """Servicio de lectura RS232 para balanza Yaohua T7+ con ciclo de vida explícito."""

    def __init__(self, port: str = "COM4", baudrate: int = 1200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.current_weight: Decimal = Decimal('0.00')
        self._lock = threading.Lock()
        self.running = False
        self._thread = None

    def start(self):
        """Método explícito para iniciar el hilo de lectura en segundo plano."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print(f"🚀 [ScaleService] Iniciado en {self.port} a {self.baudrate} baudios.")

    def stop(self):
        """Detiene el hilo de lectura y libera recursos."""
        self.running = False
        print("⏹️ [ScaleService] Detenido.")

    def _read_loop(self):
        """Bucle continuo de lectura por puerto serie."""
        while self.running:
            try:
                with serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout
                ) as ser:
                    print(f"✅ [ScaleService] Puerto {self.port} abierto correctamente.")
                    
                    while self.running:
                        raw_bytes = ser.readline()
                        if raw_bytes:
                            raw_str = raw_bytes.decode('ascii', errors='ignore').strip()
                            
                            # Extrae el número numérico (ej: "wn00007.56kg" -> "00007.56")
                            match = re.search(r'([+-]?\d+\.?\d*)', raw_str)
                            if match:
                                try:
                                    peso = Decimal(match.group(1))
                                    with self._lock:
                                        self.current_weight = peso
                                except InvalidOperation:
                                    pass
            except Exception as e:
                #print(f"⚠️ [ScaleService] Error en {self.port}: {e}. Reintentando en 2s...")
                time.sleep(2)

    def get_weight(self) -> Decimal:
        """Devuelve el peso actual registrado de forma Thread-Safe."""
        with self._lock:
            return self.current_weight
            #return 40.24