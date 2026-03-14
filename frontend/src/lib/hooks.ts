"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { StudySummary, LungRADSReport, InferenceStatus } from "./types";
import * as api from "./api";

/* ── useStudies: fetch study list from backend ── */
export function useStudies(params?: {
  modality?: string;
  status?: string;
  limit?: number;
}) {
  const [studies, setStudies] = useState<StudySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStudies(params);
      setStudies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Veri yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [params?.modality, params?.status, params?.limit]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { studies, loading, error, refetch: fetch };
}

/* ── useInference: start pipeline + poll status ── */
export function useInference() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [progress, setProgress] = useState<InferenceStatus["progress"] | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const start = useCallback(
    async (studyId: string, pipeline: "cxr" | "ct") => {
      stopPolling();
      setError(null);
      setProgress(null);
      setStatus("starting");

      try {
        const res = await api.runInference({
          study_id: studyId,
          pipeline,
        });
        setTaskId(res.task_id);
        setStatus("queued");

        // Start polling
        pollRef.current = setInterval(async () => {
          try {
            const st = await api.getInferenceStatus(res.task_id);
            setStatus(st.status);
            if (st.progress) setProgress(st.progress);

            if (
              st.status === "SUCCESS" ||
              st.status === "FAILURE" ||
              st.status === "completed" ||
              st.status === "error"
            ) {
              stopPolling();
            }
          } catch {
            // Polling error — keep trying
          }
        }, 2000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Analiz başlatılamadı");
        setStatus("error");
      }
    },
    [stopPolling]
  );

  const reset = useCallback(() => {
    stopPolling();
    setTaskId(null);
    setStatus("idle");
    setProgress(null);
    setError(null);
  }, [stopPolling]);

  // Cleanup on unmount
  useEffect(() => () => stopPolling(), [stopPolling]);

  return { taskId, status, progress, error, start, reset };
}

/* ── useReport: fetch report for a study ── */
export function useReport(studyId: string | null) {
  const [report, setReport] = useState<LungRADSReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!studyId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReport(studyId);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rapor yüklenemedi");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [studyId]);

  return { report, loading, error, fetchReport: fetch };
}
