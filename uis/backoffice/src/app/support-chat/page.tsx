"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import { useSupportChatWS } from "@/hooks/useSupportChatWs";
import styles from "./SupportChat.module.css";
import {
    AlertTriangle,
    ArrowLeft,
    Bot,
    History,
    PlusCircle,
    Radio,
    RefreshCw,
    Send,
    Square,
    Trash2,
    User,
    WifiOff,
} from "lucide-react";

interface SupportSessionSummary {
    session_id: string;
    agent_id: string;
    status: string;
    created_at: string;
    message_count: number;
    preview: string;
}

const SESSION_STORAGE_KEY = "nexova_support_session_id";

function generateSessionId(): string {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return `chat_${crypto.randomUUID().slice(0, 8)}`;
    }
    return `chat_${Math.random().toString(36).slice(2, 10)}`;
}

function renderFormattedContent(raw: string): React.ReactNode {
    const cleaned = raw
        .replace(/<external_data[^>]*>\s*/gi, "")
        .replace(/\s*<\/external_data>/gi, "");

    const parts = cleaned.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, idx) => {
        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
            return <strong key={idx}>{part.slice(2, -2)}</strong>;
        }
        return <React.Fragment key={idx}>{part}</React.Fragment>;
    });
}

export default function SupportChatPage() {
    const [sessionId, setSessionId] = useState<string>("");
    const [inputText, setInputText] = useState("");
    const [sessions, setSessions] = useState<SupportSessionSummary[]>([]);
    const [loadingSessions, setLoadingSessions] = useState(false);
    const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    const getAuthHeaders = useCallback((): HeadersInit => {
        const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
        return token ? { Authorization: `Bearer ${token}` } : {};
    }, []);

    const fetchSessions = useCallback(async () => {
        setLoadingSessions(true);
        try {
            const res = await fetch("/backend-api/agent/sessions", {
                headers: getAuthHeaders(),
            });
            if (res.status === 401) {
                window.location.href = "/login";
                return;
            }
            if (res.ok) {
                const data = await res.json();
                setSessions(Array.isArray(data.sessions) ? data.sessions : []);
            }
        } catch {
            // Silencioso: no bloquear el chat si falla la recarga de historial
        } finally {
            setLoadingSessions(false);
        }
    }, [getAuthHeaders]);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const fromUrl = params.get("session_id")?.trim();
        if (fromUrl) {
            localStorage.setItem(SESSION_STORAGE_KEY, fromUrl);
            setSessionId(fromUrl);
            return;
        }
        const stored = localStorage.getItem(SESSION_STORAGE_KEY);
        if (stored) {
            setSessionId(stored);
        } else {
            const fresh = generateSessionId();
            localStorage.setItem(SESSION_STORAGE_KEY, fresh);
            setSessionId(fresh);
        }
    }, []);

    const {
        messages,
        connectionStatus,
        reconnectAttempt,
        isGenerating,
        sendMessage,
        interruptGeneration,
    } = useSupportChatWS({
        sessionId,
        enabled: Boolean(sessionId),
    });

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (sessionId) {
            fetchSessions();
        }
    }, [sessionId, messages.length, fetchSessions]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() || connectionStatus !== "connected") return;
        sendMessage(inputText);
        setInputText("");
    };

    const handleNewSession = () => {
        const fresh = generateSessionId();
        localStorage.setItem(SESSION_STORAGE_KEY, fresh);
        setSessionId(fresh);
    };

    const handleSelectSession = (targetId: string) => {
        if (targetId === sessionId) return;
        localStorage.setItem(SESSION_STORAGE_KEY, targetId);
        setSessionId(targetId);
    };

    const handleDeleteSession = async (
        e: React.MouseEvent,
        targetId: string
    ) => {
        e.stopPropagation();
        setDeletingSessionId(targetId);
        try {
            const res = await fetch(`/backend-api/agent/sessions/${encodeURIComponent(targetId)}`, {
                method: "DELETE",
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const remaining = sessions.filter((s) => s.session_id !== targetId);
                setSessions(remaining);
                if (targetId === sessionId) {
                    const nextId = remaining[0]?.session_id || generateSessionId();
                    localStorage.setItem(SESSION_STORAGE_KEY, nextId);
                    setSessionId(nextId);
                }
            }
        } finally {
            setDeletingSessionId(null);
        }
    };

    return (
        <AuthGuard>
            <main className={styles.main}>
                {/* Cabecera */}
                <header
                    style={{
                        display: "flex",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "1rem",
                        marginBottom: "1rem",
                    }}
                >
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.35rem" }}>
                            <span
                                style={{
                                    fontSize: "0.75rem",
                                    fontWeight: 600,
                                    color: "#10b981",
                                    background: "rgba(16, 185, 129, 0.12)",
                                    border: "1px solid rgba(16, 185, 129, 0.3)",
                                    padding: "0.2rem 0.65rem",
                                    borderRadius: "999px",
                                }}
                            >
                                Agente: first_line_support
                            </span>
                            {sessionId && (
                                <code
                                    style={{
                                        fontSize: "0.75rem",
                                        color: "#94a3b8",
                                        background: "#181f2c",
                                        padding: "0.2rem 0.55rem",
                                        borderRadius: "0.35rem",
                                    }}
                                >
                                    {sessionId}
                                </code>
                            )}
                        </div>
                        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>
                            Chat de Soporte en Tiempo Real (WebSocket)
                        </h1>
                    </div>

                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.55rem", alignItems: "center" }}>
                        <span
                            data-testid="ws-status-indicator"
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem",
                                padding: "0.45rem 0.8rem",
                                borderRadius: "0.5rem",
                                fontSize: "0.8rem",
                                fontWeight: 600,
                                background:
                                    connectionStatus === "connected"
                                        ? "rgba(16, 185, 129, 0.14)"
                                        : connectionStatus === "disconnected"
                                            ? "rgba(239, 68, 68, 0.14)"
                                            : "rgba(245, 158, 11, 0.14)",
                                border:
                                    connectionStatus === "connected"
                                        ? "1px solid rgba(16, 185, 129, 0.4)"
                                        : connectionStatus === "disconnected"
                                            ? "1px solid rgba(239, 68, 68, 0.4)"
                                            : "1px solid rgba(245, 158, 11, 0.4)",
                                color:
                                    connectionStatus === "connected"
                                        ? "#34d399"
                                        : connectionStatus === "disconnected"
                                            ? "#f87171"
                                            : "#fbbf24",
                            }}
                        >
                            {connectionStatus === "disconnected" ? (
                                <WifiOff size={14} />
                            ) : (
                                <Radio size={14} />
                            )}
                            {connectionStatus === "connected" && "En vivo (WS)"}
                            {connectionStatus === "connecting" && "Conectando..."}
                            {connectionStatus === "reconnecting" &&
                                `Reconectando (#${reconnectAttempt})...`}
                            {connectionStatus === "disconnected" && "Desconectado"}
                        </span>

                        <button
                            type="button"
                            onClick={handleNewSession}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.35rem",
                                padding: "0.45rem 0.8rem",
                                borderRadius: "0.5rem",
                                background: "#181f2c",
                                border: "1px solid rgba(148, 163, 184, 0.25)",
                                color: "#e2e8f0",
                                fontSize: "0.8rem",
                                cursor: "pointer",
                            }}
                        >
                            <PlusCircle size={14} /> Nueva sesión
                        </button>

                        <Link
                            href="/rfps"
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.35rem",
                                padding: "0.45rem 0.8rem",
                                borderRadius: "0.5rem",
                                background: "#181f2c",
                                border: "1px solid rgba(148, 163, 184, 0.25)",
                                color: "#e2e8f0",
                                fontSize: "0.8rem",
                                textDecoration: "none",
                            }}
                        >
                            <ArrowLeft size={14} /> Volver a RFPs
                        </Link>
                    </div>
                </header>

                <div className={styles.layout}>
                    <div className={styles.chatColumn}>
                {/* Historial de mensajes */}
                <section
                    style={{
                        flex: 1,
                        minHeight: 0,
                        overflowY: "auto",
                        overflowX: "hidden",
                        background: "#121721",
                        border: "1px solid rgba(148, 163, 184, 0.2)",
                        borderRadius: "0.75rem",
                        padding: "1.25rem",
                        display: "flex",
                        flexDirection: "column",
                        gap: "1rem",
                        marginBottom: "1rem",
                    }}
                >
                    {messages.length === 0 ? (
                        <div style={{ margin: "auto", textAlign: "center", color: "#94a3b8" }}>
                            <Bot size={36} style={{ marginBottom: "0.5rem", opacity: 0.7 }} />
                            <p style={{ margin: 0, fontSize: "0.95rem" }}>
                                Escribe tu consulta para conversar en vivo con el agente de soporte de Nexova.
                            </p>
                            <p style={{ margin: "0.35rem 0 0", fontSize: "0.8rem", color: "#64748b" }}>
                                Puedes interrumpir y redirigir la respuesta en cualquier momento mientras escribe.
                            </p>
                        </div>
                    ) : (
                        messages.map((msg) => {
                            const isUser = msg.role === "user";
                            return (
                                <div
                                    key={msg.message_id}
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        alignItems: isUser ? "flex-end" : "flex-start",
                                    }}
                                >
                                    <div
                                        style={{
                                            maxWidth: "80%",
                                            padding: "0.85rem 1rem",
                                            borderRadius: "0.75rem",
                                            background: isUser
                                                ? "rgba(16, 185, 129, 0.16)"
                                                : "#181f2c",
                                            border:
                                                msg.status === "interrupted"
                                                    ? "1px solid rgba(245, 158, 11, 0.55)"
                                                    : isUser
                                                        ? "1px solid rgba(16, 185, 129, 0.4)"
                                                        : "1px solid rgba(148, 163, 184, 0.2)",
                                            color: "#f1f5f9",
                                            whiteSpace: "pre-wrap",
                                            overflowWrap: "anywhere",
                                            lineHeight: 1.5,
                                            fontSize: "0.92rem",
                                        }}
                                    >
                                        <div
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "0.45rem",
                                                marginBottom: "0.35rem",
                                                fontSize: "0.75rem",
                                                color: "#94a3b8",
                                                fontWeight: 600,
                                            }}
                                        >
                                            {isUser ? <User size={13} /> : <Bot size={13} color="#10b981" />}
                                            <span>{isUser ? "Tú" : "Soporte Nexova"}</span>
                                            {msg.status === "interrupted" && (
                                                <span
                                                    style={{
                                                        display: "inline-flex",
                                                        alignItems: "center",
                                                        gap: "0.25rem",
                                                        color: "#fbbf24",
                                                        background: "rgba(245, 158, 11, 0.15)",
                                                        padding: "0.1rem 0.45rem",
                                                        borderRadius: "999px",
                                                        fontSize: "0.7rem",
                                                    }}
                                                >
                                                    <AlertTriangle size={11} /> Interrumpido
                                                </span>
                                            )}
                                        </div>
                                        <div>
                                            {msg.content
                                                ? renderFormattedContent(msg.content)
                                                : msg.status === "interrupted"
                                                    ? "(Generación interrumpida antes de emitir tokens)"
                                                    : ""}
                                            {msg.status === "streaming" && (
                                                <span style={{ color: "#10b981", marginLeft: "2px" }}>
                                                    ▌
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                    <div ref={bottomRef} />
                </section>

                {/* Input y control de interrupción */}
                <form
                    onSubmit={handleSubmit}
                    style={{
                        display: "flex",
                        gap: "0.65rem",
                        alignItems: "center",
                    }}
                >
                    <input
                        type="text"
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder={
                            isGenerating
                                ? "Escribe para interrumpir y redirigir al agente..."
                                : "Escribe tu consulta de soporte..."
                        }
                        style={{
                            flex: 1,
                            padding: "0.8rem 1rem",
                            borderRadius: "0.6rem",
                            background: "#121721",
                            border: "1px solid rgba(148, 163, 184, 0.3)",
                            color: "#f1f5f9",
                            fontSize: "0.95rem",
                            outline: "none",
                        }}
                    />

                    {isGenerating && (
                        <button
                            type="button"
                            onClick={() => interruptGeneration()}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem",
                                padding: "0.8rem 1rem",
                                borderRadius: "0.6rem",
                                background: "rgba(239, 68, 68, 0.18)",
                                border: "1px solid rgba(239, 68, 68, 0.5)",
                                color: "#fca5a5",
                                fontWeight: 600,
                                fontSize: "0.85rem",
                                cursor: "pointer",
                            }}
                        >
                            <Square size={14} /> Detener
                        </button>
                    )}

                    <button
                        type="submit"
                        disabled={!inputText.trim() || connectionStatus !== "connected"}
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.4rem",
                            padding: "0.8rem 1.2rem",
                            borderRadius: "0.6rem",
                            background:
                                !inputText.trim() || connectionStatus !== "connected"
                                    ? "#334155"
                                    : isGenerating
                                        ? "#f59e0b"
                                        : "#10b981",
                            border: "none",
                            color: "#06281e",
                            fontWeight: 700,
                            fontSize: "0.9rem",
                            cursor:
                                !inputText.trim() || connectionStatus !== "connected"
                                    ? "not-allowed"
                                    : "pointer",
                        }}
                    >
                        <Send size={15} />
                        {isGenerating ? "Interrumpir y Redirigir" : "Enviar"}
                    </button>
                </form>
                    </div>

                    {/* Lateral derecho: Historial de sesiones */}
                    <aside className={styles.sessionsCard} aria-label="Historial de sesiones de soporte">
                        <div className={styles.sessionsHeader}>
                            <h2 className={styles.sessionsTitle}>
                                <History size={15} color="#34d399" />
                                Sesiones
                                <span className={styles.sessionsCount}>{sessions.length}</span>
                            </h2>
                            <button
                                type="button"
                                onClick={fetchSessions}
                                disabled={loadingSessions}
                                className={styles.refreshBtn}
                                title="Actualizar sesiones"
                                aria-label="Actualizar sesiones"
                            >
                                <RefreshCw size={14} />
                            </button>
                        </div>

                        <div className={styles.sessionsList}>
                            {sessions.length === 0 ? (
                                <p className={styles.emptyState}>
                                    {loadingSessions
                                        ? "Cargando sesiones..."
                                        : "Aún no hay sesiones registradas."}
                                </p>
                            ) : (
                                sessions.map((item) => {
                                    const isActive = item.session_id === sessionId;
                                    const dateLabel = new Date(item.created_at).toLocaleString("es-ES", {
                                        day: "2-digit",
                                        month: "2-digit",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    });
                                    return (
                                        <div
                                            key={item.session_id}
                                            role="button"
                                            tabIndex={0}
                                            onClick={() => handleSelectSession(item.session_id)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter" || e.key === " ") {
                                                    e.preventDefault();
                                                    handleSelectSession(item.session_id);
                                                }
                                            }}
                                            className={`${styles.sessionItem} ${
                                                isActive ? styles.sessionItemActive : ""
                                            }`}
                                        >
                                            <div className={styles.sessionInfo}>
                                                <p className={styles.sessionPreview}>{item.preview}</p>
                                                <div className={styles.sessionMeta}>
                                                    <span className={styles.sessionCode}>{item.session_id}</span>
                                                    <span>{item.message_count} msgs</span>
                                                    <span>{dateLabel}</span>
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={(e) => handleDeleteSession(e, item.session_id)}
                                                disabled={deletingSessionId === item.session_id}
                                                className={styles.deleteBtn}
                                                title="Eliminar sesión"
                                                aria-label={`Eliminar sesión ${item.session_id}`}
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </aside>
                </div>
            </main>
        </AuthGuard>
    );
}