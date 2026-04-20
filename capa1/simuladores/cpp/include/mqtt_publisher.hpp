#pragma once
#include <string>
#include <atomic>
#include <nlohmann/json.hpp>
#include <mqtt/async_client.h>

class MQTTPublisher {
public:
    MQTTPublisher(const std::string& broker_host, int broker_port = 1883,
                  const std::string& client_id = "urbia-sim-cpp");
    ~MQTTPublisher();

    void conectar();
    bool publicar(const std::string& topic, const nlohmann::json& payload);
    void desconectar();

    struct Stats {
        int conectado;
        int publicados;
        int errores;
    };
    Stats estadisticas() const;

private:
    std::string broker_uri;
    std::string client_id;
    std::unique_ptr<mqtt::async_client> client;
    std::atomic<bool> _conectado{false};
    std::atomic<int>  _publicados{0};
    std::atomic<int>  _errores{0};
};
