package orchestrator.model;

/*
* Result for the extern ML Analysis
*/
public record MLResult(
        boolean fire,
        double confidence
) {}