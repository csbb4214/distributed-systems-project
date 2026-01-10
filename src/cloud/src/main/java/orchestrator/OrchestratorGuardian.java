package orchestrator;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.alert.AlertPublisherActor;
import orchestrator.analysis.FireAnalysisActor;
import orchestrator.analysis.MLInferenceClient;
import orchestrator.ingest.NatsIngestActor;
import orchestrator.risk.RiskAssessmentActor;

import java.util.Map;

public class OrchestratorGuardian extends AbstractBehavior<Void> {

    // --------------------
    // Factory
    // --------------------
    public static Behavior<Void> create(String natsUrl, String mlUrl, Map<String, double[]> areaCoords) {
        return Behaviors.setup(ctx -> new OrchestratorGuardian(ctx, natsUrl, mlUrl, areaCoords));
    }

    private OrchestratorGuardian(ActorContext<Void> context, String natsUrl, String mlUrl, Map<String, double[]> areaCoords) {
        super(context);

        // create client for communication with ML model
        MLInferenceClient mlClient = new MLInferenceClient(mlUrl);

        // launch all actors
        ActorRef<AlertPublisherActor.Command> alertPublisher =
                context.spawn(AlertPublisherActor.create(natsUrl), "alertPublisher");
        ActorRef<RiskAssessmentActor.Command> riskAssessment =
                context.spawn(RiskAssessmentActor.create(alertPublisher, areaCoords), "riskAssessment");
        ActorRef<FireAnalysisActor.Command> fireAnalysis =
                context.spawn(FireAnalysisActor.create(riskAssessment, alertPublisher, mlClient), "fireAnalysis");
        context.spawn(NatsIngestActor.create(natsUrl, fireAnalysis), "natsIngest");
    }

    // --------------------
    // Behavior
    // --------------------
    @Override
    public Receive<Void> createReceive() {
        return newReceiveBuilder().build();
    }
}
