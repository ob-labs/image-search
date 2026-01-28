# Image Search Application

[中文版](./README_zh.md) | [日本語版](./README_ja.md)

## Introduction

With the vector storage and retrieval capabilities of OceanBase, we can build an image search application. The application will embed images into vectors and store them in the database. Users can upload images, and the application will search and return the most similar images in the database.

Note: You need to prepare some images yourself and update the `Image Base` configuration to the open UI. If you don't have any images available locally, you can download datasets online, such as the [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) dataset on Kaggle.

## System Architecture

The project consists of 4 core components:

- **Frontend (Streamlit UI)**: Responsible for image uploading, parameter configuration (e.g., top_k, vector_weight, distance_threshold), and result display.
- **Business Layer (OBImageStore)**: Encapsulates the core logic for dataset loading, multi-dimensional retrieval, and result fusion, coordinating all modules to complete search tasks.
- **Feature and Semantic Generation**:
  - **Image Vector (Embedding)**: Generates image vectors for similarity search (prioritizes Towhee, falls back to local CLIP if needed).
  - **Image Description (Caption)**: Generates short text descriptions for images via an OpenAI-compatible interface for full-text and hybrid search.
- **Storage Layer (OceanBase / seekdb)**: Uses seekdb containers as the vector database by default; maintains both **vector indexes** and **caption full-text indexes**.

Below is a step-by-step explanation of "Dataset Loading / Image Search / Text Search".

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
3. **Dual-Path Recall**:
   - **Vector Recall**: Performs similarity search via the vector index, supporting filtering of irrelevant results through `distance_threshold`.
   - **Text Recall**: Matches via the caption full-text index to recall semantically relevant images.
4. **Fusion and Ranking**: Normalizes results from both paths and performs weighted ranking based on the user-defined `vector_weight` to output the final Top K results.

### 3) Text Search

Usage: Enter a text query and click search.

Search Process:

1. **Enter Text**: User enters search keywords.
2. **Full-Text Retrieval**: The system leverages OceanBase / seekdb's full-text retrieval capabilities to match and recall images based on the Caption field.
3. **Result Ranking**: Ranks results based on text relevance scores and outputs the final Top K results.

## Prerequisites

1. Install [uv](https://github.com/astral-sh/uv) as a dependency management tool.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Make sure `make` is available on your system.

## Build Steps

### 1. Set up environment variables

Copy the `.env.example` file to `.env` and modify the configuration as needed.

```bash
cp .env.example .env
```

**Important Configuration:**

- **API_KEY** (Required for text/hybrid search): API key for automatic image captioning
  - Not required if using pure vector search only (vector weight = 1.0)
  - Required when using text or hybrid search (vector weight < 1.0)
  - Supports OpenAI, Qwen (Tongyi Qianwen), and other OpenAI-compatible services
  - For Qwen API: Visit [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/apiKey) to get an API Key
- **BASE_URL**: API service endpoint (defaults to Qwen's service)
- **MODEL**: Model name to use (defaults to `qwen-vl-max`)

Example configuration (`.env`):
```bash
API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
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

### 5. Search similar images

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

### 1. What should I do if I encounter an error that libGL.so.1 cannot be found?

If you encounter the error message `ImportError: libGL.so.1: cannot open shared object file` when running the application UI, you can refer to [this post](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo) to resolve it.

If you are using the CentOS/RedHat operating system, execute the following command,

```bash
sudo yum install mesa-libGL -y
```

And if you are using the Ubuntu/Debian operating system, execute the following command,

```bash
sudo apt-get install libgl1
```

### 2. What should I do if I encounter issues with Docker installation?

If you encounter any issues during Docker installation or when starting the OceanBase container, you can visit [OceanBase OBI](https://www.oceanbase.com/obi) for assistance.

