package urbia;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import java.util.logging.Logger;

public class MQTTPublisher {
    private static final Logger log = Logger.getLogger(MQTTPublisher.class.getName());
    private final ObjectMapper mapper = new ObjectMapper();

    private final String brokerUrl;
    private final String clientId;
    private MqttClient client;
    private volatile boolean conectado = false;
    private int publicados = 0;
    private int errores = 0;

    public MQTTPublisher(String brokerHost, int brokerPort, String clientId) {
        this.brokerUrl = "tcp://" + brokerHost + ":" + brokerPort;
        this.clientId  = clientId;
    }

    public void conectar() throws MqttException {
        client = new MqttClient(brokerUrl, clientId, new MemoryPersistence());
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(false);
        opts.setKeepAliveInterval(60);
        opts.setAutomaticReconnect(true);
        client.setCallback(new MqttCallbackExtended() {
            @Override public void connectComplete(boolean reconnect, String uri) {
                conectado = true;
                log.info("Conectado a " + uri + (reconnect ? " (reconexión)" : ""));
            }
            @Override public void connectionLost(Throwable cause) {
                conectado = false;
                log.warning("Conexión perdida: " + cause.getMessage());
            }
            @Override public void messageArrived(String t, MqttMessage m) {}
            @Override public void deliveryComplete(IMqttDeliveryToken t) { publicados++; }
        });
        client.connect(opts);
        conectado = true;
        log.info("Conectado a " + brokerUrl);
    }

    public boolean publicar(String topic, ObjectNode payload) {
        if (!conectado || client == null) {
            errores++;
            return false;
        }
        try {
            byte[] msg = mapper.writeValueAsBytes(payload);
            client.publish(topic, msg, 1, false);
            return true;
        } catch (Exception e) {
            errores++;
            log.warning("Error publicando en " + topic + ": " + e.getMessage());
            return false;
        }
    }

    public void desconectar() throws MqttException {
        if (client != null && client.isConnected()) {
            client.disconnect();
        }
    }

    public String estadisticas() {
        return "conectado=" + conectado + " publicados=" + publicados + " errores=" + errores;
    }
}
