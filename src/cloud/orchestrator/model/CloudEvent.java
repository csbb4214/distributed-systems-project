package orchestrator.model;

public record CloudEvent(
        String region,
        String area,
        double timestamp,
        double conf_fire,
        double wind_speed,
        double wind_direction,
        String frame_jpeg_b64
) {}