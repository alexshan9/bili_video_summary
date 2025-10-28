"""
B站视频总结工具主程序
整合bilix下载、whisper转录、LLM总结的完整流程
"""
import asyncio
import configparser
import logging
import sys
import shutil
from pathlib import Path
from typing import Optional

from bilix.sites.bilibili import DownloaderBilibili
from whisper_client import WhisperClient
from llm_client import LLMClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BiliSummary:
    """B站视频总结工具"""
    
    def __init__(self, config_path: str = "config.ini"):
        """
        初始化BiliSummary
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化客户端
        self.whisper_client = WhisperClient(
            base_url=self.config['whisper']['base_url'],
            timeout=int(self.config['whisper']['timeout'])
        )
        
        self.llm_client = LLMClient(
            base_url=self.config['litellm']['base_url'],
            api_key=self.config['litellm']['api_key'],
            model=self.config['litellm']['model'],
            default_prompt=self.config['summary']['default_prompt'],
            timeout=int(self.config['litellm']['timeout'])
        )
        
        logger.info("BiliSummary初始化完成")
    
    def _load_config(self) -> configparser.ConfigParser:
        """
        加载配置文件
        
        Returns:
            配置对象
        """
        config = configparser.ConfigParser()
        
        if not Path(self.config_path).exists():
            logger.error(f"配置文件不存在: {self.config_path}")
            logger.info("请参考 config.ini.example 创建配置文件")
            sys.exit(1)
        
        config.read(self.config_path, encoding='utf-8')
        logger.info(f"成功加载配置文件: {self.config_path}")
        
        return config
    
    async def download_audio(self, video_url: str, save_dir: str = "./tmp") -> Optional[str]:
        """
        从B站下载视频音频
        
        Args:
            video_url: B站视频URL
            save_dir: 保存目录（默认为./tmp，每次下载前会清空）
            
        Returns:
            下载的音频文件路径，失败返回None
        """
        try:
            logger.info(f"开始下载音频: {video_url}")
            
            # 清理并重建tmp目录
            save_path = Path(save_dir)
            if save_path.exists():
                logger.info(f"清理临时目录: {save_dir}")
                shutil.rmtree(save_path)
            
            # 创建新的临时目录
            save_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建临时目录: {save_dir}")
            
            async with DownloaderBilibili() as downloader:
                # 下载音频
                await downloader.get_video(
                    url=video_url,
                    only_audio=True,
                    path=save_dir
                )
            
            # 查找下载的音频文件（支持多种音频格式）
            audio_files = (
                list(save_path.glob("**/*.m4a")) + 
                list(save_path.glob("**/*.mp3")) + 
                list(save_path.glob("**/*.aac")) +
                list(save_path.glob("**/*.wav"))
            )
            
            if audio_files:
                # 按修改时间排序，取最新的
                latest_audio = max(audio_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"找到下载的音频文件: {latest_audio}")
                
                # 重命名为 temp.后缀名
                file_extension = latest_audio.suffix  # 获取原始扩展名（包含点号，如 .aac）
                new_filename = f"temp{file_extension}"
                new_path = save_path / new_filename
                
                # 如果文件名已经是temp.xxx，则不需要重命名
                if latest_audio.name != new_filename:
                    latest_audio.rename(new_path)
                    logger.info(f"文件已重命名为: {new_filename}")
                    latest_audio = new_path
                
                logger.info(f"音频下载完成: {latest_audio}")
                return str(latest_audio)
            else:
                logger.error("未找到下载的音频文件")
                return None
                
        except Exception as e:
            logger.error(f"下载音频失败: {str(e)}")
            return None
    
    def audio_to_text(self, audio_path: str) -> Optional[str]:
        """
        将音频转换为文本
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录的文本内容，失败返回None
        """
        logger.info(f"开始转录音频: {audio_path}")
        return self.whisper_client.transcribe(audio_path)
    
    def text_to_summary(self, text: str, custom_prompt: Optional[str] = None) -> Optional[str]:
        """
        将文本生成总结
        
        Args:
            text: 文本内容
            custom_prompt: 自定义提示词
            
        Returns:
            生成的总结，失败返回None
        """
        logger.info("开始生成总结")
        return self.llm_client.summarize(text, custom_prompt)
    
    async def process_video(
        self, 
        video_url: str, 
        save_dir: str = "./downloads",
        custom_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        完整处理流程：下载 -> 转录 -> 总结
        
        Args:
            video_url: B站视频URL
            save_dir: 下载保存目录
            custom_prompt: 自定义总结提示词
            
        Returns:
            生成的总结内容，失败返回None
        """
        logger.info("=" * 50)
        logger.info("开始处理视频总结任务")
        logger.info(f"视频URL: {video_url}")
        logger.info("=" * 50)
        
        summary = None
        tmp_dir = "./tmp"
        
        try:
            # 步骤1：下载音频（使用tmp_dir）
            audio_path = await self.download_audio(video_url, tmp_dir)
            if not audio_path:
                logger.error("下载音频失败，流程终止")
                return None
            
            # 步骤2：转录音频
            text = self.audio_to_text(audio_path)
            if not text:
                logger.error("转录音频失败，流程终止")
                return None
            
            logger.info(f"转录文本预览（前200字）: {text[:200]}...")
            
            # 步骤3：生成总结
            summary = self.text_to_summary(text, custom_prompt)
            if not summary:
                logger.error("生成总结失败，流程终止")
                return None
            
            logger.info("=" * 50)
            logger.info("视频总结任务完成")
            logger.info("=" * 50)
            
            return summary
            
        finally:
            # 清理临时目录和下载目录
            for dir_path in [tmp_dir, save_dir]:
                if Path(dir_path).exists():
                    try:
                        shutil.rmtree(dir_path)
                        logger.info(f"已清理目录: {dir_path}")
                    except Exception as e:
                        logger.warning(f"清理目录失败 {dir_path}: {str(e)}")
    
    def process_audio_file(
        self, 
        audio_path: str, 
        custom_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        处理本地音频文件：转录 -> 总结
        
        Args:
            audio_path: 本地音频文件路径
            custom_prompt: 自定义总结提示词
            
        Returns:
            生成的总结内容，失败返回None
        """
        logger.info("=" * 50)
        logger.info("开始处理音频文件总结任务")
        logger.info(f"音频文件: {audio_path}")
        logger.info("=" * 50)
        
        # 步骤1：转录音频
        text = self.audio_to_text(audio_path)
        if not text:
            logger.error("转录音频失败，流程终止")
            return None
        
        logger.info(f"转录文本预览（前200字）: {text[:200]}...")
        
        # 步骤2：生成总结
        summary = self.text_to_summary(text, custom_prompt)
        if not summary:
            logger.error("生成总结失败，流程终止")
            return None
        
        logger.info("=" * 50)
        logger.info("音频文件总结任务完成")
        logger.info("=" * 50)
        
        return summary


async def main():
    """主函数示例"""
    # 初始化BiliSummary
    bili_summary = BiliSummary()
    
    # 示例1：处理B站视频URL
    video_url = "https://www.bilibili.com/video/BV1THstzuEZ9/?spm_id_from=333.1007.tianma.2-2-5.click"
    # audio_path = await bili_summary.download_audio(video_url)
    # print(audio_path)
    summary = await bili_summary.process_video(video_url)
    
    if summary:
        print("\n" + "=" * 50)
        print("视频总结:")
        print("=" * 50)
        print(summary)
        print("=" * 50)
    
    # 示例2：处理本地音频文件
    # audio_path = "/path/to/your/audio.mp3"
    # summary = bili_summary.process_audio_file(audio_path)
    # if summary:
    #     print(f"\n音频总结:\n{summary}")


if __name__ == "__main__":
    asyncio.run(main())

