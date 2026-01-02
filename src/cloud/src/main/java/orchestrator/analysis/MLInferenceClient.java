package orchestrator.analysis;

import com.fasterxml.jackson.databind.ObjectMapper;
import orchestrator.model.MLResult;

import java.net.http.*;
import java.net.URI;
import java.util.Map;

public class MLInferenceClient {

    private static final ObjectMapper mapper = new ObjectMapper();
    private final HttpClient client = HttpClient.newHttpClient();
    private final String endpoint;

    public MLInferenceClient(String endpoint) {
        this.endpoint = endpoint;
    }

    public MLResult infer(String frameB64) throws Exception {
        String body = mapper.writeValueAsString(
                Map.of("frame", frameB64)
        );

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(endpoint + "/infer"))
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .header("Content-Type", "application/json")
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        return mapper.readValue(response.body(), MLResult.class);
    }
}
