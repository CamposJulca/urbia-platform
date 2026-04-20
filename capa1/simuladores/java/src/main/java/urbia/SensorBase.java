package urbia;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.File;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.util.Map;

public abstract class SensorBase {
    protected final String deviceId, deviceType, zona, nodOrigen, lenguaje;
    protected final double lat, lon;
    protected final int seed;
    protected final java.util.Random rng;
    protected int mensajes = 0, errores = 0;
    private static final ObjectMapper mapper = new ObjectMapper();

    public SensorBase(String deviceId, int seed) throws Exception {
        this.deviceId = deviceId;
        this.seed     = seed;
        this.rng      = new java.util.Random(seed);

        File catalogo = new File("/opt/urbia/capa1/comun/medidores_manizales.json");
        var root = mapper.readTree(catalogo);
        for (var m : root.get("medidores")) {
            if (m.get("device_id").asText().equals(deviceId)) {
                this.deviceType = m.get("device_type").asText();
                this.zona       = m.get("zona").asText();
                this.lat        = m.get("lat").asDouble();
                this.lon        = m.get("lon").asDouble();
                this.nodOrigen  = m.get("nodo_origen").asText();
                this.lenguaje   = m.get("lenguaje").asText();
                return;
            }
        }
        throw new RuntimeException("device_id no encontrado: " + deviceId);
    }

    protected abstract Map<String, Object> generarValores();

    public ObjectNode generarLectura() {
        var v  = generarValores();
        var ts = DateTimeFormatter.ISO_INSTANT.format(Instant.now());
        var n  = mapper.createObjectNode();
        n.put("device_id",       deviceId);
        n.put("device_type",     deviceType);
        n.put("zona",            zona);
        n.put("timestamp_utc",   ts);
        n.put("voltaje_v",       (double) v.get("voltaje_v"));
        n.put("corriente_a",     (double) v.get("corriente_a"));
        n.put("potencia_kw",     (double) v.get("potencia_kw"));
        n.put("frecuencia_hz",   (double) v.get("frecuencia_hz"));
        n.put("factor_potencia", (double) v.get("factor_potencia"));
        n.put("lat",             lat);
        n.put("lon",             lon);
        n.put("estado",          (String) v.get("estado"));
        n.put("nodo_origen",     nodOrigen);
        n.put("lenguaje",        lenguaje);
        n.put("seed",            seed);
        mensajes++;
        return n;
    }

    protected double perfilHorario() {
        int hora = java.time.LocalTime.now().getHour();
        if (hora < 6)  return 0.15;
        if (hora < 12) return 0.60;
        if (hora < 14) return 0.85;
        if (hora < 18) return 0.65;
        if (hora < 22) return 0.90;
        return 0.40;
    }
}
