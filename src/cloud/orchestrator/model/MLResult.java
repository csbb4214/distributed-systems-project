package orchestrator.model;

public record MLResult(
        boolean fire,
        double confidence
) {}