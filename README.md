# YouTube Data Tool

一个基于FastAPI的YouTube数据分析工具，提供视频信息获取、摘要生成等功能。

## 功能特点

- 获取YouTube视频详细信息
- 生成视频内容摘要
- 获取频道信息
- RESTful API接口
- 异步处理支持
- 完整的API文档

## 技术栈

- FastAPI
- Pydantic
- Google YouTube API
- Redis
- PostgreSQL

## 快速开始

1. 克隆项目
```bash
git clone https://github.com/yourusername/youtube-data-tool.git
cd youtube-data-tool
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

5. 运行服务
```bash
uvicorn app.main:app --reload
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
app/
├── api/
│   └── endpoints/
│       └── youtube.py
├── core/
│   └── config.py
├── models/
│   └── youtube.py
├── services/
│   └── youtube_service.py
├── utils/
└── main.py
```

## 开发指南

1. 代码风格遵循PEP 8规范
2. 使用类型注解
3. 编写单元测试
4. 保持文档更新

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT