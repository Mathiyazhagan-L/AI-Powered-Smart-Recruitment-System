"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { useReportViolation, useReportFrame } from "@/lib/hooks/useProctoring";
import { toast } from "sonner";

interface ProctoringMonitorProps {
  candidateId: number;
  assessmentType: string;
  onTerminated: () => void;
}

export default function ProctoringMonitor({
  candidateId,
  assessmentType,
  onTerminated,
}: ProctoringMonitorProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Client-side detection state refs
  const noFaceStartRef = useRef<number | null>(null);
  const clientFaceWarnedRef = useRef(false);
  const multiPersonStartRef = useRef<number | null>(null);
  const phoneStartRef = useRef<number | null>(null);
  const lastPhoneWarnRef = useRef<number>(0);
  const lastMultiPersonWarnRef = useRef<number>(0);
  const cocoModelRef = useRef<any>(null);

  const reportViolation = useReportViolation();
  const reportFrame = useReportFrame();

  // ─── Report to backend ────────────────────────────────────────────────────────
  const handleViolation = useCallback(
    async (type: string, message: string) => {
      toast.error(message, { duration: 5000 });
      try {
        const res = await reportViolation.mutateAsync({
          candidate_id: candidateId,
          assessment_type: assessmentType,
          violation_type: type,
        });
        if (res.is_terminated) onTerminated();
      } catch (e) {
        console.error("Failed to report violation", e);
      }
    },
    [candidateId, assessmentType, onTerminated, reportViolation]
  );

  // ─── DOM Event Violations ─────────────────────────────────────────────────────
  useEffect(() => {
    const onBlur = () =>
      handleViolation("TAB_SWITCH", "⚠ You switched away from the assessment.");
    const onVisibility = () => {
      if (document.hidden)
        handleViolation("TAB_SWITCH", "⚠ Assessment tab is no longer visible.");
    };
    const onFullscreen = () => {
      if (!document.fullscreenElement)
        handleViolation("FULLSCREEN_EXIT", "⚠ You exited fullscreen mode.");
    };
    const onContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      handleViolation("RIGHT_CLICK", "⚠ Right-click is disabled during the assessment.");
    };
    const onClipboard = (e: ClipboardEvent) => {
      e.preventDefault();
      handleViolation("COPY_PASTE", "⚠ Copy/Paste is prohibited during the assessment.");
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "F12" ||
        (e.ctrlKey && e.shiftKey && (e.key === "I" || e.key === "J" || e.key === "C"))
      ) {
        e.preventDefault();
        handleViolation("DEV_TOOLS", "⚠ Developer tools are prohibited.");
      }
    };

    window.addEventListener("blur", onBlur);
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("fullscreenchange", onFullscreen);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("copy", onClipboard);
    document.addEventListener("paste", onClipboard);
    document.addEventListener("keydown", onKeyDown);

    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    }

    return () => {
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("fullscreenchange", onFullscreen);
      document.removeEventListener("contextmenu", onContextMenu);
      document.removeEventListener("copy", onClipboard);
      document.removeEventListener("paste", onClipboard);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [handleViolation]);

  // ─── Camera + Client-side AI Detection ───────────────────────────────────────
  useEffect(() => {
    let captureInterval: NodeJS.Timeout;
    let detectionInterval: NodeJS.Timeout;

    // ── 1. Load COCO-SSD for phone/person detection ───────────────────────────
    const loadCocoSsd = async () => {
      try {
        // Dynamic import so it doesn't block SSR/initial render
        const tf = await import("@tensorflow/tfjs");
        await tf.ready();
        const cocoSsd = await import("@tensorflow-models/coco-ssd");
        cocoModelRef.current = await cocoSsd.load({ base: "lite_mobilenet_v2" });
        console.log("[Proctoring] COCO-SSD model loaded");
      } catch (e) {
        console.warn("[Proctoring] COCO-SSD unavailable — falling back to backend-only detection", e);
      }
    };

    // ── 2. Run COCO-SSD on video stream every 2 seconds ──────────────────────
    const runObjectDetection = async () => {
      const video = videoRef.current;
      if (!video || video.readyState < 2 || video.paused || !cocoModelRef.current) return;

      try {
        const predictions: Array<{ class: string; score: number }> =
          await cocoModelRef.current.detect(video);

        const now = Date.now();
        let phoneFound = false;
        let personCount = 0;

        for (const pred of predictions) {
          if (pred.class === "cell phone" && pred.score > 0.55) phoneFound = true;
          if (pred.class === "person" && pred.score > 0.78) personCount++;
        }

        // Phone detected -> require 2 seconds of continuous detection
        if (phoneFound) {
          if (phoneStartRef.current === null) {
            phoneStartRef.current = now;
          } else if (now - phoneStartRef.current >= 2000 && now - lastPhoneWarnRef.current > 5000) {
            lastPhoneWarnRef.current = now;
            handleViolation("PHONE_DETECTED", "📵 Cell phone detected! This is a strict violation.");
            reportFrame.mutateAsync({
              candidate_id: candidateId,
              assessment_type: assessmentType,
              frame: captureCurrentFrame() ?? "",
            }).then((res) => {
              if (res?.is_terminated) onTerminated();
            }).catch(() => {});
          }
        } else {
          phoneStartRef.current = null;
        }

        // Multiple persons detected (Require 4 seconds of continuous detection)
        if (personCount > 1) {
          if (multiPersonStartRef.current === null) {
            multiPersonStartRef.current = now;
          } else if (now - multiPersonStartRef.current >= 4000 && now - lastMultiPersonWarnRef.current > 8000) {
            lastMultiPersonWarnRef.current = now;
            toast.error(
              "👥 Multiple people detected in camera! Only you should be on camera.",
              { id: "multi-person-warning", duration: 6000 }
            );
            handleViolation("MULTIPLE_PERSONS", "Multiple people detected in the camera frame.");
            
            reportFrame.mutateAsync({
              candidate_id: candidateId,
              assessment_type: assessmentType,
              frame: captureCurrentFrame() ?? "",
            }).then((res) => {
              if (res?.is_terminated) onTerminated();
            }).catch(() => {});
          }
        } else {
          multiPersonStartRef.current = null; // Reset if only 1 person or 0 people
        }

        // No person detected (proxy for no face)
        if (personCount === 0) {
          if (noFaceStartRef.current === null) {
            noFaceStartRef.current = now;
            clientFaceWarnedRef.current = false;
          } else if (now - noFaceStartRef.current >= 3000 && !clientFaceWarnedRef.current) {
            clientFaceWarnedRef.current = true;
            toast.warning(
              "⚠ You are not visible in the camera! Please face the camera.",
              { id: "no-face-warning", duration: 6000 }
            );
          }
        } else {
          noFaceStartRef.current = null;
          clientFaceWarnedRef.current = false;
        }

      } catch (e) {
        // Ignore per-frame errors
      }
    };

    // ── 3. Capture + send frame to backend (backup for YOLO phone & face AI) ──
    const captureCurrentFrame = (): string | null => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState < 2) return null;
      canvas.width = video.videoWidth || 320;
      canvas.height = video.videoHeight || 240;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL("image/jpeg", 0.7);
    };

    const captureAndSendFrame = async () => {
      const frame = captureCurrentFrame();
      if (!frame) return;
      try {
        const res = await reportFrame.mutateAsync({
          candidate_id: candidateId,
          assessment_type: assessmentType,
          frame,
        });
        if (res.is_terminated) {
          onTerminated();
        } else if (res.message) {
          // Backend confirmed something COCO-SSD may have missed (e.g., looking away via MediaPipe)
          toast.error(res.message, { id: "backend-proctoring", duration: 5000 });
        }
      } catch (e) {
        console.error("Frame send failed", e);
      }
    };

    // ── Start camera ──────────────────────────────────────────────────────────
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 320 }, height: { ideal: 240 }, facingMode: "user" },
          audio: false,
        });
        streamRef.current = mediaStream;

        const video = videoRef.current;
        if (video) {
          video.srcObject = mediaStream;
          video.onloadedmetadata = () => {
            video.play().catch((err) => console.error("Video play error:", err));
          };
          setTimeout(() => {
            if (video.paused) {
              video.play().catch(() => {});
            }
          }, 1200);
        }

        // Load COCO-SSD model (async, starts detecting as soon as ready)
        await loadCocoSsd();

        // Client-side COCO-SSD: run every 2 seconds for near-instant phone & person detection
        detectionInterval = setInterval(runObjectDetection, 2000);

        // Backend frames: every 4 seconds
        captureInterval = setInterval(captureAndSendFrame, 4000);
      } catch (err) {
        console.error("Camera access error:", err);
        toast.error("Camera access denied. Proctoring cannot start.");
        onTerminated();
      }
    };

    startCamera();

    return () => {
      if (captureInterval) clearInterval(captureInterval);
      if (detectionInterval) clearInterval(detectionInterval);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      cocoModelRef.current = null;
    };
  }, [candidateId, assessmentType]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="fixed bottom-4 right-4 w-48 rounded-xl overflow-hidden shadow-2xl border-2 border-white/10 z-50 bg-gray-900">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover block"
        style={{ minHeight: "108px", background: "#111" }}
      />
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <div className="absolute top-1 left-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded-md flex items-center gap-1">
        <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
        Proctoring Active
      </div>
    </div>
  );
}
