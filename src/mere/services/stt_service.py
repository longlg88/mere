"""
OpenAI Whisper 기반 Speech-to-Text 서비스
"""
import os
import tempfile
import logging
from typing import Optional, Tuple
import whisper
import numpy as np
from pathlib import Path
import asyncio
import torch

logger = logging.getLogger(__name__)

class WhisperSTTService:
    """Whisper 기반 STT 서비스"""
    
    def __init__(self, model_size: str = "base"):
        """
        STT 서비스 초기화
        
        Args:
            model_size: Whisper 모델 크기 (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"STT 서비스 초기화 - 모델: {model_size}, 디바이스: {self.device}")
    
    def _load_model(self):
        """Whisper 모델 로딩 (지연 로딩)"""
        if self.model is None:
            logger.info(f"Whisper {self.model_size} 모델 로딩 중...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper 모델 로딩 완료")
    
    async def transcribe_audio_file(self, audio_file_path: str, language: str = "ko") -> Tuple[str, float]:
        """
        오디오 파일을 텍스트로 변환
        
        Args:
            audio_file_path: 오디오 파일 경로
            language: 언어 코드 (ko, en)
        
        Returns:
            (transcribed_text, confidence)
        """
        try:
            self._load_model()
            
            # Whisper 실행 (CPU 집약적이므로 비동기로 처리)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_file_path, 
                language
            )
            
            text = result["text"].strip()
            
            # 신뢰도 계산 (segments의 평균 no_speech_prob 역수 사용)
            confidence = self._calculate_confidence(result)
            
            logger.info(f"STT 결과: '{text}' (신뢰도: {confidence:.2f})")
            return text, confidence
            
        except Exception as e:
            logger.error(f"STT 처리 실패: {e}")
            return "", 0.0
    
    def _transcribe_sync(self, audio_file_path: str, language: str) -> dict:
        """동기적 Whisper 실행"""
        return self.model.transcribe(
            audio_file_path,
            language=language,
            task="transcribe",
            fp16=False,  # CPU에서는 fp16 비활성화
            verbose=False
        )
    
    def _calculate_confidence(self, result: dict) -> float:
        """STT 결과의 신뢰도 계산"""
        try:
            if "segments" in result and result["segments"]:
                # 각 세그먼트의 no_speech_prob 평균 계산
                no_speech_probs = [seg.get("no_speech_threshold", 0.6) for seg in result["segments"]]
                avg_no_speech = sum(no_speech_probs) / len(no_speech_probs)
                # no_speech_prob가 낮을수록 신뢰도가 높음
                confidence = max(0.0, min(1.0, 1.0 - avg_no_speech))
                return confidence
            return 0.8  # 기본 신뢰도
        except Exception:
            return 0.5
    
    async def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000, language: str = "ko") -> Tuple[str, float]:
        """
        바이트 데이터를 직접 텍스트로 변환
        
        Args:
            audio_data: 오디오 바이트 데이터
            sample_rate: 샘플링 레이트
            language: 언어 코드
        
        Returns:
            (transcribed_text, confidence)
        """
        # 임시 파일로 저장 후 처리
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            return await self.transcribe_audio_file(temp_path, language)
        finally:
            # 임시 파일 삭제
            Path(temp_path).unlink(missing_ok=True)
    
    def get_supported_formats(self) -> list:
        """지원하는 오디오 포맷 목록"""
        return [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    
    def get_model_info(self) -> dict:
        """모델 정보 반환"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "loaded": self.model is not None,
            "supported_languages": ["ko", "en", "ja", "zh", "fr", "de", "es"]
        }


# VAD (Voice Activity Detection) 간단 구현
class SimpleVAD:
    """간단한 음성 활동 감지"""
    
    @staticmethod
    def detect_speech_segments(audio_data: np.ndarray, sample_rate: int = 16000, 
                              frame_duration: float = 0.02, energy_threshold: float = 0.01) -> list:
        """
        음성 구간 감지
        
        Args:
            audio_data: 오디오 numpy 배열
            sample_rate: 샘플링 레이트
            frame_duration: 프레임 길이 (초)
            energy_threshold: 에너지 임계값
        
        Returns:
            [(start_time, end_time), ...] 음성 구간 리스트
        """
        frame_size = int(sample_rate * frame_duration)
        segments = []
        current_start = None
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame = audio_data[i:i + frame_size]
            energy = np.mean(frame ** 2)
            
            current_time = i / sample_rate
            
            if energy > energy_threshold:
                if current_start is None:
                    current_start = current_time
            else:
                if current_start is not None:
                    segments.append((current_start, current_time))
                    current_start = None
        
        # 마지막 세그먼트 처리
        if current_start is not None:
            segments.append((current_start, len(audio_data) / sample_rate))
        
        return segments


# 전역 STT 서비스 인스턴스
stt_service = None

def get_stt_service(model_size: str = "base") -> WhisperSTTService:
    """STT 서비스 싱글톤 인스턴스 반환"""
    global stt_service
    if stt_service is None:
        stt_service = WhisperSTTService(model_size=model_size)
    return stt_service