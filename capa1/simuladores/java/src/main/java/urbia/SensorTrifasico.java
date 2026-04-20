package urbia;

import java.util.Map;

public class SensorTrifasico extends SensorBase {

    public SensorTrifasico(String deviceId, int seed) throws Exception {
        super(deviceId, seed);
    }

    @Override
    protected Map<String, Object> generarValores() {
        double factor   = perfilHorario();
        double voltaje  = clamp(220.0 + rng.nextGaussian() * 4.4, 198.0, 242.0);
        double corriente = clamp(rng.nextDouble() * 40.0 * factor, 0.0, 40.0);
        double fp       = 0.82 + rng.nextDouble() * 0.13;
        double frec     = clamp(60.0 + rng.nextGaussian() * 0.15, 59.0, 61.0);
        double potencia = voltaje * corriente * fp / 1000.0;
        double r        = rng.nextDouble();
        String estado   = r < 0.01 ? "anomalia_voltaje" : r < 0.02 ? "falla" : "activo";

        return Map.of(
            "voltaje_v",       round(voltaje, 3),
            "corriente_a",     round(corriente, 3),
            "potencia_kw",     round(potencia, 4),
            "frecuencia_hz",   round(frec, 3),
            "factor_potencia", round(fp, 3),
            "estado",          estado
        );
    }

    private double clamp(double v, double min, double max) {
        return Math.max(min, Math.min(max, v));
    }

    private double round(double v, int d) {
        double f = Math.pow(10, d);
        return Math.round(v * f) / f;
    }
}
