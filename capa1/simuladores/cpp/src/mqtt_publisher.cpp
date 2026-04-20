#include "mqtt_publisher.hpp"
#include <iostream>
#include <stdexcept>

MQTTPublisher::MQTTPublisher(const std::string& broker_host, int broker_port,
                             const std::string& client_id)
    : client_id(client_id) {
    broker_uri = "tcp://" + broker_host + ":" + std::to_string(broker_port);
    client = std::make_unique<mqtt::async_client>(broker_uri, client_id);
}

MQTTPublisher::~MQTTPublisher() {
    if (_conectado) {
        try { desconectar(); } catch (...) {}
    }
}

void MQTTPublisher::conectar() {
    auto opts = mqtt::connect_options_builder()
        .clean_session(false)
        .keep_alive_interval(std::chrono::seconds(60))
        .automatic_reconnect(std::chrono::seconds(2), std::chrono::seconds(30))
        .finalize();

    try {
        client->connect(opts)->wait();
        _conectado = true;
        std::cout << "[MQTT] Conectado a " << broker_uri << "\n";
    } catch (const mqtt::exception& e) {
        throw std::runtime_error(std::string("Error MQTT conectar: ") + e.what());
    }
}

bool MQTTPublisher::publicar(const std::string& topic, const nlohmann::json& payload) {
    if (!_conectado) {
        ++_errores;
        std::cerr << "[MQTT] Sin conexión — mensaje descartado\n";
        return false;
    }
    try {
        auto msg = mqtt::make_message(topic, payload.dump(), 1, false);
        client->publish(msg)->wait_for(std::chrono::seconds(5));
        ++_publicados;
        return true;
    } catch (const mqtt::exception& e) {
        ++_errores;
        std::cerr << "[MQTT] Error publicando en " << topic << ": " << e.what() << "\n";
        return false;
    }
}

void MQTTPublisher::desconectar() {
    try {
        client->disconnect()->wait();
        _conectado = false;
        std::cout << "[MQTT] Desconectado limpiamente\n";
    } catch (const mqtt::exception& e) {
        std::cerr << "[MQTT] Error al desconectar: " << e.what() << "\n";
    }
}

MQTTPublisher::Stats MQTTPublisher::estadisticas() const {
    return {_conectado ? 1 : 0, _publicados.load(), _errores.load()};
}
