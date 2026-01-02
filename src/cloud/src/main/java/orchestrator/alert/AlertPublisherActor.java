package orchestrator.alert;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import io.nats.client.*;

public class AlertPublisherActor
        extends AbstractBehavior<AlertPublisherActor.Command> {

    // --------------------
    // Protocol
    // --------------------
    public interface Command {}

    public record SendAlert(
            String area,
            String text
    ) implements Command {}

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Command> create(String natsUrl) {
        return Behaviors.setup(ctx ->
                new AlertPublisherActor(ctx, natsUrl)
        );
    }

    private final Connection nc;

    private AlertPublisherActor(
            ActorContext<Command> context,
            String natsUrl
    ) {
        super(context);
        try {
            this.nc = Nats.connect(natsUrl);
        } catch (Exception e) {
            context.getLog().error("NATS connection failed", e);
            throw new RuntimeException(e);
        }
    }

    // --------------------
    // Behavior
    // --------------------
    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(SendAlert.class, this::onSendAlert)
                .onSignal(PostStop.class, signal -> onPostStop())
                .build();
    }

    private Behavior<Command> onSendAlert(SendAlert msg) {
        nc.publish(
                "alerts." + msg.area(),
                msg.text().getBytes()
        );
        getContext().getLog().info("Alert sent to {}", msg.area());
        return this;
    }

    private Behavior<Command> onPostStop() {
        if (nc != null) {
            try {
                nc.close();
                getContext().getLog().info("NATS connection closed (AlertPublisher)");
            } catch (Exception e) {
                getContext().getLog().warn("Error closing NATS connection", e);
            }
        }
        return this;
    }
}
