FROM gcc:13 AS builder

RUN apt-get update && apt-get install -y \
    cmake \
    nlohmann-json3-dev \
    libssl-dev \
    libpaho-mqtt-dev \
    libpaho-mqttpp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY CMakeLists.txt .
COPY src/ src/
COPY include/ include/

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j$(nproc)

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    libpaho-mqtt-dev \
    libpaho-mqttpp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /build/build/urbia_sensor .

ENV BROKER_HOST=192.168.0.101
ENV BROKER_PORT=1883
ENV NODE_ID=192.168.0.104
ENV INTERVALO_SEG=5
ENV SEED_BASE=42

CMD ["./urbia_sensor"]
