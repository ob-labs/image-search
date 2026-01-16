# Image Search Application

[中文版](./README_zh.md)

## Introduction

With the vector storage and retrieval capabilities of OceanBase, we can build an image search application. The application will embed images into vectors and store them in the database. Users can upload images, and the application will search and return the most similar images in the database.

Note: You need to prepare some images yourself and update the `Image Base` configuration to the open UI. If you don't have any images available locally, you can download datasets online, such as the [Animals-10](https://www.kaggle.com/datasets/alessiocorrado99/animals10/data) dataset on Kaggle.

## Prerequisites

1. Install [Python 3.9](https://www.python.org/downloads/) and above versions and the corresponding [Pip](https://pip.pypa.io/en/stable/installation/) tool.

2. Install [Docker](https://docs.docker.com/get-docker/) to start the OceanBase database container.

3. Install [Poetry](https://python-poetry.org/docs/) as a dependency management tool, you can refer to the following command,

```bash
python3 -m pip install poetry
```

4. Obtain the database connection information of OceanBase 4.3.3 and above versions. If you do not plan to deploy OceanBase locally, you can refer to the OceanBase [open source version deployment solution](https://open.oceanbase.com/quickStart) or [OceanBase Cloud](https://www.oceanbase.com/free-trial) solution.

## Build Steps

### 1. Deploy an OceanBase Cluster

#### 1.1 Start an OceanBase docker container

If you are the first time to login to the machine provided by the workshop, you need to start the docker service with the following command:

```bash
systemctl start docker
```

And then, you can start an OceanBase docker container with the following command:

```bash
docker run --ulimit stack=4294967296 --name=ob433 -e MODE=mini -e OB_MEMORY_LIMIT=8G -e OB_DATAFILE_SIZE=10G -e OB_CLUSTER_NAME=ailab2024 -p 127.0.0.1:2881:2881 -d quay.io/oceanbase/oceanbase-ce:4.3.3.0-100000142024101215
```

If the above command is executed successfully, you will see the following output:

```bash
af5b32e79dc2a862b5574d05a18c1b240dc5923f04435a0e0ec41d70d91a20ee
```

#### 1.2 Check the bootstrap of OceanBase is complete

After the container is started, you can check the bootstrap status of OceanBase with the following command:

```bash
docker logs -f ob433
```

The initialization will take about 2 ~ 3 minutes. When you see the following message (the bottom `boot success!` is essential), the bootstrap of OceanBase is complete:

```bash
cluster scenario: express_oltp
Start observer ok
observer program health check ok
Connect to observer ok
Initialize oceanbase-ce ok
Wait for observer init ok
+----------------------------------------------+
|                 oceanbase-ce                 |
+------------+---------+------+-------+--------+
| ip         | version | port | zone  | status |
+------------+---------+------+-------+--------+
| 172.17.0.2 | 4.3.3.0 | 2881 | zone1 | ACTIVE |
+------------+---------+------+-------+--------+
obclient -h172.17.0.2 -P2881 -uroot -Doceanbase -A

cluster unique id: c17ea619-5a3e-5656-be07-00022aa5b154-19298807cfb-00030304

obcluster running
Trace ID: 08f99c98-8c37-11ef-ad07-0242ac110002
If you want to view detailed obd logs, please run: obd display-trace 08f99c98-8c37-11ef-ad07-0242ac110002
Get local repositories and plugins ok
Open ssh connection ok
Connect to observer ok
Create tenant test ok
Exec oceanbase-ce-4.3.3.0-100000142024101215.el8-3eee13839888800065c13ffc5cd7c3e6b12cb55c import_time_zone_info.py ok
Exec oceanbase-ce-4.3.3.0-100000142024101215.el8-3eee13839888800065c13ffc5cd7c3e6b12cb55c import_srs_data.py ok
obclient -h172.17.0.2 -P2881 -uroot@test -Doceanbase -A

optimize tenant with scenario: express_oltp ok
Trace ID: 3c50193c-8c37-11ef-ace2-0242ac110002
If you want to view detailed obd logs, please run: obd display-trace 3c50193c-8c37-11ef-ace2-0242ac110002
check tenant connectable
tenant is connectable
boot success!
```

Type `Ctrl+C` to exit the log view.

#### 1.3 Test deployment (Optional)

Connect to the OceanBase cluster with mysql client to check the deployment.

```bash
mysql -h127.0.0.1 -P2881 -uroot@test -A -e "show databases"
```

If the deployment is successful, you will see the following output:

```bash
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| oceanbase          |
| test               |
+--------------------+
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Set up environment variables

We provide the `.env.example` file, you need to copy it to the `.env` file and fill in your database connection information. You can refer to the following command,

```bash
cp .env.example .env
# Modify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME in the .env file
vi .env
```

### 4. Start the image search application

```bash
poetry run streamlit run --server.runOnSave false frontend/streamlit_app.py
```

### 5. Process and store images

After opening the application interface, you can see the input box of "Image Base" in the left sidebar. Fill in the absolute path of the image directory you prepared in it, and then click the "Load Images" button. The application will process and store these image data, and you will see the image processing progress on the interface.

### 6. Search similar images

After the image processing is completed, you will see the image upload operation bar at the top of the interface. You can upload an image to search for similar images. Once the image is uploaded, the application will search and return some of the most similar images in the database, and by default, the top 10 most similar images will be returned.

![image_search_ui](./data/demo/image-search-demo.png)

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

### 2. What should I do if I encounter an error that pkg_resources cannot be found?

If you encounter the error message `ModuleNotFoundError: No module named 'pkg_resources'` when running the application UI, you can refer to [this post](https://stackoverflow.com/questions/7446187/no-module-named-pkg-resources) to resolve it.

Specifically, you can refer to the following two commands,

```bash
python3 -m pip install --upgrade pip
python3 -m pip install setuptools
```
