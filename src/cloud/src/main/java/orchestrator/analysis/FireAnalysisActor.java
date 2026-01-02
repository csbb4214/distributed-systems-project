package orchestrator.analysis;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.model.CloudEvent;
import orchestrator.risk.RiskAssessmentActor;

import java.util.concurrent.CompletableFuture;

public class FireAnalysisActor extends AbstractBehavior<FireAnalysisActor.Command> {

    // --------------------
    // Protocol
    // --------------------
    public interface Command {}

    public record Analyze(CloudEvent event) implements Command {}

    private record MLConfirmed(
            CloudEvent event,
            double confidence
    ) implements Command {}

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Command> create(
            ActorRef<RiskAssessmentActor.Command> riskAssessment,
            MLInferenceClient mlClient
    ) {
        return Behaviors.setup(ctx ->
                new FireAnalysisActor(ctx, riskAssessment, mlClient)
        );
    }

    private final ActorRef<RiskAssessmentActor.Command> riskAssessment;
    private final MLInferenceClient mlClient;

    private FireAnalysisActor(
            ActorContext<Command> context,
            ActorRef<RiskAssessmentActor.Command> riskAssessment,
            MLInferenceClient mlClient
    ) {
        super(context);
        this.riskAssessment = riskAssessment;
        this.mlClient = mlClient;
    }

    // --------------------
    // Behavior
    // --------------------
    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Analyze.class, this::onAnalyze)
                .onMessage(MLConfirmed.class, this::onMLConfirmed)
                .build();
    }

    private Behavior<Command> onAnalyze(Analyze msg) {
        CompletableFuture
                .supplyAsync(() -> {
                    try {
                        return mlClient.infer(msg.event().frame_jpeg_b64());
                    } catch (Exception e) {
                        return null;
                    }
                })
                .thenAccept(result -> {
                    if (result != null && result.fire()) {
                        getContext().getSelf().tell(
                                new MLConfirmed(msg.event(), result.confidence())
                        );
                    }
                });

        return this;
    }

    private Behavior<Command> onMLConfirmed(MLConfirmed msg) {
        getContext().getLog().info(
                "ML confirmed fire in {} (conf={})",
                msg.event().area(),
                msg.confidence()
        );

        riskAssessment.tell(
                new RiskAssessmentActor.Assess(msg.event())
        );

        return this;
    }
}
