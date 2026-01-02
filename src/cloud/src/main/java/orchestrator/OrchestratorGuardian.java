package orchestrator;

import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;
import orchestrator.alert.AlertPublisherActor;
import orchestrator.analysis.FireAnalysisActor;
import orchestrator.analysis.MLInferenceClient;
import orchestrator.ingest.NatsIngestActor;
import orchestrator.risk.RiskAssessmentActor;

public class OrchestratorGuardian extends AbstractBehavior<Void> {

    public static Behavior<Void> create(String natsUrl) {
        return Behaviors.setup(ctx -> new OrchestratorGuardian(ctx, natsUrl));
    }

    private OrchestratorGuardian(
            ActorContext<Void> context,
            String natsUrl
    ) {
        super(context);

        // create client for communication with ML model
        MLInferenceClient mlClient = new MLInferenceClient("http://ml-ec2:8080/infer");

        ActorRef<AlertPublisherActor.Command> alertPublisher =
                context.spawn(AlertPublisherActor.create(natsUrl), "alertPublisher");

        ActorRef<RiskAssessmentActor.Command> riskAssessment =
                context.spawn(RiskAssessmentActor.create(alertPublisher), "riskAssessment");

        ActorRef<FireAnalysisActor.Command> fireAnalysis =
                context.spawn(FireAnalysisActor.create(riskAssessment, mlClient), "fireAnalysis");

        context.spawn(
                NatsIngestActor.create(natsUrl, fireAnalysis),
                "natsIngest"
        );
    }

    @Override
    public Receive<Void> createReceive() {
        return newReceiveBuilder().build();
    }
}
