FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /build
COPY pom.xml .
COPY src/ src/
RUN mvn package -q

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=builder /build/target/urbia-simulator-1.0.0-jar-with-dependencies.jar app.jar

ENV BROKER_HOST=192.168.0.101
ENV BROKER_PORT=1883
ENV NODE_ID=192.168.0.105
ENV INTERVALO_SEG=5
ENV SEED_BASE=42

CMD ["java", "-jar", "app.jar"]
