package orchestrator;

import akka.actor.typed.ActorSystem;

public class Main {
    public static void main(String[] args) {
        String natsUrl = System.getenv().getOrDefault(
                "NATS_URL", "nats://localhost:4222"
        );

        ActorSystem.create(
                OrchestratorGuardian.create(natsUrl),
                "CloudOrchestrator"
        );
    }
}
