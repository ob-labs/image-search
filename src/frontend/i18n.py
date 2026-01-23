"""
Simple i18n helper with built-in translation dictionary.
"""

import os

from common.logger import get_logger

# Logger for i18n helpers
logger = get_logger(__name__)

# Translation table keyed by language code
tr = {
    "en": {
        "title": "🔍 Image Search",
        "caption": "🚀 Similar Image Search application built with vector retrieval feature of OceanBase database",
        "settings": "🔧 Settings",
        "search_setting": "Searching Setting",
        "table_name_input": "Table Name",
        "table_name_help": "Name of the table that stores image vectors and other data",
        "recall_number": "Recall Number",
        "recall_number_help": "How many similar images to return",
        "vector_weight": "Vector Weight",
        "vector_weight_help": "Weight of vector search: 0.0=text only, 1.0=vector only, 0.7=recommended",
        "distance_threshold": "Distance Threshold",
        "distance_threshold_help": "Only show results with distance <= this value",
        "show_distance": "Show Distance",
        "show_file_path": "Show File Path",
        "load_setting": "Loading Setting",
        "image_base_input": "Image Base",
        "image_base_help": "Absolute path of directory containing images to load",
        "image_base_placeholder": "Absolute path like /data/imgs",
        "load_images": "Load Images",
        "set_table_name_pls": "Set table name first please",
        "set_image_base_pls": "Set image base first please",
        "image_base_not_exist": "The image base directory you set ({}) does not exist",
        "images_loading": "Loading images...",
        "images_loading_progress": "Loading images... (Finished {} / {})",
        "images_loaded": "All images are loaded successfully!",
        "image_upload_label": "Choose an image to upload...",
        "image_upload_help": "Upload an image to search for similar images",
        "uploaded_image_header": "Upload Image",
        "uploaded_image_caption": "📌 Uploaded Image",
        "similar_images_header": "Similar Images",
        "no_similar_images": "No similar images found",
        "image_no": "Image {}",
        "distance": "📏 Distance:",
        "file_path": "📂 File path:",
        "image_caption": "📝 Description:",
        "table_not_exist": "The table {} does not exist, load images first please",
        "upload_image_archive": "Upload Image Archive",
        "image_archive": "Image Archive",
        "image_archive_help": "Select an image archive file and click Load Images to extract and load images",
    },
    "zh": {
        "title": "🔍 图像搜索应用",
        "caption": "🚀 基于 OceanBase 向量检索能力构建的相似图像搜索应用",
        "settings": "🔧 应用设置",
        "search_setting": "图片搜索设置",
        "table_name_input": "表名",
        "table_name_help": "用于存放图片的向量和其他数据的表名",
        "recall_number": "召回数量",
        "recall_number_help": "需要返回多少张相似照片",
        "vector_weight": "向量权重",
        "vector_weight_help": "向量检索权重：0.0=纯文本，1.0=纯向量，0.7=推荐",
        "distance_threshold": "距离阈值",
        "distance_threshold_help": "只显示距离小于等于该值的结果",
        "show_distance": "显示距离",
        "show_file_path": "显示文件路径",
        "load_setting": "图片加载设置",
        "image_base_input": "图片加载目录",
        "image_base_help": "需要加载的图片目录路径",
        "image_base_placeholder": "图片目录的绝对路径，如 /data/imgs",
        "load_images": "加载图片",
        "set_table_name_pls": "请设置表名",
        "set_image_base_pls": "请设置图片加载目录",
        "image_base_not_exist": "您设置的图片加载目录 {} 不存在",
        "images_loading": "图片加载中...",
        "images_loading_progress": "图片加载中... (已完成 {} / {})",
        "images_loaded": "所有图片加载完成！",
        "image_upload_label": "选择一张图片...",
        "image_upload_help": "上传一张图片以搜索相似图片",
        "uploaded_image_header": "上传图片",
        "uploaded_image_caption": "📌 您上传的图片",
        "similar_images_header": "相似图片",
        "no_similar_images": "没有找到相似图片",
        "image_no": "图片 {}",
        "distance": "📏 距离:",
        "file_path": "📂 文件路径:",
        "image_caption": "📝 描述:",
        "table_not_exist": "图片表 {} 不存在，请先加载图片",
        "upload_image_archive": "上传图片压缩包",
        "image_archive": "图片压缩包",
        "image_archive_help": "选中一个已上传的图片压缩包，点击加载图片来批量加载图片",
    },
    "ja": {
        "title": "🔍 画像検索アプリ",
        "caption": "🚀 OceanBase のベクトル検索機能で構築された類似画像検索アプリケーション",
        "settings": "🔧 設定",
        "search_setting": "検索設定",
        "table_name_input": "テーブル名",
        "table_name_help": "画像ベクトルなどを保存するテーブル名",
        "recall_number": "リコール数",
        "recall_number_help": "返す類似画像の枚数",
        "vector_weight": "ベクトル重み",
        "vector_weight_help": "ベクトル検索の重み：0.0=テキストのみ、1.0=ベクトルのみ、0.7=推奨",
        "distance_threshold": "距離しきい値",
        "distance_threshold_help": "距離がこの値以下の結果のみ表示",
        "show_distance": "距離を表示",
        "show_file_path": "ファイルパスを表示",
        "load_setting": "読み込み設定",
        "image_base_input": "画像ディレクトリ",
        "image_base_help": "読み込む画像ディレクトリのパス",
        "image_base_placeholder": "画像ディレクトリの絶対パス、例: /data/imgs",
        "load_images": "画像を読み込む",
        "set_table_name_pls": "テーブル名を設定してください",
        "set_image_base_pls": "画像ディレクトリを設定してください",
        "image_base_not_exist": "設定された画像ディレクトリ {} が存在しません",
        "images_loading": "画像を読み込んでいます...",
        "images_loading_progress": "画像を読み込んでいます... (完了 {} / {})",
        "images_loaded": "すべての画像が読み込まれました！",
        "image_upload_label": "画像を選択...",
        "image_upload_help": "類似画像を検索するために画像をアップロード",
        "uploaded_image_header": "アップロード画像",
        "uploaded_image_caption": "📌 アップロードされた画像",
        "similar_images_header": "類似画像",
        "no_similar_images": "類似画像が見つかりませんでした",
        "image_no": "画像 {}",
        "distance": "📏 距離:",
        "file_path": "📂 ファイルパス:",
        "image_caption": "📝 説明:",
        "table_not_exist": "画像テーブル {} が存在しません。先に画像を読み込んでください",
        "upload_image_archive": "画像圧縮ファイルをアップロード",
        "image_archive": "画像圧縮ファイル",
        "image_archive_help": "アップロードされた画像圧縮ファイルを選択し、画像を読み込むをクリックして一括読み込み",
    },
}

# Read UI language from env and fallback to zh
lang = os.getenv("UI_LANG", "zh")
if lang not in ["en", "zh", "ja"]:
    logger.warning("Invalid language %s, using default (zh).", lang)
    lang = "zh"


def t(key: str, *args) -> str:
    """
    Translate a key with optional format arguments.
    """
    if len(args) > 0:
        return tr[lang].get(key, "TODO: " + key).format(*args)
    return tr[lang].get(key, "TODO: " + key)
