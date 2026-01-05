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

    // TODO: This should be extern information for cloud/edge/IoT for data-coherence
    private static final Map<String, double[]> AREA_COORDS = Map.of(
            "areaA1", new double[]{0, 0},
            "areaB1", new double[]{3, 2}
    );

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Command> create(
            ActorRef<AlertPublisherActor.Command> alertPublisher
    ) {
        return Behaviors.setup(ctx ->
                new RiskAssessmentActor(ctx, alertPublisher)
        );
    }

    private final ActorRef<AlertPublisherActor.Command> alertPublisher;

    private RiskAssessmentActor(
            ActorContext<Command> context,
            ActorRef<AlertPublisherActor.Command> alertPublisher
    ) {
        super(context);
        this.alertPublisher = alertPublisher;
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
        double[] fireCoord = AREA_COORDS.get(msg.event.area());
        if (fireCoord == null) {
            return this;
        }

        // Convert wind direction (degrees) to unit vector
        double radians = Math.toRadians(msg.event.wind_direction());
        double windX = Math.sin(radians);   // East-West
        double windY = Math.cos(radians);   // North-South

        for (Map.Entry<String, double[]> entry : AREA_COORDS.entrySet()) {
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
                double ageSeconds = now - msg.event.timestamp();
                double timeFactor = Math.exp(-ageSeconds / 60.0);

                double urgency = windFactor * distanceFactor * timeFactor;
                alertPublisher.tell(
                        new AlertPublisherActor.SendAlert(
                                area,
                                "Fire near " + msg.event.area() + " urgency=" + urgency
                        )
                );
            }
        }
        return this;
    }
}
