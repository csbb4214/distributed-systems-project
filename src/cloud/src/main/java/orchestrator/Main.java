package orchestrator;

import akka.actor.typed.ActorSystem;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Map;

public class Main {
    public static void main(String[] args) {
        // get NATS_URL and ML_URL -> fall back to localhost if not set
        String natsUrl = System.getenv().getOrDefault(
                "NATS_URL", "nats://98.95.255.36:4222"
        );
        String mlUrl = System.getenv().getOrDefault(
                "ML_URL", "http://34.233.208.20:8000"
        );

        // Parse AREA_COORDS from environment variable (as json)
        Map<String, double[]> areaCoords = parseAreaCoords();

        // launch OrchestratorGuardian
        ActorSystem.create(OrchestratorGuardian.create(natsUrl, mlUrl, areaCoords), "CloudOrchestrator");
    }

    private static Map<String, double[]> parseAreaCoords() {
        String areaCoordsJson = System.getenv("AREA_COORDS");

        // Default fallback
        Map<String, double[]> defaultCoords = Map.of(
                "areaA1", new double[]{0, 0},
                "areaB1", new double[]{3, 2}
        );

        if (areaCoordsJson == null || areaCoordsJson.isEmpty()) {
            System.out.println("AREA_COORDS not set, using defaults");
            return defaultCoords;
        }

        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.readValue(
                    areaCoordsJson,
                    new TypeReference<>() {}
            );
        } catch (Exception e) {
            // cannot use akka context logging here because there is none yet
            System.err.println("Failed to parse AREA_COORDS: " + e.getMessage());
            System.err.println("Using default coordinates");
            return defaultCoords;
        }
    }
}
