#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import os
import pathlib
import queue
import re
import threading
from datetime import datetime

import cv2
from loguru import logger

SAVE_DIR = "Captures/videos"
MAX_CLIPS = 10
_SENTINEL = object()


class ClipManager:
    """最新N件の動画ファイルパスを管理し、古いものをディスクから削除する。

    スレッドセーフ設計: _lock により add_and_rotate() の複数スレッドからの
    同時呼び出しを排他制御する。
    """

    def __init__(self, max_clips: int = MAX_CLIPS):
        self._clips: collections.deque = collections.deque(maxlen=max_clips)
        self._lock = threading.Lock()

    def add_and_rotate(self, path: str) -> None:
        """新しいクリップを登録し、上限超過時は最古のファイルを物理削除する。

        削除処理はブロッキングで完了してからリターンする（呼び出し元同期保証）。
        """
        with self._lock:
            if len(self._clips) == self._clips.maxlen:
                oldest = self._clips[0]
                _delete_file(oldest)  # 物理削除（完了まで待機）
            self._clips.append(path)
            logger.info(
                f"[ClipManager] 登録: {path} "
                f"({len(self._clips)}/{self._clips.maxlen})"
            )


def _delete_file(path: str) -> None:
    """指定パスのファイルを安全に削除する。

    - FileNotFoundError: 既に削除済みの場合は無視（冪等性確保）
    - PermissionError: OS によるアクセス拒否（Windows でファイル使用中など）
    - OSError: その他 I/O 系エラー
    """
    try:
        pathlib.Path(path).unlink(missing_ok=True)
        logger.info(f"[ClipManager] 古い録画を削除しました: {path}")
    except FileNotFoundError:
        # missing_ok=True で通常は到達しないが念のため
        logger.warning(f"[ClipManager] 削除対象が見つかりませんでした（無視）: {path}")
    except PermissionError as e:
        logger.error(
            f"[ClipManager] アクセス拒否による削除失敗（ファイル使用中の可能性）: "
            f"{path} / {e}"
        )
    except OSError as e:
        logger.error(f"[ClipManager] ファイル削除失敗 (OSError): {path} / {e}")


class VideoRecorder:
    """Producer-Consumer パターンで非同期動画録画を行うクラス。

    Camera.camera_update() が Producer としてフレームを供給し、
    本クラスの Consumer スレッドが VideoWriter でディスクへ書き出す。

    スレッドモデル:
        - start_recording() / stop_recording() はコマンドスレッドから呼ぶ。
        - _consumer() は VideoRecorderThread で動作する。
        - _camera._recording_queue の書き換えは GIL によりアトミック。
        - _is_recording の読み書きは同一スレッドからのみ行うため Lock 不要。
    """

    def __init__(self, camera, clip_name: str = "unknown", save_dir: str = SAVE_DIR):
        """
        Args:
            camera   : Camera インスタンス（camera.fps / camera._recording_queue を使用）
            clip_name: ファイル名プレフィクス（クラスの NAME 属性を想定。不正文字は自動置換）
            save_dir : 動画保存ディレクトリ（デフォルト: Captures/videos）
        """
        self._camera = camera
        self._clip_name = clip_name
        self._save_dir = save_dir
        self._queue: queue.Queue = queue.Queue(maxsize=300)  # 約6.7秒@45fps
        self._thread: threading.Thread | None = None
        self._current_path: str | None = None
        self._is_recording: bool = False

    # ------------------------------------------------------------------
    # 公開インターフェース
    # ------------------------------------------------------------------

    def start_recording(self) -> None:
        """新しいクリップの録画を開始する。既に録画中の場合は何もしない。"""
        if self._is_recording:
            return

        os.makedirs(self._save_dir, exist_ok=True)
        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        # ファイルシステム使用不可文字を _ に置換
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", self._clip_name)
        # 絶対パスで保持する（stop_recording() の戻り値仕様を満たすため）
        self._current_path = os.path.abspath(
            os.path.join(self._save_dir, f"{safe_name}_{dt}_{pid}.avi")
        )

        # キューを空にしてから開始（前回の残留フレームを除去）
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        # Consumer スレッド起動 → カメラにキューを登録
        # 順序: スレッド start() 後に _recording_queue を設定することで、
        # Consumer 未起動のままフレームが届くことを防ぐ。
        self._thread = threading.Thread(
            target=self._consumer,
            daemon=True,
            name="VideoRecorderThread",
        )
        self._thread.start()
        self._camera._recording_queue = self._queue  # Producer 側に登録（GIL 保護）
        self._is_recording = True
        logger.info(f"[VideoRecorder] 録画開始: {self._current_path}")

    def stop_recording(self) -> str | None:
        """録画を停止し、全フレームの書き出し完了後に絶対パスを返す。

        処理順:
            1. カメラ側のキュー参照を None にして新規フレーム供給を遮断。
            2. 番兵オブジェクトをキューに投入して Consumer に終了を通知。
            3. thread.join() で Consumer スレッドの完了（VideoWriter.release() 含む）を待機。
            4. 絶対パスを返す。

        Returns:
            保存が完了した動画ファイルの絶対パス。録画中でなければ None。
        """
        if not self._is_recording:
            return None

        # ① Producer 停止（Camera スレッドからの新規フレーム供給を遮断）
        self._camera._recording_queue = None  # GIL によりアトミック書き換え

        # ② Consumer 終了通知（番兵投入）
        self._queue.put(_SENTINEL)

        # ③ Consumer スレッドの完全終了を待機（VideoWriter.release() まで含む）
        if self._thread is not None:
            self._thread.join()
            self._thread = None

        # ④ 状態をリセットして絶対パスを返す
        self._is_recording = False
        abs_path = self._current_path  # start_recording() で os.path.abspath() 済み
        self._current_path = None
        logger.info(f"[VideoRecorder] 録画停止・保存完了: {abs_path}")
        return abs_path

    def is_recording(self) -> bool:
        """現在録画中かどうかを返す。"""
        return self._is_recording

    # ------------------------------------------------------------------
    # Consumer スレッド本体
    # ------------------------------------------------------------------

    def _consumer(self) -> None:
        """VideoRecorderThread のエントリポイント。

        キューからフレームを取り出して VideoWriter へ書き込む。
        番兵（_SENTINEL）を受け取ったら書き込みを終了し、
        finally ブロックで VideoWriter.release() を確実に呼び出す。
        """
        fps = int(self._camera.fps)
        writer = cv2.VideoWriter(
            self._current_path,
            cv2.VideoWriter_fourcc(*"MJPG"),
            fps,
            (1280, 720),
        )
        logger.debug(
            f"[VideoRecorder] Consumer 開始: fps={fps}, path={self._current_path}"
        )
        try:
            while True:
                try:
                    item = self._queue.get(timeout=5.0)
                except queue.Empty:
                    # stop_recording() が呼ばれていないのに 5 秒フレームが来ない場合
                    # → ループ継続（録画中フラグは stop_recording() 側で制御）
                    logger.warning(
                        "[VideoRecorder] フレーム取得タイムアウト（5秒）、継続待機"
                    )
                    continue

                if item is _SENTINEL:
                    # 番兵受信 → キュー内の残フレームは届いているので終了
                    break

                writer.write(item)

        except Exception as e:
            logger.error(f"[VideoRecorder] Consumer 例外: {e}")
        finally:
            # VideoWriter.release() は必ずここで呼ばれる（ファイルヘッダの確定）
            writer.release()
            logger.debug("[VideoRecorder] VideoWriter 解放完了")
