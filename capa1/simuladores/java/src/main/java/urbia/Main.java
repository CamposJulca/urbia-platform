package urbia;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.*;

public class Main {

    private static final Logger log = Logger.getLogger("urbia.main");

    public static void main(String[] args) throws Exception {
        configureLogging();

        String brokerHost = System.getenv().getOrDefault("BROKER_HOST",   "192.168.0.101");
        int    brokerPort = Integer.parseInt(System.getenv().getOrDefault("BROKER_PORT",   "1883"));
        String nodeId     = System.getenv().getOrDefault("NODE_ID",       "192.168.0.105");
        int    intervalo  = Integer.parseInt(System.getenv().getOrDefault("INTERVALO_SEG", "5"));
        int    seedBase   = Integer.parseInt(System.getenv().getOrDefault("SEED_BASE",     "42"));

        var catalogo = new ObjectMapper().readTree(
            new File("/opt/urbia/capa1/comun/medidores_manizales.json"));

        List<SensorBase> sensores = new ArrayList<>();
        int idx = 0;
        for (var m : catalogo.get("medidores")) {
            if (m.get("nodo_origen").asText().equals(nodeId)) {
                String id   = m.get("device_id").asText();
                String tipo = m.get("device_type").asText();
                sensores.add(tipo.equals("mono")
                    ? new SensorMonofasico(id, seedBase + idx++)
                    : new SensorTrifasico(id,  seedBase + idx++));
            }
        }

        log.info("Nodo " + nodeId + " — " + sensores.size() + " sensores cargados");

        MQTTPublisher publisher = new MQTTPublisher(brokerHost, brokerPort, "urbia-sim-105");
        publisher.conectar();
        Thread.sleep(2000);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log.info("Señal de parada recibida");
            Thread.currentThread().interrupt();
        }));

        int ciclo = 0;
        while (!Thread.currentThread().isInterrupted()) {
            ciclo++;
            int enviados = 0;
            for (var s : sensores) {
                var lectura = s.generarLectura();
                String zona  = lectura.get("zona").asText();
                String tipo  = lectura.get("device_type").asText();
                String devId = lectura.get("device_id").asText();
                String topic = "urbia/manizales/" + zona + "/" + tipo + "/" + devId + "/telemetria";
                if (publisher.publicar(topic, lectura)) {
                    enviados++;
                }
            }
            if (ciclo % 12 == 0) {
                log.info("[ciclo " + ciclo + "] enviados: " + enviados +
                    "/" + sensores.size() + " | " + publisher.estadisticas());
            }
            Thread.sleep(intervalo * 1000L);
        }

        publisher.desconectar();
        log.info("Simulador detenido limpiamente");
    }

    private static void configureLogging() {
        Logger root = Logger.getLogger("");
        root.setLevel(Level.INFO);
        for (Handler h : root.getHandlers()) {
            h.setFormatter(new SimpleFormatter() {
                @Override public String format(LogRecord r) {
                    return String.format("%tFT%<tT [%s] %s — %s%n",
                        r.getMillis(), r.getLevel(), r.getLoggerName(), r.getMessage());
                }
            });
        }
    }
}
