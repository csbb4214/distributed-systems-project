package orchestrator;

import akka.actor.typed.ActorSystem;

public class Main {
    public static void main(String[] args) {
        // get NATS_URL -> fall back to localhost if not set
        String natsUrl = System.getenv().getOrDefault(
                "NATS_URL", "nats://localhost:4222"
        );

        // create OrchestratorGuardian
        ActorSystem.create(OrchestratorGuardian.create(natsUrl), "CloudOrchestrator");
    }
}
