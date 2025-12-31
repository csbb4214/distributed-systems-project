import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import io.nats.client.*;

public class AlertPublisherActor extends AbstractBehavior<AlertPublisherActor.Command> {

    public interface Command {}

    public static class SendAlert implements Command {
        public final String area;
        public final String text;
        public SendAlert(String area, String text) {
            this.area = area;
            this.text = text;
        }
    }

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
            nc = Nats.connect(natsUrl);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(SendAlert.class, this::onSendAlert)
                .build();
    }

    private Behavior<Command> onSendAlert(SendAlert msg) {
        nc.publish(
                "alerts." + msg.area,
                msg.text.getBytes()
        );
        getContext().getLog().info("🚨 Alert sent to {}", msg.area);
        return this;
    }
}
