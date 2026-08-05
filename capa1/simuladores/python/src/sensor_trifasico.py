import math

from sensor_base import SensorBase

SQRT3 = math.sqrt(3)


class SensorTrifasico(SensorBase):
    """
    Simulador de medidor trifásico de baja tensión, uso comercial/industrial.

    Voltaje de línea nominal: 220V (rango esquema 187–253V).
    Corriente máxima: 60A — techo del esquema payload_schema_v1.json.
    Justificación: cuadros de distribución comerciales/industriales en
    Colombia operan típicamente 30–60A por fase (motores, compresores,
    iluminación industrial, variadores de frecuencia). 60A cubre
    instalaciones de hasta ~21 kVA en configuración trifásica estándar y
    coincide con el límite del esquema, evitando clamp en operación normal.

    Potencia activa trifásica: P = √3 · V_linea · I_linea · fp / 1000
    Peor caso en esquema: √3 · 253 · 60 · 0.95 / 1000 ≈ 24.98 kW < 30 kW.

    Factor de potencia 0.80–0.95: menor que el residencial (0.88–0.98) por
    la presencia de cargas inductivas (motores asincrónicos, balastos,
    UPS, variadores), que generan corriente reactiva inductiva.

    Zonas: La Enea, Palermo, Universitario — Manizales.
    """

    VOLTAJE_NOMINAL = 220.0
    CORRIENTE_MAX   = 60.0
    FRECUENCIA_NOM  = 60.0

    def _generar_valores(self) -> dict:
        factor = self._perfil_horario()

        # Voltaje de línea: 220V ±2% con ruido gaussiano
        voltaje = float(self.rng.normal(
            self.VOLTAJE_NOMINAL,
            self.VOLTAJE_NOMINAL * 0.02
        ))
        voltaje = max(198.0, min(242.0, voltaje))

        # Corriente según perfil horario (carga comercial/industrial)
        corriente = float(self.rng.uniform(
            self.CORRIENTE_MAX * factor * 0.3,
            self.CORRIENTE_MAX * factor
        ))
        corriente = max(0.0, min(self.CORRIENTE_MAX, corriente))

        # Factor de potencia comercial/industrial: 0.80–0.95
        fp = float(self.rng.uniform(0.80, 0.95))

        # Frecuencia: 60Hz ±0.3Hz
        frecuencia = float(self.rng.normal(self.FRECUENCIA_NOM, 0.15))
        frecuencia = max(59.0, min(61.0, frecuencia))

        # Potencia activa trifásica: P = √3 · V_linea · I_linea · fp / 1000
        # Peor caso: √3·253·60·0.95/1000 ≈ 24.98 kW — clamp defensivo a 30 kW
        potencia_kw = SQRT3 * voltaje * corriente * fp / 1000.0
        potencia_kw = min(potencia_kw, 30.0)

        # Estado: 98% activo, 1% anomalia_voltaje, 1% falla
        r = float(self.rng.random())
        if r < 0.01:
            estado = "anomalia_voltaje"
            voltaje = float(self.rng.uniform(243.0, 250.0))
        elif r < 0.02:
            estado = "falla"
        else:
            estado = "activo"

        return {
            "voltaje_v":       voltaje,
            "corriente_a":     corriente,
            "potencia_kw":     potencia_kw,
            "frecuencia_hz":   frecuencia,
            "factor_potencia": fp,
            "estado":          estado,
        }
