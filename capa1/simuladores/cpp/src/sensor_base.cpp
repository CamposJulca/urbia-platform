#include "sensor_base.hpp"
#include <fstream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <ctime>
#include <stdexcept>

SensorBase::SensorBase(const std::string& device_id, int seed)
    : device_id(device_id), seed(seed), rng(seed) {

    std::ifstream f("/opt/urbia/capa1/comun/medidores_manizales.json");
    if (!f.is_open())
        throw std::runtime_error("No se puede abrir medidores_manizales.json");

    nlohmann::json catalogo = nlohmann::json::parse(f);

    for (auto& m : catalogo["medidores"]) {
        if (m["device_id"] == device_id) {
            device_type = m["device_type"];
            zona        = m["zona"];
            lat         = m["lat"];
            lon         = m["lon"];
            nodo_origen = m["nodo_origen"];
            lenguaje    = m["lenguaje"];
            return;
        }
    }
    throw std::runtime_error("device_id no encontrado: " + device_id);
}

nlohmann::json SensorBase::generar_lectura() {
    auto valores = _generar_valores();

    auto now = std::chrono::system_clock::now();
    auto t   = std::chrono::system_clock::to_time_t(now);
    auto ms  = std::chrono::duration_cast<std::chrono::milliseconds>(
                   now.time_since_epoch()) % 1000;

    std::ostringstream ts;
    ts << std::put_time(std::gmtime(&t), "%Y-%m-%dT%H:%M:%S")
       << "." << std::setfill('0') << std::setw(3) << ms.count() << "Z";

    ++_mensajes;
    return {
        {"device_id",       device_id},
        {"device_type",     device_type},
        {"zona",            zona},
        {"timestamp_utc",   ts.str()},
        {"voltaje_v",       valores["voltaje_v"]},
        {"corriente_a",     valores["corriente_a"]},
        {"potencia_kw",     valores["potencia_kw"]},
        {"frecuencia_hz",   valores["frecuencia_hz"]},
        {"factor_potencia", valores["factor_potencia"]},
        {"lat",             lat},
        {"lon",             lon},
        {"estado",          valores["estado"]},
        {"nodo_origen",     nodo_origen},
        {"lenguaje",        lenguaje},
        {"seed",            seed},
    };
}

double SensorBase::_perfil_horario() const {
    auto t    = std::time(nullptr);
    int  hora = std::localtime(&t)->tm_hour;
    if (hora < 6)  return 0.15;
    if (hora < 12) return 0.60;
    if (hora < 14) return 0.85;
    if (hora < 18) return 0.65;
    if (hora < 22) return 0.90;
    return 0.40;
}

std::map<std::string, int> SensorBase::estadisticas() const {
    return {{"mensajes", _mensajes}, {"errores", _errores}};
}
