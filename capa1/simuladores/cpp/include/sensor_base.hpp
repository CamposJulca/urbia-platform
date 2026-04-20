#pragma once
#include <string>
#include <map>
#include <random>
#include <nlohmann/json.hpp>

class SensorBase {
public:
    SensorBase(const std::string& device_id, int seed = 42);
    virtual ~SensorBase() = default;

    nlohmann::json generar_lectura();
    std::map<std::string, int> estadisticas() const;

protected:
    virtual nlohmann::json _generar_valores() = 0;
    double _perfil_horario() const;

    std::string device_id, device_type, zona, nodo_origen, lenguaje;
    double lat, lon;
    int seed;
    std::mt19937 rng;
    int _mensajes = 0, _errores = 0;
};
