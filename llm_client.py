"""
LLM对话客户端模块
用于调用LiteLLM API生成文本总结
"""
import requests
import logging
from typing import Optional, List, Dict


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMClient:
    """LiteLLM API客户端"""
    
    def __init__(
        self, 
        base_url: str, 
        api_key: str, 
        model: str = "gpt-4o",
        default_prompt: str = "",
        timeout: int = 60
    ):
        """
        初始化LLM客户端
        
        Args:
            base_url: LiteLLM服务的基础URL
            api_key: API密钥
            model: 使用的模型名称
            default_prompt: 默认的系统提示词
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.default_prompt = default_prompt
        self.timeout = timeout
        logger.info(f"初始化LLMClient，服务地址: {self.base_url}, 模型: {self.model}")
    
    def summarize(
        self, 
        text: str, 
        custom_prompt: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """
        使用LLM生成文本总结
        
        Args:
            text: 需要总结的文本内容
            custom_prompt: 自定义提示词（将与文本拼接作为用户消息）
            system_message: 自定义系统消息（覆盖default_prompt）
            
        Returns:
            生成的总结内容，失败返回None
        """
        if not text or not text.strip():
            logger.error("输入文本为空")
            return None
        
        logger.info(f"开始生成总结，输入文本长度: {len(text)}字符")
        
        try:
            # 构建请求URL
            url = f"{self.base_url}/v1/chat/completions"
            
            # 构建消息列表
            messages: List[Dict[str, str]] = []
            
            # 添加系统消息
            sys_msg = system_message if system_message else self.default_prompt
            if sys_msg:
                messages.append({
                    "role": "system",
                    "content": sys_msg
                })
            
            # 添加用户消息
            user_content = custom_prompt if custom_prompt else ""
            if user_content:
                user_content += "\n\n"
            user_content += f"以下是需要总结的内容：\n\n{text}"
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages
            }
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            logger.debug(f"发送请求到: {url}")
            logger.debug(f"消息数量: {len(messages)}")
            
            # 发送请求
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析JSON响应
            result = response.json()
            logger.debug(f"API响应: {result}")
            
            # 提取总结内容
            # OpenAI格式的响应：choices[0].message.content
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    summary = choice['message']['content']
                    logger.info(f"成功生成总结，长度: {len(summary)}字符")
                    return summary
            
            logger.warning(f"无法从响应中提取总结内容: {result}")
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f"请求超时（{self.timeout}秒）")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"响应内容: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"生成总结过程发生错误: {str(e)}")
            return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        通用的聊天接口
        
        Args:
            messages: 消息列表，格式: [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            
        Returns:
            模型的回复内容，失败返回None
        """
        if not messages:
            logger.error("消息列表为空")
            return None
        
        try:
            url = f"{self.base_url}/v1/chat/completions"
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                data["max_tokens"] = max_tokens
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            logger.debug(f"发送聊天请求，消息数: {len(messages)}")
            
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            
            logger.warning(f"无法从响应中提取内容: {result}")
            return None
            
        except Exception as e:
            logger.error(f"聊天请求失败: {str(e)}")
            return None


if __name__ == "__main__":
#     base_url = http://10.18.188.89:4000
# api_key = 7c7391c2f61e8690b288a0a0134e406ba78804b3a8008432ebe5b41705eb21e1
# model = deepseek-ai/DeepSeek-V3.1
    # 测试代码
    client = LLMClient(
        base_url="http://10.18.188.89:4000",
        api_key="sk-MJyi9Ftzp7azOj9gJoMKuw",
        model="deepseek-ai/DeepSeek-V3.1",
        default_prompt="你是一个专业的视频内容总结助手。请仔细阅读以下视频字幕内容，提取关键信息，生成一份结构化的总结，包括：1. 核心主题 2. 主要观点（3-5点）3. 关键结论。请使用简洁清晰的中文。"
    )
    
    # 示例：生成总结
    summary = client.summarize("A： 因为StringBuffer内部使用synchronized关键字对方法进行了同步处理，确保了多线程环境下对字符串的修改操作是线程安全的，避免了数据竞争和不一致的问题。而StringBuilder没有同步机制，在多线程环境下可能会导致不可预知的结果。TIPS： 如果需要在多线程环境下使用StringBuilder，可以通过外部同步机制（如使用锁）来保证线程安全，但这样会增加代码复杂性。<br>")
    if summary:
        print(f"总结: {summary}")

