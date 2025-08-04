# balitower_v1.py  –  loop panjang + analisis frame
import os, time, psutil, multiprocessing, newrelic.agent

# ── 0) NEW RELIC INIT (diekssekusi ulang di child – aman) ───────────────
newrelic.agent.initialize('newrelic.ini')
APP = newrelic.agent.register_application(timeout=10.0)

# ── 1) UTIL – tambahkan atribut fungsi & core ke span saat ini ───────────
def _add_fn_core_attrs(fname: str):
    proc = psutil.Process()
    newrelic.agent.add_custom_span_attribute("function_name", fname)
    newrelic.agent.add_custom_span_attribute("cpu_core",      proc.cpu_num())
    newrelic.agent.add_custom_span_attribute("pid",           os.getpid())

# ── 2) FUNGSI PEMUTAR VIDEO (loop tak berujung) ─────────────────────────
def play_a_video(video_path: str, window_name: str) -> None:
    frame = 0
    while True:
        proc = psutil.Process()
        print(f"[{window_name}] Frame {frame} | Core {proc.cpu_num()} | PID {os.getpid()}")

        # Custom Event tiap frame
        newrelic.agent.record_custom_event(
            "VideoLoopEventSampling",
            {
                "function_name": "play_a_video",
                "frame": frame,
                "window_name": window_name,
                "video_path": video_path,
                "cpu_core": proc.cpu_num(),
                "pid": os.getpid()
            },
            APP
        )

        # Analisis frame (span terpisah)
        analyze_frame(video_path, window_name, frame)
        time.sleep(0.5)
        frame += 1

# ── 3) ANALYZE_FRAME – transaksi terpisah per frame ─────────────────────
def analyze_frame(video_path: str, window_name: str, frame_no: int):
    with newrelic.agent.BackgroundTask(APP, name="frame_analysis", group="VideoAnalysis"):
        _add_fn_core_attrs("analyze_frame")
        print(f"[{window_name}] Analysing frame {frame_no}")
        time.sleep(1)

        newrelic.agent.add_custom_span_attribute("frame",       frame_no)
        newrelic.agent.add_custom_span_attribute("video_path",  video_path)
        newrelic.agent.add_custom_span_attribute("window_name", window_name)

# ── 4) MAIN MULTIPROCESSING ─────────────────────────────────────────────
if __name__ == '__main__':
    multiprocessing.set_start_method("spawn", force=True)
    videos = ["video1.mp4", "video2.mp4"]

    procs = []
    for idx, vid in enumerate(videos, 1):
        p = multiprocessing.Process(target=play_a_video,
                                    args=(vid, f"Video {idx}"),
                                    name=f"Video_{idx}")
        p.start()
        procs.append(p)

    for p in procs:
        p.join()