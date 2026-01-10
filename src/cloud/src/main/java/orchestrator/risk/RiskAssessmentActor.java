package orchestrator.risk;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.alert.AlertPublisherActor;
import orchestrator.model.CloudEvent;

import java.util.Map;

public class RiskAssessmentActor extends AbstractBehavior<RiskAssessmentActor.Command> {

    // --------------------
    // Protocol
    // --------------------
    public interface Command {}

    public record Assess(CloudEvent event) implements Command {}

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Command> create(
            ActorRef<AlertPublisherActor.Command> alertPublisher,
            Map<String, double[]> areaCoords
    ) {
        return Behaviors.setup(ctx ->
                new RiskAssessmentActor(ctx, alertPublisher, areaCoords)
        );
    }

    private final ActorRef<AlertPublisherActor.Command> alertPublisher;
    // This should technically be extern information for cloud/edge/IoT for data-coherence
    private final Map<String, double[]> areaCoords;

    private RiskAssessmentActor(
            ActorContext<Command> context,
            ActorRef<AlertPublisherActor.Command> alertPublisher,
            Map<String, double[]> areaCoords
    ) {
        super(context);
        this.alertPublisher = alertPublisher;
        this.areaCoords = areaCoords;
    }

    // --------------------
    // Behavior
    // --------------------
    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Assess.class, this::onAssess)
                .build();
    }

    private Behavior<Command> onAssess(Assess msg) {
        double[] fireCoord = areaCoords.get(msg.event.area());
        if (fireCoord == null) {
            return this;
        }

        // Convert wind direction (degrees) to unit vector
        double radians = Math.toRadians(msg.event.wind_direction());
        double windX = Math.sin(radians);   // East-West
        double windY = Math.cos(radians);   // North-South

        for (Map.Entry<String, double[]> entry : areaCoords.entrySet()) {
            String area = entry.getKey();
            double[] targetCoord = entry.getValue();

            if (area.equals(msg.event.area())) {
                continue;
            }

            // Vector from fire to target area
            double dx = targetCoord[0] - fireCoord[0];
            double dy = targetCoord[1] - fireCoord[1];

            // Dot product: >0 means that this is roughly the direction
            double dot = dx * windX + dy * windY;

            if (dot > 0) {
                // Calculate urgency value based on wind speed, distance, and time passed
                double windFactor = Math.min(1.0, msg.event.wind_speed() / 25.0);

                double distance = Math.sqrt(dx * dx + dy * dy);
                double distanceFactor = Math.exp(-distance / 5.0);

                double now = System.currentTimeMillis() / 1000.0;
                double ageSeconds = now - msg.event.trace().timestamps().get("iot_capture");
                double timeFactor = Math.exp(-ageSeconds / 60.0);

                double urgency = windFactor * distanceFactor * timeFactor;
                alertPublisher.tell(
                        new AlertPublisherActor.SendAlert(
                                area,
                                "Fire near " + msg.event.area() + " urgency=" + urgency,
                                msg.event().trace())
                );
            }
        }
        return this;
    }
}
