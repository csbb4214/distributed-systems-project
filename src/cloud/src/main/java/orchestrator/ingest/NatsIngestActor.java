package orchestrator.ingest;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.nats.client.*;
import orchestrator.analysis.FireAnalysisActor;
import orchestrator.model.CloudEvent;

public class NatsIngestActor extends AbstractBehavior<Void> {

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Void> create(
            String natsUrl,
            ActorRef<FireAnalysisActor.Command> fireAnalysis
    ) {
        return Behaviors.setup(ctx ->
                new NatsIngestActor(ctx, natsUrl, fireAnalysis)
        );
    }

    private final ObjectMapper mapper = new ObjectMapper();
    private final Connection nc;

    private NatsIngestActor(
            ActorContext<Void> context,
            String natsUrl,
            ActorRef<FireAnalysisActor.Command> fireAnalysis
    ) {
        super(context);

        try {
            this.nc = Nats.connect(natsUrl);

            Dispatcher dispatcher = nc.createDispatcher(msg -> {
                try {
                    CloudEvent event =
                            mapper.readValue(msg.getData(), CloudEvent.class);
                    fireAnalysis.tell(new FireAnalysisActor.Analyze(event));
                } catch (Exception e) {
                    context.getLog().error("JSON parse failed", e);
                }
            });

            dispatcher.subscribe("region.*.processed");

            context.getLog().info("Subscribed to region.*.processed");
        } catch (Exception e) {
            context.getLog().error("NATS connection failed", e);
            throw new RuntimeException(e);
        }
    }

    // --------------------
    // Behavior
    // --------------------
    @Override
    public Receive<Void> createReceive() {
        return newReceiveBuilder()
                .onSignal(PostStop.class, signal -> onPostStop())
                .build();
    }

    private Behavior<Void> onPostStop() {
        if (nc != null) {
            try {
                nc.close();
                getContext().getLog().info("NATS connection closed (NatsIngest)");
            } catch (Exception e) {
                getContext().getLog().warn("Error closing NATS connection", e);
            }
        }
        return this;
    }
}
