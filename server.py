"""
Flask REST API服务器
提供B站视频总结的HTTP接口
"""
import asyncio
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import BiliSummary

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS

# 初始化BiliSummary（全局单例）
bili_summary = None

def get_bili_summary():
    """获取或创建BiliSummary实例"""
    global bili_summary
    if bili_summary is None:
        bili_summary = BiliSummary()
    return bili_summary

@app.route('/api/summary_bili', methods=['POST'])
def summary_bili():
    """
    B站视频总结接口
    
    请求格式：
    {
        "url": "https://www.bilibili.com/video/BV..."
    }
    
    响应格式：
    {
        "success": true,
        "summary": "视频总结内容..."
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': '请求参数错误：缺少url字段'
            }), 400
        
        video_url = data['url']
        
        # 验证URL格式
        if not video_url.startswith('https://www.bilibili.com/video'):
            return jsonify({
                'success': False,
                'error': 'URL格式错误：必须是B站视频链接'
            }), 400
        
        logger.info(f"收到总结请求: {video_url}")
        
        # 处理视频总结（异步转同步）
        summary_tool = get_bili_summary()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        summary = loop.run_until_complete(
            summary_tool.process_video(video_url)
        )
        loop.close()
        
        if summary:
            logger.info("总结生成成功")
            return jsonify({
                'success': True,
                'summary': summary
            })
        else:
            logger.error("总结生成失败")
            return jsonify({
                'success': False,
                'error': '总结生成失败，请检查视频链接或稍后重试'
            }), 500
            
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # 使用Uvicorn运行（需要ASGI适配器）
    import uvicorn
    from asgiref.wsgi import WsgiToAsgi
    
    asgi_app = WsgiToAsgi(app)
    logger.info("启动服务器 http://localhost:5000")
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000)

