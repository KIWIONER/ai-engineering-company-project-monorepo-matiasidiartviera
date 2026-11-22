'use client';

import React, { useState } from 'react';
import { CandidateStatus, CandidateStage } from '@/types/candidate';
import { patchCandidateStatusStage } from '@/services/trackerApi';
import Badge from '@/components/ui/Badge';

interface StatusStageControlsProps {
  candidateId: number | string;
  initialStatus: CandidateStatus;
  initialStage: CandidateStage;
  onUpdate?: (newStatus: CandidateStatus, newStage: CandidateStage) => void;
}

export default function StatusStageControls({
  candidateId,
  initialStatus,
  initialStage,
  onUpdate,
}: StatusStageControlsProps) {
  const [status, setStatus] = useState<CandidateStatus>(initialStatus);
  const [stage, setStage] = useState<CandidateStage>(initialStage);
  const [updating, setUpdating] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleStatusChange = async (newStatus: CandidateStatus) => {
    if (newStatus === status) return;
    setUpdating(true);
    setFeedback(null);
    try {
      await patchCandidateStatusStage(candidateId, { status: newStatus, stage });
      setStatus(newStatus);
      setFeedback({ type: 'success', message: 'Estado actualizado correctamente' });
      if (onUpdate) onUpdate(newStatus, stage);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar el estado.';
      setFeedback({ type: 'error', message: msg });
    } finally {
      setUpdating(false);
    }
  };

  const handleStageChange = async (newStage: CandidateStage) => {
    if (newStage === stage) return;
    setUpdating(true);
    setFeedback(null);
    try {
      await patchCandidateStatusStage(candidateId, { status, stage: newStage });
      setStage(newStage);
      setFeedback({ type: 'success', message: 'Etapa actualizada correctamente' });
      if (onUpdate) onUpdate(status, newStage);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al actualizar la etapa.';
      setFeedback({ type: 'error', message: msg });
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="bg-[#ddd9ce]/90 backdrop-blur-xl rounded-2xl border border-stone-500/50 p-6 shadow-xl mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-stone-400/70">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Control de Estado y Etapa (PATCH)
        </h3>
        {updating && (
          <div className="flex items-center text-xs font-semibold text-emerald-800">
            <div className="w-3.5 h-3.5 border-2 border-emerald-700 border-t-transparent rounded-full animate-spin mr-1.5" />
            Actualizando...
          </div>
        )}
      </div>

      {feedback && (
        <div
          className={`p-3 rounded-xl text-xs font-semibold mb-4 flex items-center justify-between ${
            feedback.type === 'success'
              ? 'bg-emerald-700/15 text-emerald-900 border border-emerald-700/35'
              : 'bg-rose-700/15 text-rose-900 border border-rose-700/35'
          }`}
        >
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="text-slate-700 hover:text-slate-950">
            &times;
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-5">
        {/* Cambiar Estado */}
        <div className="min-w-0">
          <label className="text-xs font-semibold text-slate-800 mb-2 flex flex-wrap items-center justify-between gap-2">
            <span>Estado Actual:</span>
            <Badge label={status} variant="status" size="sm" />
          </label>
          <select
            disabled={updating}
            value={status}
            onChange={(e) => handleStatusChange(e.target.value as CandidateStatus)}
            className="w-full bg-[#181f2c]/95 border border-stone-600/50 text-white text-xs rounded-xl p-3 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600 disabled:opacity-50"
          >
            <option value="PENDING">PENDIENTE (PENDING)</option>
            <option value="IN_REVIEW">EN REVISIÓN (IN_REVIEW)</option>
            <option value="ACCEPTED">ACEPTADO (ACCEPTED)</option>
            <option value="REJECTED">RECHAZADO (REJECTED)</option>
          </select>
        </div>

        {/* Cambiar Etapa */}
        <div className="min-w-0">
          <label className="text-xs font-semibold text-slate-800 mb-2 flex flex-wrap items-center justify-between gap-2">
            <span>Etapa Actual:</span>
            <Badge label={stage} variant="stage" size="sm" />
          </label>
          <select
            disabled={updating}
            value={stage}
            onChange={(e) => handleStageChange(e.target.value as CandidateStage)}
            className="w-full bg-[#181f2c]/95 border border-stone-600/50 text-white text-xs rounded-xl p-3 font-medium focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600 disabled:opacity-50"
          >
            <option value="SCREENING">CRIBA (SCREENING)</option>
            <option value="INTERVIEW">ENTREVISTA (INTERVIEW)</option>
            <option value="TECHNICAL_TEST">PRUEBA TÉCNICA (TECHNICAL_TEST)</option>
            <option value="OFFER">OFERTA (OFFER)</option>
            <option value="HIRED">CONTRATADO (HIRED)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
