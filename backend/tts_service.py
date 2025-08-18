"""
Enhanced TTS Service with OpenAI TTS API Support
오픈소스 Piper TTS와 OpenAI TTS API를 모두 지원하는 TTS 서비스
"""
import os
import asyncio
import logging
import tempfile
import io
from pathlib import Path
from typing import Optional, Union
import wave

# Environment variable loading
from dotenv import load_dotenv
load_dotenv()

# OpenAI API for TTS
try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

# Piper TTS (fallback)
try:
    import piper
    from piper import PiperVoice
    piper_available = True
except ImportError:
    piper = None
    PiperVoice = None
    piper_available = False

logger = logging.getLogger(__name__)

class EnhancedTTSService:
    """Enhanced TTS Service - OpenAI API + Piper fallback"""
    
    def __init__(self, use_openai: bool = True, model_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        TTS 서비스 초기화
        
        Args:
            use_openai: OpenAI TTS API 사용 여부 (기본값: True)
            model_path: Piper 모델 파일 경로 (fallback용)
            config_path: 모델 설정 파일 경로
        """
        self.use_openai = use_openai and openai_available
        self.openai_client = None
        
        # OpenAI TTS API 설정
        if self.use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI TTS API 클라이언트 초기화 완료")
            else:
                logger.warning("OPENAI_API_KEY가 설정되지 않음. Piper TTS로 fallback")
                self.use_openai = False
        
        # Piper TTS 설정 (fallback)
        self.model_path = model_path or self._get_default_model_path()
        self.config_path = config_path or self._get_default_config_path()
        self.voice = None
        self.sample_rate = 22050  # 기본 샘플레이트
        
        primary_engine = "OpenAI TTS API" if self.use_openai else "Piper TTS"
        logger.info(f"TTS 서비스 초기화 - 주요 엔진: {primary_engine}")
    
    def _get_default_model_path(self) -> str:
        """기본 한국어 모델 경로 반환"""
        # 한국어 모델이 없는 경우 영어 모델 사용
        models_dir = Path.home() / ".local" / "share" / "piper-voices"
        
        # 한국어 모델 우선 검색
        korean_patterns = [
            "ko_KR-*/*.onnx",
            "korean-*/*.onnx"
        ]
        
        for pattern in korean_patterns:
            korean_models = list(models_dir.glob(pattern))
            if korean_models:
                return str(korean_models[0])
        
        # 영어 모델 대체
        english_patterns = [
            "en_US-*/*.onnx",
            "en-*/*.onnx",
            "*/*.onnx"
        ]
        
        for pattern in english_patterns:
            models = list(models_dir.glob(pattern))
            if models:
                logger.warning("한국어 모델을 찾을 수 없어 영어 모델을 사용합니다")
                return str(models[0])
        
        # 기본 경로 반환 (다운로드 필요)
        return str(models_dir / "en_US-lessac-high.onnx")
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        model_dir = Path(self.model_path).parent
        config_files = list(model_dir.glob("*.onnx.json"))
        
        if config_files:
            return str(config_files[0])
        
        return str(model_dir / f"{Path(self.model_path).stem}.json")
    
    def _load_voice(self):
        """음성 모델 로딩 (지연 로딩)"""
        if self.voice is None:
            try:
                logger.info(f"Piper 음성 모델 로딩 중: {self.model_path}")
                
                if not os.path.exists(self.model_path):
                    logger.error(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
                    # 간단한 대체 구현
                    return self._create_fallback_voice()
                
                self.voice = PiperVoice.load(self.model_path, config_path=self.config_path)
                logger.info("Piper 음성 모델 로딩 완료")
                
            except Exception as e:
                logger.warning(f"Piper 모델 로딩 실패: {e}")
                # 대체 구현 사용
                return self._create_fallback_voice()
    
    def _create_fallback_voice(self):
        """Piper 모델이 없을 때 대체 구현"""
        logger.info("대체 TTS 구현을 사용합니다 (무음 생성)")
        self.voice = "fallback"
    
    async def synthesize_text(self, text: str, output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        텍스트를 음성으로 합성
        
        Args:
            text: 합성할 텍스트
            output_path: 출력 파일 경로 (None이면 bytes 반환)
        
        Returns:
            파일 경로 또는 오디오 바이트 데이터
        """
        try:
            # OpenAI TTS API 우선 사용
            if self.use_openai and self.openai_client:
                return await self._synthesize_with_openai(text, output_path)
            
            # Piper TTS fallback
            return await self._synthesize_with_piper(text, output_path)
                
        except Exception as e:
            logger.error(f"TTS 합성 실패: {e}")
            return await self._synthesize_fallback(text, output_path)
    
    async def _synthesize_with_openai(self, text: str, output_path: Optional[str] = None) -> Union[str, bytes]:
        """OpenAI TTS API를 사용한 음성 합성"""
        try:
            logger.info(f"OpenAI TTS API로 음성 합성 중: '{text[:50]}...'")
            
            # OpenAI TTS API 호출 (비동기)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.audio.speech.create(
                    model="tts-1",  # 빠른 모델 (tts-1-hd는 고품질이지만 느림)
                    voice="alloy",   # 음성 선택 (alloy, echo, fable, onyx, nova, shimmer)
                    input=text,
                    response_format="wav"
                )
            )
            
            # 오디오 데이터 추출
            audio_data = response.content
            
            if output_path:
                # 파일로 저장
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"OpenAI TTS 오디오 저장: {output_path} ({len(audio_data)} bytes)")
                return output_path
            else:
                # 바이트 데이터로 반환
                logger.info(f"OpenAI TTS 완료: {len(audio_data)} bytes")
                return audio_data
                
        except Exception as e:
            logger.error(f"OpenAI TTS API 실패: {e}")
            # Piper TTS로 fallback
            logger.info("Piper TTS로 fallback 중...")
            return await self._synthesize_with_piper(text, output_path)
    
    async def _synthesize_with_piper(self, text: str, output_path: Optional[str] = None) -> Union[str, bytes]:
        """Piper TTS를 사용한 음성 합성"""
        try:
            self._load_voice()
            
            if self.voice == "fallback":
                return await self._synthesize_fallback(text, output_path)
            
            # Piper TTS 실행 (CPU 집약적이므로 비동기로 처리)
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None, 
                self._synthesize_sync, 
                text
            )
            
            if output_path:
                # 파일로 저장
                self._save_audio_to_file(audio_data, output_path)
                logger.info(f"Piper TTS 오디오 저장: {output_path}")
                return output_path
            else:
                # 바이트 데이터로 반환
                return self._convert_to_wav_bytes(audio_data)
                
        except Exception as e:
            logger.error(f"Piper TTS 합성 실패: {e}")
            return await self._synthesize_fallback(text, output_path)
    
    def _synthesize_sync(self, text: str) -> bytes:
        """동기적 Piper TTS 실행"""
        if self.voice == "fallback":
            raise ValueError("Fallback voice cannot be used in sync mode")
        
        # Piper TTS로 음성 합성
        audio_stream = io.BytesIO()
        self.voice.synthesize(text, audio_stream)
        return audio_stream.getvalue()
    
    async def _synthesize_fallback(self, text: str, output_path: Optional[str] = None) -> Union[str, bytes]:
        """대체 TTS 구현 (무음 생성)"""
        duration = max(len(text) * 0.1, 1.0)  # 텍스트 길이에 비례한 무음
        samples = int(self.sample_rate * duration)
        
        # 무음 생성
        audio_data = b'\x00' * (samples * 2)  # 16-bit mono
        
        if output_path:
            self._save_silent_audio(audio_data, output_path)
            logger.info(f"대체 TTS 오디오 생성: {output_path} (무음 {duration:.1f}초)")
            return output_path
        else:
            return self._convert_silent_to_wav_bytes(audio_data)
    
    def _save_audio_to_file(self, audio_data: bytes, output_path: str):
        """오디오 데이터를 WAV 파일로 저장"""
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
    
    def _save_silent_audio(self, audio_data: bytes, output_path: str):
        """무음 데이터를 WAV 파일로 저장"""
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
    
    def _convert_to_wav_bytes(self, audio_data: bytes) -> bytes:
        """오디오 데이터를 WAV 바이트로 변환"""
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
        return output.getvalue()
    
    def _convert_silent_to_wav_bytes(self, audio_data: bytes) -> bytes:
        """무음 데이터를 WAV 바이트로 변환"""
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
        return output.getvalue()
    
    async def synthesize_streaming(self, text: str, chunk_size: int = 1024):
        """스트리밍 TTS (향후 구현)"""
        # 현재는 전체 합성 후 청크로 분할
        audio_bytes = await self.synthesize_text(text)
        
        if isinstance(audio_bytes, str):
            # 파일 경로인 경우 읽기
            with open(audio_bytes, 'rb') as f:
                audio_bytes = f.read()
        
        # 청크 단위로 yield
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i + chunk_size]
    
    def get_supported_languages(self) -> list:
        """지원하는 언어 목록"""
        return ["ko", "en", "en-US"]
    
    def get_voice_info(self) -> dict:
        """음성 정보 반환"""
        return {
            "primary_engine": "OpenAI TTS API" if self.use_openai else "Piper TTS",
            "openai_available": self.use_openai and self.openai_client is not None,
            "piper_model_path": self.model_path,
            "piper_config_path": self.config_path,
            "sample_rate": self.sample_rate,
            "piper_loaded": self.voice is not None,
            "supported_languages": self.get_supported_languages(),
            "openai_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] if self.use_openai else []
        }

