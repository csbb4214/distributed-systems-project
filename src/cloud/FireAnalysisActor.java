import akka.actor.typed.*;
import akka.actor.typed.javadsl.*;

public class FireAnalysisActor extends AbstractBehavior<FireAnalysisActor.Command> {

    public interface Command {}

    public static class Analyze implements Command {
        public final CloudEvent event;
        public Analyze(CloudEvent event) {
            this.event = event;
        }
    }

    public static Behavior<Command> create(
            ActorRef<RiskAssessmentActor.Command> riskAssessment
    ) {
        return Behaviors.setup(ctx ->
                new FireAnalysisActor(ctx, riskAssessment)
        );
    }

    private final ActorRef<RiskAssessmentActor.Command> riskAssessment;

    private FireAnalysisActor(
            ActorContext<Command> context,
            ActorRef<RiskAssessmentActor.Command> riskAssessment
    ) {
        super(context);
        this.riskAssessment = riskAssessment;
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
                .onMessage(Analyze.class, this::onAnalyze)
                .build();
    }

    private Behavior<Command> onAnalyze(Analyze msg) {
        boolean confirmed = msg.event.conf_fire > 0.05;

        if (confirmed) {
            getContext().getLog().info(
                    "Fire confirmed in {}", msg.event.area
            );
            riskAssessment.tell(
                    new RiskAssessmentActor.Assess(msg.event)
            );
        }

        return this;
    }
}
