"use client";
import { useEffect, useRef, useState, useCallback } from "react";

export type WsMessage =
  | { type: "snapshot"; seller_id: number; timestamp: string; data: Record<string, unknown> }
  | { type: "update"; seller_id: number; timestamp: string; data: Record<string, unknown> }
  | { type: "anomaly_alert"; seller_id: number; timestamp: string; data: Record<string, unknown> }
  | { type: "ping"; timestamp: string; connections: number }
  | { type: "pong"; timestamp: string };

type Status = "connecting" | "connected" | "disconnected" | "error";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useMetricsSocket(sellerId: number) {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [status, setStatus] = useState<Status>("disconnected");
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);

  const connect = useCallback(() => {
    if (!mounted.current) return;
    setStatus("connecting");

    const socket = new WebSocket(`${WS_BASE}/ws/metrics/${sellerId}`);
    ws.current = socket;

    socket.onopen = () => {
      if (!mounted.current) return;
      setStatus("connected");
    };

    socket.onmessage = (event) => {
      if (!mounted.current) return;
      try {
        const msg: WsMessage = JSON.parse(event.data);
        setLastMessage(msg);
        if (msg.type === "snapshot" || msg.type === "update") {
          setSnapshot(msg.data);
        }
        if (msg.type === "ping") {
          // Pong gönder
          socket.send(JSON.stringify({ type: "pong" }));
        }
      } catch {
        // malformed JSON — yoksay
      }
    };

    socket.onerror = () => {
      if (!mounted.current) return;
      setStatus("error");
    };

    socket.onclose = () => {
      if (!mounted.current) return;
      setStatus("disconnected");
      // 5 saniye sonra yeniden bağlan
      reconnectTimer.current = setTimeout(() => {
        if (mounted.current) connect();
      }, 5000);
    };
  }, [sellerId]);

  useEffect(() => {
    mounted.current = true;
    connect();
    return () => {
      mounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const requestRefresh = useCallback(() => {
    ws.current?.send(JSON.stringify({ type: "refresh" }));
  }, []);

  return { lastMessage, status, snapshot, requestRefresh };
}
