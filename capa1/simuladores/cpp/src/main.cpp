/**
 * UrbIA — Simulador C++ · Nodo .104
 * Publica telemetría de 50 medidores trifásicos (La Enea y Palermo)
 * al broker MQTT en .101:1883
 */
#include <iostream>
#include <fstream>
#include <vector>
#include <memory>
#include <thread>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <nlohmann/json.hpp>
#include "sensor_trifasico.hpp"
#include "mqtt_publisher.hpp"

static volatile bool running = true;
void signal_handler(int) { running = false; }

int main() {
    signal(SIGTERM, signal_handler);
    signal(SIGINT,  signal_handler);

    const char* broker_host = std::getenv("BROKER_HOST")    ?: "192.168.0.101";
    int broker_port         = std::atoi(std::getenv("BROKER_PORT")    ?: "1883");
    const char* node_id     = std::getenv("NODE_ID")         ?: "192.168.0.104";
    int intervalo           = std::atoi(std::getenv("INTERVALO_SEG")  ?: "5");
    int seed_base           = std::atoi(std::getenv("SEED_BASE")      ?: "42");

    std::ifstream f("/opt/urbia/capa1/comun/medidores_manizales.json");
    if (!f.is_open()) {
        std::cerr << "[ERROR] No se puede abrir medidores_manizales.json\n";
        return 1;
    }
    nlohmann::json catalogo = nlohmann::json::parse(f);

    std::vector<std::unique_ptr<SensorTrifasico>> sensores;
    int idx = 0;
    for (auto& m : catalogo["medidores"]) {
        if (m["nodo_origen"] == node_id) {
            sensores.push_back(std::make_unique<SensorTrifasico>(
                m["device_id"].get<std::string>(), seed_base + idx++
            ));
        }
    }

    if (sensores.empty()) {
        std::cerr << "[ERROR] No hay medidores asignados a nodo " << node_id << "\n";
        return 1;
    }

    std::cout << "[UrbIA C++] Nodo " << node_id
              << " — " << sensores.size() << " sensores cargados\n";

    MQTTPublisher publisher(broker_host, broker_port, "urbia-sim-104");
    try {
        publisher.conectar();
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] " << e.what() << "\n";
        return 1;
    }
    std::this_thread::sleep_for(std::chrono::seconds(2));
    std::cout << "[UrbIA C++] Iniciando simulación — intervalo: "
              << intervalo << "s\n";

    int ciclo = 0;
    while (running) {
        ++ciclo;
        int enviados = 0;

        for (auto& s : sensores) {
            auto lectura = s->generar_lectura();
            std::string zona      = lectura["zona"];
            std::string dev_type  = lectura["device_type"];
            std::string device_id = lectura["device_id"];
            std::string topic = "urbia/manizales/" + zona + "/" +
                                dev_type + "/" + device_id + "/telemetria";
            if (publisher.publicar(topic, lectura))
                ++enviados;
        }

        if (ciclo % 12 == 0) {
            auto stats = publisher.estadisticas();
            std::cout << "[ciclo " << ciclo << "] enviados: "
                      << enviados << "/" << sensores.size()
                      << " | total_pub: " << stats.publicados
                      << " | errores: "   << stats.errores << "\n";
        }

        std::this_thread::sleep_for(std::chrono::seconds(intervalo));
    }

    publisher.desconectar();
    std::cout << "[UrbIA C++] Detenido limpiamente\n";
    return 0;
}
