#pragma once
#include "sensor_base.hpp"

class SensorTrifasico : public SensorBase {
public:
    SensorTrifasico(const std::string& device_id, int seed = 42);

protected:
    nlohmann::json _generar_valores() override;

private:
    static constexpr double VOLTAJE_FASE   = 220.0;
    static constexpr double CORRIENTE_MAX  = 40.0;
    static constexpr double FRECUENCIA_NOM = 60.0;
};
