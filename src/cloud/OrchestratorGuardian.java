import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;

public class OrchestratorGuardian extends AbstractBehavior<Void> {

    public static Behavior<Void> create(String natsUrl) {
        return Behaviors.setup(ctx -> new OrchestratorGuardian(ctx, natsUrl));
    }

    private OrchestratorGuardian(
            ActorContext<Void> context,
            String natsUrl
    ) {
        super(context);

        ActorRef<AlertPublisherActor.Command> alertPublisher =
                context.spawn(AlertPublisherActor.create(natsUrl), "alertPublisher");

        ActorRef<RiskAssessmentActor.Command> riskAssessment =
                context.spawn(RiskAssessmentActor.create(alertPublisher), "riskAssessment");

        ActorRef<FireAnalysisActor.Command> fireAnalysis =
                context.spawn(FireAnalysisActor.create(riskAssessment), "fireAnalysis");

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
