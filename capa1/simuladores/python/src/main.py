"""
UrbIA — Simulador Python
Publica la telemetría de los medidores del catálogo cuyo `nodo_origen`
coincide con NODE_ID (mono y/o trifásicos) al broker MQTT.
Una instancia por nodo; todo se configura por variables de entorno.
"""
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sensor_monofasico import SensorMonofasico
from sensor_trifasico  import SensorTrifasico
from mqtt_publisher    import MQTTPublisher
from payload_validator import PayloadValidator


def _crear_sensor(m: dict, seed: int):
    cls = SensorTrifasico if m["device_type"] == "trifasico" else SensorMonofasico
    return cls(m["device_id"], seed=seed)

# ── Configuración via variables de entorno ──────────────────────
BROKER_HOST  = os.getenv("BROKER_HOST",   "192.168.0.101")
BROKER_PORT  = int(os.getenv("BROKER_PORT", "1883"))
NODE_ID      = os.getenv("NODE_ID",       "192.168.0.103")
INTERVALO    = float(os.getenv("INTERVALO_SEG", "5"))
LOG_LEVEL    = os.getenv("LOG_LEVEL",     "INFO")
SEED_BASE    = int(os.getenv("SEED_BASE", "42"))

# client_id MQTT: único por instancia. Con clean_session=False dos clientes
# con el mismo id se expulsan mutuamente del broker en bucle, así que el
# default se deriva del último octeto del NODE_ID (.103 → urbia-sim-103) y
# se puede sobreescribir con MQTT_CLIENT_ID.
MQTT_CLIENT_ID = os.getenv(
    "MQTT_CLIENT_ID", f"urbia-sim-{NODE_ID.rsplit('.', 1)[-1]}"
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/simulador.log"),
    ]
)
logger = logging.getLogger("urbia.main")


def cargar_medidores():
    catalogo = json.load(open(
        Path(__file__).parent.parent / "comun" / "medidores_manizales.json"
    ))
    return [m for m in catalogo["medidores"] if m["nodo_origen"] == NODE_ID]


def main():
    medidores_info = cargar_medidores()
    logger.info(f"Nodo {NODE_ID} — {len(medidores_info)} medidores asignados")

    sensores   = [_crear_sensor(m, SEED_BASE + i) for i, m in enumerate(medidores_info)]
    publisher  = MQTTPublisher(BROKER_HOST, BROKER_PORT, MQTT_CLIENT_ID)
    validator  = PayloadValidator()

    publisher.conectar()
    time.sleep(2)
    logger.info(
        f"Conectado a {BROKER_HOST}:{BROKER_PORT} "
        f"(client_id={MQTT_CLIENT_ID}) — iniciando simulación"
    )

    running = [True]
    def stop(sig, frame):
        running[0] = False
        logger.info("Señal de parada recibida")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    ciclo = 0
    while running[0]:
        ciclo += 1
        enviados = 0
        for sensor in sensores:
            lectura = sensor.generar_lectura()
            ok, msg = validator.validar(lectura)
            if not ok:
                logger.warning(f"Payload inválido {sensor.device_id}: {msg}")
                continue
            topic = f"urbia/manizales/{lectura['zona']}/{lectura['device_type']}/{lectura['device_id']}/telemetria"
            if publisher.publicar(topic, lectura):
                enviados += 1

        if ciclo % 12 == 0:  # log cada minuto (12 ciclos × 5s)
            stats_pub = publisher.estadisticas()
            stats_val = validator.estadisticas()
            logger.info(
                f"Ciclo {ciclo} — enviados:{enviados}/{len(sensores)} "
                f"total_pub:{stats_pub['publicados']} "
                f"tasa_valid:{stats_val['tasa_exito_pct']}%"
            )

        time.sleep(INTERVALO)

    publisher.desconectar()
    logger.info("Simulador detenido limpiamente")


if __name__ == "__main__":
    main()
