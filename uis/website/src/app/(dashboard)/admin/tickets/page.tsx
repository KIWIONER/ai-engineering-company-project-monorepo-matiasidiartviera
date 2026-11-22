'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import api from '@/lib/axios';
import axios from 'axios';

type IncidentStatus = 'open' | 'in_progress' | 'resolved' | 'discarded';

interface ResolutionNote {
  id: string;
  author: string;
  content: string;
  created_at: string;
}

interface IncidentItem {
  id: string;
  title: string;
  description: string;
  category: string;
  status: IncidentStatus;
  origin: string;
  branch: string;
  assigned_to?: string | null;
  resolution_notes?: ResolutionNote[];
  created_at: string;
  updated_at?: string;
}

const ASSIGNABLE_AGENTS = [
  'Roberto Diaz (Soporte)',
  'Laura Mendoza (IT)',
  'Javier Almeida (Selección)',
  'Tom Callahan (Facturación)',
];

const PAGE_SIZE = 10;

const STATUS_LABELS: Record<IncidentStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  discarded: 'Discarded',
};

function statusBadgeClasses(status: IncidentStatus): string {
  switch (status) {
    case 'open':
      return 'bg-amber-400/15 text-amber-200 border-amber-300/40';
    case 'in_progress':
      return 'bg-sky-500/15 text-sky-300 border-sky-400/40';
    case 'resolved':
      return 'bg-emerald-500/15 text-emerald-300 border-emerald-400/40';
    case 'discarded':
      return 'bg-slate-500/15 text-slate-300 border-slate-500/40';
  }
}

