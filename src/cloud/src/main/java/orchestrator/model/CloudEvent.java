package orchestrator.model;

/*
 * Datastructure for Nats message pass
*/
public record CloudEvent(
        String region,
        String area,
        double timestamp,
        double conf_fire,
        double wind_speed,
        double wind_direction,
        String frame_jpeg_b64
) {}