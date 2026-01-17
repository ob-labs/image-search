"""
Streamlit frontend for loading and searching images.
"""

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from common.db import build_client
from common.image_store import OBImageStore
from common.logger import get_logger
from common.compress import extract_bundle
from frontend.i18n import t

# Logger for Streamlit app
logger = get_logger(__name__)

# Load environment variables for configuration
load_dotenv()
logger.info("Environment variables loaded for frontend.")

@dataclass(frozen=True)
class AppPaths:
    base_dir: Path
    data_dir: Path
    demo_dir: Path
    tmp_dir: Path
    tmp_path: Path
    archives_dir: Path
    extracted_dir: Path
    icon_path: Path
    logo_path: Path


def build_paths() -> AppPaths:
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data"
    demo_dir = data_dir / "demo"
    tmp_dir = data_dir / "tmp"
    logger.info("Resolved base paths under %s.", base_dir)
    return AppPaths(
        base_dir=base_dir,
        data_dir=data_dir,
        demo_dir=demo_dir,
        tmp_dir=tmp_dir,
        tmp_path=tmp_dir / "temp.jpg",
        archives_dir=tmp_dir / "archives",
        extracted_dir=tmp_dir / "extracted",
        icon_path=demo_dir / "ob-icon.png",
        logo_path=demo_dir / "logo.png",
    )


def configure_page(paths: AppPaths) -> None:
    page_icon = "🔍"
    if paths.icon_path.exists():
        page_icon = str(paths.icon_path.resolve())

    page_title_text = re.sub(r'[\U0001F300-\U0001F9FF]', '', t("title")).strip()
    st.set_page_config(
        layout="wide",
        page_title=page_title_text,
        page_icon=page_icon,
    )
    logger.info("Streamlit page configured.")


def render_header() -> None:
    st.title(t("title"))
    st.caption(t("caption"))


def ensure_temp_dirs(paths: AppPaths) -> None:
    os.makedirs(paths.archives_dir, exist_ok=True)
    os.makedirs(paths.extracted_dir, exist_ok=True)
    logger.info("Temp directories ensured.")


def ensure_session_state() -> None:
    if "archives" not in st.session_state:
        st.session_state.archives = {}
        logger.info("Session state initialized for archives.")


def persist_archive_upload(uploaded_file, paths: AppPaths) -> None:
    if uploaded_file is None:
        return
    if uploaded_file.name in st.session_state.archives:
        return
    archive_path = paths.archives_dir / uploaded_file.name
    with open(archive_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state.archives[uploaded_file.name] = True
    logger.info("Archive uploaded: %s", uploaded_file.name)
    st.rerun()


def render_sidebar_logo(paths: AppPaths) -> None:
    if paths.logo_path.exists():
        st.logo(paths.logo_path)


def render_sidebar_inputs(paths: AppPaths) -> tuple[str, int, bool, bool, str, bool]:
    st.title(t("settings"))
    st.subheader(t("search_setting"))
    table_name = os.getenv("IMG_TABLE_NAME", "image_search")
    top_k = st.slider(t("recall_number"), 1, 30, 10, help=t("recall_number_help"))
    show_distance = st.checkbox(t("show_distance"), value=True)
    show_file_path = st.checkbox(t("show_file_path"), value=True)

    st.subheader(t("load_setting"))
    archive = st.file_uploader(
        t("upload_image_archive"),
        type=["zip", "tar", "tar.gz", "bz2", "xz"],
    )
    persist_archive_upload(archive, paths)

    archives = os.listdir(paths.archives_dir)
    selected_archive = st.selectbox(
        t("image_archive"),
        help=t("image_archive_help"),
        options=archives,
        index=0,
        key="image_archive",
    )
    click_load = st.button(t("load_images"))
    return table_name, top_k, show_distance, show_file_path, selected_archive, click_load


def load_images_from_archive(
    store: OBImageStore,
    selected_archive: str,
    table_name: str,
    paths: AppPaths,
) -> None:
    source = paths.archives_dir / selected_archive
    target = paths.extracted_dir / selected_archive
    logger.info("Loading archive %s into %s", source, target)
    extract_bundle(str(source), str(target))
    total = store.load_amount(str(target))
    finished = 0
    bar = st.progress(0, text=t("images_loading"))
    for _ in store.load_image_dir(str(target), table_name=table_name):
        finished += 1
        bar.progress(
            finished / total,
            text=t("images_loading_progress", finished, total),
        )
    st.toast(t("images_loaded"), icon="🎉")
    st.balloons()
    time.sleep(2)
    logger.info("Image loading completed: %s images.", total)
    st.rerun()


def render_search_results(
    store: OBImageStore,
    uploaded_image,
    table_name: str,
    top_k: int,
    show_distance: bool,
    show_file_path: bool,
    tmp_path: Path,
) -> None:
    col1, col2 = st.columns(2)
    col1.subheader(t("uploaded_image_header"))
    col1.caption(t("uploaded_image_caption"))
    col1.image(uploaded_image)

    with open(tmp_path, "wb") as f:
        f.write(uploaded_image.read())

    col2.subheader(t("similar_images_header"))
    results = store.search(str(tmp_path), limit=top_k, table_name=table_name)
    logger.info("Search returned %s results.", len(results))
    with col2:
        if len(results) == 0:
            st.warning(t("no_similar_images"))
        else:
            tabs = st.tabs([t("image_no", i + 1) for i in range(len(results))])
            for res, tab in zip(results, tabs):
                with tab:
                    if show_distance:
                        st.write(t("distance"), f"{res['distance']:.8f}")
                    if show_file_path:
                        st.write(t("file_path"), os.path.join(res["file_path"]))
                    st.image(res["file_path"])


def init_store() -> OBImageStore:
    logger.info("Initializing image store for frontend.")
    return OBImageStore(
        client=build_client(),
    )


def render_search_panel(
    store: OBImageStore,
    table_name: str,
    top_k: int,
    show_distance: bool,
    show_file_path: bool,
    tmp_path: Path,
) -> None:
    uploaded_image = st.file_uploader(
        label=t("image_upload_label"),
        type=["jpg", "jpeg", "png"],
        help=t("image_upload_help"),
    )
    if uploaded_image is not None:
        render_search_results(
            store,
            uploaded_image,
            table_name,
            top_k,
            show_distance,
            show_file_path,
            tmp_path,
        )


def main() -> None:
    paths = build_paths()
    configure_page(paths)
    ensure_session_state()
    ensure_temp_dirs(paths)
    render_header()
    logger.info("Streamlit main flow started.")

    with st.sidebar:
        render_sidebar_logo(paths)
        (
            table_name,
            top_k,
            show_distance,
            show_file_path,
            selected_archive,
            click_load,
        ) = render_sidebar_inputs(paths)

    store = init_store()

    table_exist = store.client.check_table_exists(table_name)
    if click_load:
        if not selected_archive:
            st.error(t("set_image_base_pls"))
            logger.warning("Load clicked but no archive selected.")
        else:
            load_images_from_archive(store, selected_archive, table_name, paths)
    elif table_exist:
        render_search_panel(
            store,
            table_name,
            top_k,
            show_distance,
            show_file_path,
            paths.tmp_path,
        )
    else:
        st.warning(t("table_not_exist", table_name))
        logger.warning("Table %s does not exist.", table_name)


main()
