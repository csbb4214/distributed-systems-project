package orchestrator.model;

/*
* Result-datastructure for the extern ML Analysis
*/
public record MLResult(
        boolean fire,
        double confidence
) {}