package orchestrator.analysis;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.alert.AlertPublisherActor;
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
            ActorRef<AlertPublisherActor.Command> alertPublisher,
            MLInferenceClient mlClient
    ) {
        return Behaviors.setup(ctx ->
                new FireAnalysisActor(ctx, riskAssessment, alertPublisher, mlClient)
        );
    }

    private final ActorRef<RiskAssessmentActor.Command> riskAssessment;
    private final ActorRef<AlertPublisherActor.Command> alertPublisher;
    private final MLInferenceClient mlClient;

    private FireAnalysisActor(
            ActorContext<Command> context,
            ActorRef<RiskAssessmentActor.Command> riskAssessment,
            ActorRef<AlertPublisherActor.Command> alertPublisher,
            MLInferenceClient mlClient
    ) {
        super(context);
        this.riskAssessment = riskAssessment;
        this.alertPublisher = alertPublisher;
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

        // Mark ML request start
        msg.event().trace().timestamps().put(
                "ml_request_start",
                System.nanoTime()
        );

        CompletableFuture
                .supplyAsync(() -> {
                    try {
                        return mlClient.infer(msg.event().frame_jpeg_b64());
                    } catch (Exception e) {
                        return null;
                    }
                })
                .thenAccept(result -> {
                    if (result != null && result.fireProbability() > 0.7) {

                        // Mark ML request end
                        msg.event().trace().timestamps().put(
                                "ml_request_end",
                                System.nanoTime()
                        );

                        // Mark Cloud decision time
                        msg.event().trace().timestamps().put(
                                "cloud_decision",
                                System.nanoTime()
                        );

                        getContext().getSelf().tell(
                                new MLConfirmed(msg.event(), result.fireProbability())
                        );
                    }
                });

        return this;
    }

    private Behavior<Command> onMLConfirmed(MLConfirmed msg) {
        String affectedArea = msg.event().area();

        getContext().getLog().info(
                "ML confirmed fire in {} (conf={})",
                affectedArea,
                msg.confidence()
        );

        // Alarm publication timestamp
        msg.event().trace().timestamps().put(
                "alarm_published",
                System.nanoTime()
        );

        alertPublisher.tell(
                new AlertPublisherActor.SendAlert(
                        affectedArea,
                        "Fire detected confidence=" + msg.confidence(),
                        msg.event().trace()   // pass trace forward
                )
        );

        riskAssessment.tell(
                new RiskAssessmentActor.Assess(msg.event())
        );

        return this;
    }
}
