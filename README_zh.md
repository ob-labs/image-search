# 图像搜索应用

[English Edition](./README.md) | [日本語版](./README_ja.md)

## 介绍

凭借 OceanBase 的向量存储和检索能力，我们可以构建一个图像搜索应用。该应用会把图像嵌入为向量并存储在数据库中。用户可以上传图像，应用程序将搜索并返回数据库中最相似的图像。

注意：您需要自己准备一些图像并将 `Image Base` 配置更新到打开的 UI 中。如果您本地没有可用的图像，可以在线下载数据集，例如在 Kaggle 上的 [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) 数据集。

## 准备工作

1. 安装 [uv](https://github.com/astral-sh/uv) 作为依赖管理工具。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 确保系统中 `make` 命令可用。

## 应用搭建步骤

### 1. 配置环境变量

将 `.env.example` 文件复制为 `.env` 并根据需要修改配置。

```bash
cp .env.example .env
```

**重要配置项：**

- **API_KEY**（全文/混合搜索必需）：用于图像自动描述功能的 API 密钥
  - 如果只使用纯向量搜索（向量权重=1.0），则不需要配置
  - 使用文本或混合搜索（向量权重<1.0）时必须配置
  - 支持 OpenAI、Qwen（通义千问）等兼容 OpenAI API 的服务
  - Qwen API 获取方式：访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/apiKey) 获取 API Key
- **BASE_URL**：API 服务地址（默认为 Qwen 的服务地址）
- **MODEL**：使用的模型名称（默认为 `qwen-vl-max`）

示例配置（`.env`）：
```bash
API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-vl-max
```

### 2. 初始化环境

该命令将启动 OceanBase 数据库容器并安装所有依赖。

```bash
make init
```

### 3. 启动应用

```bash
make start
```

### 4. 处理并存储图像数据

打开应用界面之后，您可以在左侧侧边栏中看到"Image Base"的输入框，在其中填写您准备的图片目录的绝对路径，然后点击"Load Images"按钮。应用程序将处理并存储这些图像数据，您将在界面上看到图片处理进度。

### 5. 使用图像搜索

在图片处理完成后，您将在界面中上方看到图片上传操作栏，您可上传一张图片用于搜索相似图片。上传图片后，应用程序将搜索并返回数据库中最相似的一些图片，默认返回最相似的前 10 张图片。

![image_search_ui](./data/demo/image-search-demo.png)

## 其他命令

### 停止应用

```bash
make stop
```

### 清理资源

```bash
make clean
```

## 常见问题

### 1. 遇到找不到 libGL.so.1 文件的报错怎么办？

如果您在运行应用 UI 时遇到了 `ImportError: libGL.so.1: cannot open shared object file` 的报错信息，可参考[该帖子](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo)解决。

在 CentOS/RedHat 操作系统中，执行以下命令：

```bash
sudo yum install mesa-libGL -y
```

在 Ubuntu/Debian 操作系统中，执行以下命令：

```bash
sudo apt-get install libgl1
```

### 2. Docker 安装遇到问题怎么办？

如果您在安装 Docker 或启动 OceanBase 容器时遇到任何问题，可以访问 [OceanBase OBI](https://www.oceanbase.com/obi) 寻求帮助。
