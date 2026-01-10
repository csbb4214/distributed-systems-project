package orchestrator.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public record MLResult(
        @JsonProperty("predicted_class")
        String predictedClass,

        double confidence,

        Map<String, Double> probs
) {
    public boolean isFire() {
        return "fire".equalsIgnoreCase(predictedClass);
    }

    public boolean isSmoke() {
        return "smoke".equalsIgnoreCase(predictedClass);
    }

    public double fireProbability() {
        return probs.getOrDefault("fire", 0.0);
    }
}
