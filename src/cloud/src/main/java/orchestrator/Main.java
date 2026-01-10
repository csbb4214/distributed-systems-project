package orchestrator;

import akka.actor.typed.ActorSystem;

public class Main {
    public static void main(String[] args) {
        // get NATS_URL and ML_URL -> fall back to localhost if not set
        String natsUrl = System.getenv().getOrDefault(
                "NATS_URL", "nats://98.84.116.31:4222"
        );
        String mlUrl = System.getenv().getOrDefault(
                "ML_URL", "http://107.20.119.21:8000"
        );

        // launch OrchestratorGuardian
        ActorSystem.create(OrchestratorGuardian.create(natsUrl, mlUrl), "CloudOrchestrator");
    }
}
