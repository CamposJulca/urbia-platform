#include "sensor_trifasico.hpp"
#include <algorithm>

SensorTrifasico::SensorTrifasico(const std::string& device_id, int seed)
    : SensorBase(device_id, seed) {}

nlohmann::json SensorTrifasico::_generar_valores() {
    double factor = _perfil_horario();

    std::normal_distribution<double>       dist_v(VOLTAJE_FASE, VOLTAJE_FASE * 0.02);
    std::uniform_real_distribution<double> dist_i(
        CORRIENTE_MAX * factor * 0.3,
        CORRIENTE_MAX * factor
    );
    std::uniform_real_distribution<double> dist_fp(0.82, 0.95);
    std::normal_distribution<double>       dist_f(FRECUENCIA_NOM, 0.15);
    std::uniform_real_distribution<double> dist_r(0.0, 1.0);

    double voltaje    = std::clamp(dist_v(rng), 198.0, 242.0);
    double corriente  = std::clamp(dist_i(rng), 0.0, CORRIENTE_MAX);
    double fp         = dist_fp(rng);
    double frecuencia = std::clamp(dist_f(rng), 59.0, 61.0);
    double potencia   = voltaje * corriente * fp / 1000.0;

    std::string estado = "activo";
    double r = dist_r(rng);
    if (r < 0.01) {
        estado = "anomalia_voltaje";
        std::uniform_real_distribution<double> d(243.0, 250.0);
        voltaje = d(rng);
        potencia = voltaje * corriente * fp / 1000.0;
    } else if (r < 0.02) {
        estado = "falla";
    }

    auto rnd = [](double v, int d) {
        double f = std::pow(10.0, d);
        return std::round(v * f) / f;
    };

    return {
        {"voltaje_v",       rnd(voltaje,    3)},
        {"corriente_a",     rnd(corriente,  3)},
        {"potencia_kw",     rnd(potencia,   4)},
        {"frecuencia_hz",   rnd(frecuencia, 3)},
        {"factor_potencia", rnd(fp,         3)},
        {"estado",          estado},
    };
}
