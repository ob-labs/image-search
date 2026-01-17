# Image Search Application

[中文版](./README_zh.md)

## Introduction

With the vector storage and retrieval capabilities of OceanBase, we can build an image search application. The application will embed images into vectors and store them in the database. Users can upload images, and the application will search and return the most similar images in the database.

Note: You need to prepare some images yourself and update the `Image Base` configuration to the open UI. If you don't have any images available locally, you can download datasets online, such as the [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) dataset on Kaggle.

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

