const SSE_URL =
  process.env.NEXT_PUBLIC_SSE_URL ?? "http://localhost:8000/api/realtime/events/stream";

export type RealtimeEvent = {
  event: string;
  data: string;
};

export function createRealtimeClient(onEvent: (event: RealtimeEvent) => void): () => void {
  const source = new EventSource(SSE_URL);

  source.onmessage = (message) => {
    onEvent({ event: message.type, data: message.data });
  };

  source.addEventListener("heartbeat", (message) => {
    onEvent({ event: "heartbeat", data: message.data });
  });

  return () => source.close();
}
