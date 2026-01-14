package orchestrator.model;

import java.util.Map;

public record Trace(
        String trace_id,
        Map<String, Long> timestamps
) {}
