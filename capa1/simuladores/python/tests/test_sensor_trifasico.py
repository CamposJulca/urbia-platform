import os
import sys
from pathlib import Path

# Apuntar al catálogo y al esquema antes de importar módulos que los leen
os.environ.setdefault(
    "COMUN_DIR",
    str(Path(__file__).parent.parent.parent.parent / "comun")
)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sensor_trifasico import SensorTrifasico, SQRT3
from payload_validator import PayloadValidator

DEVICE_ID = "urbia-ena-tri-0001"
SCHEMA    = Path(os.environ["COMUN_DIR"]) / "payload_schema_v1.json"

validator = PayloadValidator(SCHEMA)


# ── Rangos del esquema ────────────────────────────────────────────

def test_rangos_validos():
    """Todos los campos están dentro de los límites del esquema en 100 lecturas."""
    sensor = SensorTrifasico(DEVICE_ID, seed=7)
    for _ in range(100):
        v = sensor._generar_valores()
        assert 187.0 <= v["voltaje_v"]       <= 253.0, f"voltaje={v['voltaje_v']}"
        assert 0.0   <= v["corriente_a"]     <= 60.0,  f"corriente={v['corriente_a']}"
        assert 0.0   <= v["potencia_kw"]     <= 30.0,  f"potencia={v['potencia_kw']}"
        assert 57.0  <= v["frecuencia_hz"]   <= 63.0,  f"frecuencia={v['frecuencia_hz']}"
        assert 0.0   <= v["factor_potencia"] <= 1.0,   f"fp={v['factor_potencia']}"


def test_corriente_max_esquema():
    """corriente_a nunca supera los 60A del esquema."""
    sensor = SensorTrifasico(DEVICE_ID, seed=11)
    for _ in range(200):
        v = sensor._generar_valores()
        assert v["corriente_a"] <= 60.0, f"corriente={v['corriente_a']} > 60A"


# ── Reproducibilidad ──────────────────────────────────────────────

def test_reproducibilidad():
    """Misma semilla produce exactamente el mismo resultado."""
    s1 = SensorTrifasico(DEVICE_ID, seed=99)
    s2 = SensorTrifasico(DEVICE_ID, seed=99)
    assert s1._generar_valores() == s2._generar_valores()


def test_semillas_distintas_difieren():
    """Semillas distintas producen valores diferentes."""
    v1 = SensorTrifasico(DEVICE_ID, seed=1)._generar_valores()
    v2 = SensorTrifasico(DEVICE_ID, seed=2)._generar_valores()
    assert v1 != v2


# ── Física trifásica ──────────────────────────────────────────────

def test_formula_trifasica():
    """P = √3·V·I·fp/1000 cuando estado ≠ anomalia_voltaje (voltaje no se sobreescribe)."""
    sensor = SensorTrifasico(DEVICE_ID, seed=123)
    verificados = 0
    for _ in range(300):
        v = sensor._generar_valores()
        if v["estado"] != "anomalia_voltaje":
            esperado = SQRT3 * v["voltaje_v"] * v["corriente_a"] * v["factor_potencia"] / 1000.0
            assert abs(v["potencia_kw"] - esperado) < 1e-9, (
                f"potencia={v['potencia_kw']:.6f} esperado={esperado:.6f}"
            )
            verificados += 1
    assert verificados >= 290, f"Solo {verificados} casos verificados (esperado ≥290)"


def test_factor_potencia_rango_comercial():
    """fp siempre dentro del rango comercial/industrial 0.80–0.95."""
    sensor = SensorTrifasico(DEVICE_ID, seed=5)
    for _ in range(200):
        fp = sensor._generar_valores()["factor_potencia"]
        assert 0.80 <= fp <= 0.95, f"fp={fp} fuera del rango comercial"


# ── Validación end-to-end ─────────────────────────────────────────

def test_payload_pasa_validator():
    """El payload completo pasa las tres capas del PayloadValidator."""
    sensor = SensorTrifasico(DEVICE_ID, seed=42)
    lectura = sensor.generar_lectura()
    ok, msg = validator.validar(lectura)
    assert ok, f"Payload rechazado: {msg}"


def test_cien_lecturas_validas():
    """100 lecturas consecutivas pasan el validator sin rechazos."""
    sensor = SensorTrifasico(DEVICE_ID, seed=0)
    for i in range(100):
        ok, msg = validator.validar(sensor.generar_lectura())
        assert ok, f"Lectura {i} rechazada: {msg}"


# ── Distribución de estados ───────────────────────────────────────

def test_estados_distribucion():
    """Los tres estados posibles aparecen en 500 iteraciones."""
    sensor = SensorTrifasico(DEVICE_ID, seed=0)
    estados = {sensor._generar_valores()["estado"] for _ in range(500)}
    assert "activo"           in estados
    assert "anomalia_voltaje" in estados
    assert "falla"            in estados
