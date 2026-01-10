package orchestrator.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public record MLResult(
        @JsonProperty("predicted_class")
        String predictedClass,

        double confidence,

        Map<String, Double> probs
) {
    public double fireProbability() {
        return probs.getOrDefault("fire", 0.0);
    }
}
