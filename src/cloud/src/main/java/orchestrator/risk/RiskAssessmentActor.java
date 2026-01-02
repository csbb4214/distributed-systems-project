package orchestrator.risk;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.alert.AlertPublisherActor;
import orchestrator.model.CloudEvent;

import java.util.Map;

public class RiskAssessmentActor extends AbstractBehavior<RiskAssessmentActor.Command> {

    public interface Command {}

    public record Assess(CloudEvent event) implements Command {}

    private static final Map<String, double[]> AREA_COORDS = Map.of(
            "areaA", new double[]{0, 0},
            "areaB", new double[]{3, 2},
            "areaC", new double[]{6, 1}
    );

    public static Behavior<Command> create(
            ActorRef<AlertPublisherActor.Command> alertPublisher
    ) {
        return Behaviors.setup(ctx ->
                new RiskAssessmentActor(ctx, alertPublisher)
        );
    }

    private final ActorRef<Command> alertPublisher;

    private RiskAssessmentActor(
            ActorContext<Command> context,
            ActorRef<AlertPublisherActor.Command> alertPublisher
    ) {
        super(context);
        this.alertPublisher = alertPublisher;
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Assess.class, this::onAssess)
                .build();
    }

    private Behavior<Command> onAssess(Assess msg) {
        for (String area : AREA_COORDS.keySet()) {
            if (!area.equals(msg.event.area())) {
                double severity = Math.min(1.0, msg.event.wind_speed() / 25.0);
                alertPublisher.tell(
                        new AlertPublisherActor.SendAlert(
                                area,
                                "Fire near " + msg.event.area() +
                                " severity=" + severity
                        )
                );
            }
        }
        return this;
    }
}
