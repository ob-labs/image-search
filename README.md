# Image Search Application

[中文版](./README_zh.md) | [日本語版](./README_ja.md)

## Introduction

With the vector storage and retrieval capabilities of OceanBase, we can build an image search application. The application will embed images into vectors and store them in the database. Users can upload images, and the application will search and return the most similar images in the database.

Note: You need to prepare some images yourself and update the `Image Base` configuration to the open UI. If you don't have any images available locally, you can download datasets online, such as the [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) dataset on Kaggle.

## System Architecture

The project consists of 4 core components:

- **Frontend (Streamlit UI)**: Responsible for image uploading, parameter configuration (e.g., top_k, search mode, distance_threshold), and result display.
- **Business Layer (OBImageStore)**: Encapsulates the core logic for dataset loading, multi-dimensional retrieval, and result fusion, coordinating all modules to complete search tasks.
- **Feature and Semantic Generation**:
  - **Image Vector (Embedding)**: Generates image vectors via DashScope Multimodal-Embedding API for similarity search.
  - **Image Description (Caption)**: Generates short text descriptions for images via an OpenAI-compatible interface for full-text and hybrid search.
- **Storage Layer (OceanBase / seekdb)**: Uses seekdb containers as the vector database by default; maintains both **vector indexes** and **caption full-text indexes**.

Below is a step-by-step explanation of "Dataset Loading / Image Search" (the standalone text-search UI is currently not exposed).

### 1) Dataset Loading

Usage: Select an image archive in the sidebar and click **Load Images**.

Dataset Loading Process:

1. **Decompression and Scanning**: Unzips the uploaded archive and scans for image files (supports jpg, jpeg, png formats).
2. **Step-by-Step Processing**:
   - **Read Image** and extract basic information.
   - **Generate Vector**: Creates an embedding for the image, used for subsequent similarity search.
   - **Generate Description**: Creates a short text description (Caption) for the image, used for subsequent text or hybrid search.
3. **Infrastructural Preparation**: Ensures the database table and its associated **vector index** (HNSW) and **full-text index** are ready, which is a prerequisite for efficient searching.
4. **Bulk Ingestion**: Batch writes image filenames, paths, descriptions, and vector features into OceanBase / seekdb.

Additional Notes:

- **make init creates tables/indexes**: The initialization script creates the table and the vector + caption full-text indexes; it skips if the table already exists.
- **Load process handles table creation as a fallback**: Even without running the creation command first, the business layer will check for table existence during the first ingestion and create it if missing.

### 2) Image Search

Usage: Upload an image and click search.

Search Process:

1. **Upload Image**: The frontend uploads the image as the search input.
2. **Generate Query Features**:
   - **Vector Feature**: Extracts the image's vector for similarity retrieval against images in the dataset.
   - **Text Feature**: Generates a text description (Caption) for the image for full-text retrieval in the database.
3. **Mode-based recall and ranking**:
   - **Full-text mode**: Recalls results only from the caption full-text index.
   - **Hybrid mode**: Uses both vector recall and full-text recall, then fuses/ranks results with pyseekdb native `hybrid_search` (RRF).
   - **Vector mode**: Uses vector similarity search only, and supports filtering by `distance_threshold`.
4. **Return Top K**: Outputs final Top K results.

## Quick Start (Recommended)

Use Docker Compose to start the application and database with one command.

### 1. Configure environment variables

```bash
cd docker
cp .env.example .env
```

Edit `docker/.env` file and configure the required settings:

```bash
# Image embedding API Key (required)
EMBEDDING_API_KEY=sk-your-dashscope-key

# Image captioning VLM API key (required for hybrid/full-text mode, optional for vector mode)
# Works with any OpenAI-compatible VLM provider.
VLM_API_KEY=sk-your-vlm-key
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Database selection (seekdb or oceanbase)
DB_STORE=seekdb
```

### 2. Start services

```bash
# Using seekdb (default, lower memory usage)
docker compose --profile seekdb up -d

# Or using oceanbase
docker compose --profile oceanbase up -d
```

### 3. Access the application

Open your browser and visit `http://localhost:8501`. Upload an image archive in the sidebar to load the dataset, then start searching.

### 4. Stop services

```bash
docker compose down
```

---

## Local Development Deployment

If you prefer to run directly in your local environment (without Docker), follow these steps.

### Prerequisites

1. Install [uv](https://github.com/astral-sh/uv) as a dependency management tool.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Make sure `make` is available on your system.

### 1. Set up environment variables

Copy the `.env.example` file to `.env` and modify the configuration as needed.

```bash
cp .env.example .env
```

**Important Configuration:**

- **EMBEDDING_API_KEY** (Required): API key for image embedding generation
  - Visit [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/apiKey) to get an API Key
- **VLM_API_KEY** (Required for hybrid/full-text mode): API key for image captioning
  - Not required if using vector mode only
  - Supports OpenAI, Qwen (Tongyi Qianwen), and other OpenAI-compatible services

Other configuration items (usually use default values):

- **EMBEDDING_TYPE**: Embedding backend type (default `dashscope`)
- **EMBEDDING_MODEL**: Embedding model name (default `tongyi-embedding-vision-plus`)
- **EMBEDDING_DIMENSION**: Vector dimension (default `1024`)
- **VLM_BASE_URL**: Image captioning API service endpoint (defaults to Qwen's service)
- **MODEL**: Image captioning model name (default `qwen-vl-max`)

Example configuration (`.env`):
```bash
# Required configuration
EMBEDDING_API_KEY=sk-your-dashscope-key
VLM_API_KEY=sk-your-vlm-key

# Optional configuration (use default values)
EMBEDDING_TYPE=dashscope
EMBEDDING_MODEL=tongyi-embedding-vision-plus
EMBEDDING_DIMENSION=1024
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-vl-max
```

### 2. Initialize the environment

This command will start the OceanBase database container and install all dependencies.

```bash
make init
```

### 3. Start the application

```bash
make start
```

### 4. Process and store images

After opening the application interface, you can see the input box of "Image Base" in the left sidebar. Fill in the absolute path of the image directory you prepared in it, and then click the "Load Images" button. The application will process and store these image data, and you will see the image processing progress on the interface.

### 5. Search for similar images

After the image processing is completed, you will see the image upload operation bar at the top of the interface. You can upload an image to search for similar images. Once the image is uploaded, the application will search and return some of the most similar images in the database, and by default, the top 10 most similar images will be returned.

![image_search_ui](./data/demo/image-search-demo.png)

## Other Commands

### Stop the application

```bash
make stop
```

### Clean up resources

```bash
make clean
```

## FAQ

### 1. What should I do if I encounter issues with Docker installation?

If you encounter any issues during Docker installation or when starting the OceanBase container, you can visit [OceanBase OBI](https://www.oceanbase.com/obi) for assistance.