export default function TicketsAdminPage() {
  const { token, isAuthenticated } = useAuth();
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [actionError, setActionError] = useState('');
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [activeTicket, setActiveTicket] = useState<IncidentItem | null>(null);
  const [noteInput, setNoteInput] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'active' | 'all' | IncidentStatus>('active');
  const [currentPage, setCurrentPage] = useState(1);
  const listTopRef = useRef<HTMLDivElement | null>(null);

  const fetchIncidents = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await api.get<IncidentItem[]>('/api/incidents');
      const sorted = [...(res.data || [])].sort((a, b) => {
        const da = new Date(a.created_at || 0).getTime();
        const db = new Date(b.created_at || 0).getTime();
        return db - da;
      });
      setIncidents(sorted);
    } catch {
      setErrorMsg('No se pudieron cargar las incidencias reales desde el backend.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (isAuthenticated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchIncidents();
    }
  }, [isAuthenticated, fetchIncidents]);

  const openCount = incidents.filter((i) => i.status === 'open').length;
  const inProgressCount = incidents.filter((i) => i.status === 'in_progress').length;
  const resolvedCount = incidents.filter((i) => i.status === 'resolved').length;

  const filteredIncidents = useMemo(() => {
    return incidents.filter((inc) => {
      if (statusFilter === 'all') return true;
      if (statusFilter === 'active') return inc.status === 'open' || inc.status === 'in_progress';
      return inc.status === statusFilter;
    });
  }, [incidents, statusFilter]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentPage(1);
  }, [statusFilter]);

  const handleTransition = async (id: string, nextStatus: IncidentStatus) => {
    setActionError('');
    setUpdatingId(id);
    try {
      const res = await api.patch<IncidentItem>(`/api/incidents/${id}/status`, {
        status: nextStatus,
      });
      const updated = res.data;
      setIncidents((prev) => prev.map((item) => (item.id === id ? updated : item)));
      setActiveTicket((prev) => (prev && prev.id === id ? updated : prev));
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setActionError(String(err.response.data.detail));
      } else {
        setActionError('Error al actualizar el estado del ticket en el servidor.');
      }
    } finally {
      setUpdatingId(null);
    }
  };

  const handleAssign = async (id: string, assignedTo: string) => {
    setActionError('');
    setUpdatingId(id);
    try {
      const res = await api.patch<IncidentItem>(`/api/incidents/${id}/assign`, {
        assigned_to: assignedTo || null,
      });
      const updated = res.data;
      setIncidents((prev) => prev.map((item) => (item.id === id ? updated : item)));
      setActiveTicket((prev) => (prev && prev.id === id ? updated : prev));
    } catch {
      setActionError('Error al asignar el responsable del ticket.');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTicket || !noteInput.trim()) return;
    setActionError('');
    setSavingNote(true);
    try {
      const res = await api.post<IncidentItem>(`/api/incidents/${activeTicket.id}/notes`, {
        content: noteInput.trim(),
      });
      const updated = res.data;
      setIncidents((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setActiveTicket(updated);
      setNoteInput('');
    } catch {
      setActionError('Error al guardar la nota de resolución.');
    } finally {
      setSavingNote(false);
    }
  };

  const totalItems = filteredIncidents.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const startIdx = (safePage - 1) * PAGE_SIZE;
  const paginated = filteredIncidents.slice(startIdx, startIdx + PAGE_SIZE);
  const rangeStart = totalItems === 0 ? 0 : startIdx + 1;
  const rangeEnd = Math.min(startIdx + PAGE_SIZE, totalItems);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    listTopRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="text-slate-100 antialiased pb-16">
      <header className="rounded-2xl border border-emerald-500/25 bg-[#121721]/85 p-6 mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-emerald-400 font-semibold">
            Nexova / Escalado IT · Conectado a /api/incidents
          </p>
          <h1 className="mt-1 text-2xl font-bold text-white">
            Panel de Agentes — Tickets Escalados
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2.5 text-xs font-semibold">
          <a
            href={`${process.env.NEXT_PUBLIC_BACKOFFICE_URL || 'http://localhost:3001'}/support-chat`}
            className="rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-4 py-2 text-emerald-300 hover:bg-emerald-400 hover:text-[#0a0d12] transition"
          >
            Chatbot Soporte IA
          </a>
          <Link
            href="/incidents"
            className="rounded-xl border border-emerald-500/20 bg-[#0a0d12]/60 px-4 py-2 text-slate-300 hover:text-white transition"
          >
            Ver Incidencias
          </Link>
        </div>
      </header>

      {/* Métricas reales */}
      <section className="grid gap-4 sm:grid-cols-3">
        <article className="rounded-2xl border border-emerald-500/20 bg-[#121721]/75 p-5 shadow-lg">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Abiertos (Open)
          </h2>
          <p className="mt-2 text-3xl font-extrabold text-amber-300">{openCount}</p>
        </article>
        <article className="rounded-2xl border border-emerald-500/20 bg-[#121721]/75 p-5 shadow-lg">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            En Progreso
          </h2>
          <p className="mt-2 text-3xl font-extrabold text-sky-300">{inProgressCount}</p>
        </article>
        <article className="rounded-2xl border border-emerald-500/20 bg-[#121721]/75 p-5 shadow-lg">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Resueltos
          </h2>
          <p className="mt-2 text-3xl font-extrabold text-emerald-400">{resolvedCount}</p>
        </article>
      </section>

      {/* Listado real */}
      <section
        ref={listTopRef}
        className="mt-6 scroll-mt-4 rounded-2xl border border-emerald-500/20 bg-[#121721]/80 p-5 shadow-xl sm:p-6"
      >
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Cola de Tickets en Seguimiento</h2>
            <p className="text-xs font-mono text-emerald-400 mt-1">
              Mostrando {rangeStart}–{rangeEnd} de {totalItems} tickets · Página {safePage} de {totalPages}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="ticket-status-filter" className="text-xs font-medium text-slate-400">
              Vista:
            </label>
            <select
              id="ticket-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
              className="rounded-xl border border-emerald-500/25 bg-[#0a0d12] px-3 py-1.5 text-xs font-semibold text-slate-200 focus:border-emerald-400 focus:outline-none"
            >
              <option value="active">Activos (Open / In Progress)</option>
              <option value="open">Solo Open</option>
              <option value="in_progress">Solo In Progress</option>
              <option value="resolved">Solo Resueltos</option>
              <option value="discarded">Solo Descartados</option>
              <option value="all">Todos</option>
            </select>
          </div>
        </header>

        {errorMsg ? (
          <div className="mt-5 rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={fetchIncidents} className="underline font-bold">
              Reintentar
            </button>
          </div>
        ) : loading ? (
          <div className="py-12 text-center text-xs font-mono text-slate-400">
            Cargando tickets desde /api/incidents...
          </div>
        ) : paginated.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-400">
            No hay tickets en esta vista.
          </div>
        ) : (
          <>
            <div className="mt-6 flex flex-col gap-3">
              {paginated.map((ticket) => (
                <article
                  key={ticket.id}
                  onClick={() => {
                    setActionError('');
                    setActiveTicket(ticket);
                  }}
                  className="cursor-pointer rounded-xl border border-emerald-500/15 bg-[#181f2c]/80 p-4 hover:border-emerald-400/45 transition-colors"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="sm:w-1/3 min-w-0">
                      <p className="text-[11px] font-mono font-bold text-emerald-400 truncate">
                        {ticket.id}
                      </p>
                      <h3 className="text-sm font-bold text-white leading-snug mt-0.5 truncate">
                        {ticket.title}
                      </h3>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {ticket.category} · {ticket.branch} · {ticket.origin}
                      </p>
                    </div>

                    <div className="flex-1 text-xs text-slate-300 line-clamp-2 min-w-0">
                      {ticket.description}
                    </div>

                    <div
                      className="sm:w-48 shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <select
                        aria-label={`Asignar ticket ${ticket.title}`}
                        value={ticket.assigned_to || ''}
                        disabled={updatingId === ticket.id}
                        onChange={(e) => handleAssign(ticket.id, e.target.value)}
                        className="w-full rounded-xl border border-emerald-500/25 bg-[#0a0d12] px-2.5 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                      >
                        <option value="">Sin asignar</option>
                        {ASSIGNABLE_AGENTS.map((agent) => (
                          <option key={agent} value={agent}>
                            {agent}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
                      <span className="text-xs font-mono text-slate-400 whitespace-nowrap">
                        {new Date(ticket.created_at).toLocaleDateString('es-ES')}
                      </span>
                      <span
                        className={`inline-flex min-w-[96px] justify-center rounded-full border px-3 py-1 text-xs font-semibold ${statusBadgeClasses(
                          ticket.status
                        )}`}
                      >
                        {STATUS_LABELS[ticket.status] || ticket.status}
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {totalPages > 1 && (
              <nav
                aria-label="Paginación de tickets"
                className="mt-6 flex flex-wrap items-center justify-center gap-2"
              >
                <button
                  type="button"
                  onClick={() => goToPage(safePage - 1)}
                  disabled={safePage === 1}
                  className="rounded-xl border border-emerald-500/25 bg-[#0a0d12] px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/60 hover:text-emerald-300 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  &larr; Anterior
                </button>
                {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((pageNum) => {
                  const isCurrent = pageNum === safePage;
                  return (
                    <button
                      key={pageNum}
                      type="button"
                      onClick={() => goToPage(pageNum)}
                      aria-current={isCurrent ? 'page' : undefined}
                      className={`min-w-[36px] rounded-xl px-3 py-2 text-xs font-mono font-bold transition ${
                        isCurrent
                          ? 'border border-emerald-400 bg-emerald-400 text-[#0a0d12]'
                          : 'border border-slate-700/70 bg-[#0a0d12] text-slate-300 hover:border-emerald-400/50 hover:text-emerald-300'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  type="button"
                  onClick={() => goToPage(safePage + 1)}
                  disabled={safePage === totalPages}
                  className="rounded-xl border border-emerald-500/25 bg-[#0a0d12] px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/60 hover:text-emerald-300 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Siguiente &rarr;
                </button>
              </nav>
            )}
          </>
        )}
      </section>

      {/* Modal Detalle y Resolución Real */}
      {activeTicket && (
        <section className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm p-4 sm:p-6 flex items-center justify-center">
          <article className="w-full max-h-[90vh] max-w-2xl overflow-y-auto rounded-2xl border border-emerald-500/30 bg-[#121721] p-6 shadow-2xl">
            <header className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  Resolución de Ticket IT
                </p>
                <h2 className="mt-1 text-lg font-bold text-white">{activeTicket.title}</h2>
                <p className="mt-0.5 text-xs font-mono text-slate-400 break-all">
                  ID: {activeTicket.id}
                </p>
              </div>
              <button
                onClick={() => setActiveTicket(null)}
                className="rounded-xl border border-emerald-500/30 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-emerald-500/15 shrink-0"
              >
                Cerrar
              </button>
            </header>

            <section className="mt-5 grid gap-4 rounded-xl border border-emerald-500/20 bg-[#0a0d12]/80 p-4 sm:grid-cols-2 lg:grid-cols-4 text-xs">
              <div>
                <h3 className="font-semibold uppercase tracking-wide text-slate-400">Categoría / Sede</h3>
                <p className="mt-1 font-bold text-white">
                  {activeTicket.category} · {activeTicket.branch}
                </p>
              </div>
              <div>
                <h3 className="font-semibold uppercase tracking-wide text-slate-400">Origen</h3>
                <p className="mt-1 font-bold text-white">{activeTicket.origin}</p>
              </div>
              <div>
                <h3 className="font-semibold uppercase tracking-wide text-slate-400">Estado Actual</h3>
                <span
                  className={`mt-1 inline-flex rounded-full border px-3 py-0.5 font-semibold ${statusBadgeClasses(
                    activeTicket.status
                  )}`}
                >
                  {STATUS_LABELS[activeTicket.status] || activeTicket.status}
                </span>
              </div>
              <div>
                <h3 className="font-semibold uppercase tracking-wide text-slate-400">Asignado a</h3>
                <select
                  aria-label="Asignar responsable en modal"
                  value={activeTicket.assigned_to || ''}
                  disabled={updatingId === activeTicket.id}
                  onChange={(e) => handleAssign(activeTicket.id, e.target.value)}
                  className="mt-1 w-full rounded-lg border border-emerald-500/25 bg-[#121721] px-2.5 py-1 text-xs font-medium text-slate-200 focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                >
                  <option value="">Sin asignar</option>
                  {ASSIGNABLE_AGENTS.map((agent) => (
                    <option key={agent} value={agent}>
                      {agent}
                    </option>
                  ))}
                </select>
              </div>
            </section>

            <section className="mt-5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                Descripción del Problema
              </h3>
              <p className="mt-2 rounded-xl border border-emerald-500/15 bg-[#0a0d12]/80 p-3.5 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                {activeTicket.description}
              </p>
            </section>

            {/* Bitácora / Notas de Resolución */}
            <section className="mt-5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                Bitácora de Resolución ({activeTicket.resolution_notes?.length || 0})
              </h3>

              <form onSubmit={handleAddNote} className="mt-2 flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  disabled={savingNote}
                  placeholder="Añade acciones tomadas o diagnóstico de resolución..."
                  className="flex-1 rounded-xl border border-emerald-500/25 bg-[#0a0d12] px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-emerald-400 focus:outline-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={savingNote || !noteInput.trim()}
                  className="rounded-xl bg-emerald-500/20 border border-emerald-400/40 px-4 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-400 hover:text-[#0a0d12] transition disabled:opacity-40"
                >
                  {savingNote ? 'Guardando...' : '+ Guardar Nota'}
                </button>
              </form>

              <div className="mt-3 max-h-44 overflow-y-auto space-y-2">
                {!activeTicket.resolution_notes || activeTicket.resolution_notes.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">
                    Aún no hay notas de resolución registradas para este ticket.
                  </p>
                ) : (
                  activeTicket.resolution_notes.map((note) => (
                    <div
                      key={note.id}
                      className="rounded-xl border border-emerald-500/15 bg-[#0a0d12]/80 p-3 text-xs"
                    >
                      <div className="flex items-center justify-between gap-2 text-[11px] text-emerald-300/80 mb-1">
                        <span className="font-semibold">{note.author}</span>
                        <span className="font-mono text-slate-500">
                          {new Date(note.created_at).toLocaleString('es-ES')}
                        </span>
                      </div>
                      <p className="text-slate-200 whitespace-pre-wrap">{note.content}</p>
                    </div>
                  ))
                )}
              </div>
            </section>

            {actionError && (
              <div className="mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300">
                {actionError}
              </div>
            )}

            <section className="mt-5 rounded-xl border border-emerald-500/20 bg-[#0a0d12]/60 p-4">
              {activeTicket.status === 'open' && (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs text-slate-300">
                    Para resolver un ticket abierto, primero tómalo <strong>En Progreso</strong> o descártalo.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={updatingId === activeTicket.id}
                      onClick={() => handleTransition(activeTicket.id, 'in_progress')}
                      className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-bold text-[#0a0d12] hover:bg-emerald-300 transition disabled:opacity-50"
                    >
                      Iniciar Atención (In Progress)
                    </button>
                    <button
                      type="button"
                      disabled={updatingId === activeTicket.id}
                      onClick={() => handleTransition(activeTicket.id, 'discarded')}
                      className="rounded-xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 text-xs font-bold text-rose-200 hover:bg-rose-500/25 transition disabled:opacity-50"
                    >
                      Descartar
                    </button>
                  </div>
                </div>
              )}

              {activeTicket.status === 'in_progress' && (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs text-slate-300">
                    Ticket en atención activa. Puedes marcarlo como resuelto o descartarlo.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={updatingId === activeTicket.id}
                      onClick={() => handleTransition(activeTicket.id, 'resolved')}
                      className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-bold text-[#0a0d12] hover:bg-emerald-300 transition disabled:opacity-50"
                    >
                      Marcar como Resuelto
                    </button>
                    <button
                      type="button"
                      disabled={updatingId === activeTicket.id}
                      onClick={() => handleTransition(activeTicket.id, 'discarded')}
                      className="rounded-xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 text-xs font-bold text-rose-200 hover:bg-rose-500/25 transition disabled:opacity-50"
                    >
                      Descartar
                    </button>
                  </div>
                </div>
              )}

              {(activeTicket.status === 'resolved' || activeTicket.status === 'discarded') && (
                <p className="text-xs text-emerald-300 text-center font-semibold">
                  Ticket cerrado ({STATUS_LABELS[activeTicket.status]}). No admite más transiciones.
                </p>
              )}
            </section>
          </article>
        </section>
      )}
    </div>
  );
}
