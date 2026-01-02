import java.util.concurrent.CompletableFuture;

private Behavior<Command> onAnalyze(Analyze msg) {
    CompletableFuture
            .supplyAsync(() -> {
                try {
                    return mlClient.infer(msg.event.frame_jpeg_b64);
                } catch (Exception e) {
                    return null;
                }
            })
            .thenAccept(result -> {
                if (result != null && result.fire) {
                    getContext().getSelf().tell(
                            new MLConfirmed(msg.event, result.confidence)
                    );
                }
            });
    return this;
}

private record MLConfirmed(
        CloudEvent event,
        double confidence
) implements Command {}