# 전역 TTS 서비스 인스턴스
tts_service = None

def get_tts_service(use_openai: bool = True, model_path: Optional[str] = None) -> EnhancedTTSService:
    """TTS 서비스 싱글톤 인스턴스 반환"""
    global tts_service
    if tts_service is None:
        tts_service = EnhancedTTSService(use_openai=use_openai, model_path=model_path)
    return tts_service

# 레거시 호환성을 위한 alias
PiperTTSService = EnhancedTTSService

# 일반적인 응답 프리캐싱을 위한 템플릿
COMMON_RESPONSES = {
    "greeting": "안녕하세요! 오늘 무엇을 도와드릴까요?",
    "memo_saved": "메모를 저장했습니다.",
    "todo_added": "할일을 추가했습니다.",
    "event_created": "일정을 등록했습니다.",
    "unknown": "죄송합니다. 명령을 이해하지 못했습니다.",
    "error": "처리 중 오류가 발생했습니다.",
    "success": "완료되었습니다.",
    "thanks": "천만에요! 언제든 말씀해주세요."
}

async def precache_common_responses():
    """일반적인 응답들을 미리 캐싱"""
    tts = get_tts_service()
    cache_dir = Path(tempfile.gettempdir()) / "tts_cache"
    cache_dir.mkdir(exist_ok=True)
    
    logger.info("일반적인 응답들을 TTS 캐싱 중...")
    
    for key, text in COMMON_RESPONSES.items():
        cache_path = cache_dir / f"{key}.wav"
        if not cache_path.exists():
            try:
                await tts.synthesize_text(text, str(cache_path))
                logger.info(f"TTS 캐시 생성: {key}")
            except Exception as e:
                logger.warning(f"TTS 캐시 생성 실패 ({key}): {e}")
    
    logger.info("TTS 캐싱 완료")