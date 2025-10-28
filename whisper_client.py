"""
Whisper语音识别客户端模块
用于将音频文件转换为文本
"""
import requests
import logging
from pathlib import Path
from typing import Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WhisperClient:
    """Whisper API客户端"""
    
    def __init__(self, base_url: str, timeout: int = 300):
        """
        初始化Whisper客户端
        
        Args:
            base_url: Whisper服务的基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"初始化WhisperClient，服务地址: {self.base_url}")
    
    def transcribe(self, audio_file_path: str, output_format: str = "json") -> Optional[str]:
        """
        将音频文件转换为文本
        
        Args:
            audio_file_path: 本地音频文件路径
            output_format: 输出格式，默认为json
            
        Returns:
            转换后的文本内容，失败返回None
        """
        audio_path = Path(audio_file_path)
        
        # 检查文件是否存在
        if not audio_path.exists():
            logger.error(f"音频文件不存在: {audio_file_path}")
            return None
        
        # 检查文件是否为空
        if audio_path.stat().st_size == 0:
            logger.error(f"音频文件为空: {audio_file_path}")
            return None
        
        logger.info(f"开始转录音频文件: {audio_file_path}")
        
        try:
            # 构建请求URL
            url = f"{self.base_url}/asr"
            params = {"output": output_format}
            
            # 打开文件并发送请求
            with open(audio_path, 'rb') as audio_file:
                files = {'audio_file': (audio_path.name, audio_file, 'audio/*')}
                
                logger.debug(f"发送请求到: {url}?output={output_format}")
                response = requests.post(
                    url,
                    params=params,
                    files=files,
                    timeout=self.timeout
                )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析JSON响应
            result = response.json()
            logger.debug(f"API响应: {result}")
            
            # 提取文本内容
            # 根据Whisper API的响应格式，文本通常在'text'字段中
            if isinstance(result, dict):
                text = result.get('text', '')
            elif isinstance(result, str):
                text = result
            else:
                logger.warning(f"未知的响应格式: {type(result)}")
                text = str(result)
            
            if text:
                logger.info(f"成功转录音频，文本长度: {len(text)}字符")
                return text
            else:
                logger.warning("转录结果为空")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时（{self.timeout}秒）")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"转录过程发生错误: {str(e)}")
            return None


if __name__ == "__main__":
    # 测试代码
    client = WhisperClient(base_url="http://10.18.188.89:9000")
    
    # 示例：转录音频文件
    text = client.transcribe(r"C:\Users\m1876\Desktop\project\pyutils\biliSummary\downloads\1.aac")
    if text:
        print(f"转录结果: {text}")

