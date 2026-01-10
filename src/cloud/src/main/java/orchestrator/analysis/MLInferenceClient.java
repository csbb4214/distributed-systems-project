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
                Map.of("frame_jpeg_b64", frameB64)
        );

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(endpoint + "/infer"))
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .header("Content-Type", "application/json")
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("ML server error: " + response.body());
        }

        return mapper.readValue(response.body(), MLResult.class);
    }
}
