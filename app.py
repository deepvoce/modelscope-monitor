from flask import Flask, render_template_string, request
import requests
import os

app = Flask(__name__)

# 通过环境变量配置 API Key，安全且可移植
MS_API_KEY = os.environ.get("MS_API_KEY", "")
if not MS_API_KEY:
    print("⚠️  警告: 未设置 MS_API_KEY 环境变量，请通过 export MS_API_KEY='your-token' 配置")

# 整合后的 HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
 <meta charset="UTF-8">
 <title>ModelScope 额度实战监控</title>
 <style>
 body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f9; margin: 0; padding: 40px; }
 .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
 h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
 
 .input-box { display: flex; gap: 10px; margin-bottom: 30px; }
 input[type="text"] { flex: 1; padding: 15px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; outline: none; transition: 0.3s; }
 input[type="text"]:focus { border-color: #3498db; }
 button { padding: 15px 30px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; }
 button:hover { background: #2980b9; }

 .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }
 .card { padding: 20px; border-radius: 10px; border-left: 5px solid; }
 .model-card { background: #fff4e6; border-left-color: #f39c12; }
 .account-card { background: #e8f4fd; border-left-color: #3498db; }
 
 .label { font-size: 14px; color: #7f8c8d; margin-bottom: 5px; }
 .value { font-size: 24px; font-weight: bold; color: #2c3e50; }
 .warning { color: #e74c3c; animation: blink 1s infinite; }
 @keyframes blink { 50% { opacity: 0.5; } }

 .response-title { font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
 .response-content { background: #2d3436; color: #dfe6e9; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-family: 'Courier New', monospace; }
 </style>
</head>
<body>
 <div class="container">
 <h1>🚀 API 额度实时探测</h1>
 
 <form method="POST">
 <div class="input-box">
 <input type="text" name="model_id" placeholder="粘贴模型 ID (例如: Qwen/Qwen3-235B-A22B-Instruct-2507)" required value="{{ model_id }}">
 <button type="submit">立即检查并执行</button>
 </div>
 </form>

 {% if limits %}
 <div class="grid">
 <div class="card model-card">
 <div class="label">模型当日总限额 (Limit)</div>
 <div class="value">{{ limits.get('model-limit', '---') }}</div>
 </div>
 <div class="card model-card">
 <div class="label">模型当日剩余 (Remaining)</div>
 <div class="value {% if limits.get('model-rem') == '0' %}warning{% endif %}">
 {{ limits.get('model-rem', '---') }}
 </div>
 </div>
 <div class="card account-card">
 <div class="label">账号当日总限额 (Limit)</div>
 <div class="value">{{ limits.get('user-limit', '---') }}</div>
 </div>
 <div class="card account-card">
 <div class="label">账号当日总剩余 (Remaining)</div>
 <div class="value">{{ limits.get('user-rem', '---') }}</div>
 </div>
 </div>

 <div class="response-title">️ 响应结果预览:</div>
 <div class="response-content">{{ content }}</div>
 {% endif %}
 </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    context = {"model_id": "", "limits": None, "content": ""}
    if request.method == 'POST':
        mid = request.form.get('model_id').strip()
        context["model_id"] = mid

        try:
            r = requests.post(
                "https://api-inference.modelscope.cn/v1/chat/completions",
                headers={"Authorization": f"Bearer {MS_API_KEY}"},
                json={"model": mid, "messages": [{"role": "user", "content": "你好"}], "max_tokens": 10},
                timeout=10
            )

            # 提取并翻译核心数据
            h = r.headers
            context["limits"] = {
                "model-limit": h.get('modelscope-ratelimit-model-requests-limit'),
                "model-rem": h.get('modelscope-ratelimit-model-requests-remaining'),
                "user-limit": h.get('modelscope-ratelimit-requests-limit'),
                "user-rem": h.get('modelscope-ratelimit-requests-remaining')
            }

            if r.status_code == 200:
                context["content"] = r.json()['choices'][0]['message']['content']
            else:
                context["content"] = f"请求返回异常 (HTTP {r.status_code}):\n{r.text}"

        except Exception as e:
            context["content"] = f"发生错误: {str(e)}"

    return render_template_string(HTML_TEMPLATE, **context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
