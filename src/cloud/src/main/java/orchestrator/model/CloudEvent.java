package orchestrator.model;

/*
 * NATS message pass
*/
public record CloudEvent(
        String region,
        String area,
        Trace trace,
        double conf_fire,
        double conf_smoke,
        double wind_speed,
        double wind_direction,
        String frame_jpeg_b64
) {}