import os
import time
from pathlib import Path
import dotenv

dotenv.load_dotenv()

import streamlit as st
from image_search.image_store import OBImageStore
from image_search.connection import connection_args
from image_search.i18n import t
from image_search.utils import extract_bundle

base_dir = Path(__file__).resolve().parents[1]
data_dir = base_dir / "data"
demo_dir = data_dir / "demo"
tmp_dir = data_dir / "tmp"
tmp_path = tmp_dir / "temp.jpg"

if "archives" not in st.session_state:
    st.session_state.archives = {}

st.set_page_config(
    layout="wide",
    page_title=t("title"),
    page_icon=str(demo_dir / "ob-icon.png"),
)
st.title(t("title"))
st.caption(t("caption"))
os.makedirs(tmp_dir / "archives", exist_ok=True)
os.makedirs(tmp_dir / "extracted", exist_ok=True)

with st.sidebar:
    st.title(t("settings"))
    st.logo(str(demo_dir / "logo.png"))
    st.subheader(t("search_setting"))
    table_name = st.text_input(
        t("table_name_input"),
        os.getenv("IMG_TABLE_NAME", "image_search"),
        help=t("table_name_help"),
    )
    top_k = st.slider(t("recall_number"), 1, 30, 10, help=t("recall_number_help"))
    show_distance = st.checkbox(t("show_distance"), value=True)
    show_file_path = st.checkbox(t("show_file_path"), value=True)

    st.subheader(t("load_setting"))
    archive = st.file_uploader(
        t("upload_image_archive"),
        type=["zip", "tar", "tar.gz", "bz2", "xz"],
    )
    if archive is not None and archive.name not in st.session_state.archives:
        with open(tmp_dir / "archives" / archive.name, "wb") as f:
            f.write(archive.read())
            st.session_state.archives[archive.name] = True
            st.rerun()

    archives = os.listdir(tmp_dir / "archives")
    selected_archive = st.selectbox(
        t("image_archive"),
        help=t("image_archive_help"),
        options=archives,
        index=0,
        key="image_archive",
    )
    click_load = st.button(t("load_images"))

store = OBImageStore(
    uri=f"{connection_args['host']}:{connection_args['port']}",
    **connection_args,
)

table_exist = store.client.check_table_exists(table_name)
if not table_name or table_name.isspace():
    st.error(t("set_table_name_pls"))
    st.stop()
elif click_load:
    if not selected_archive:
        st.error(t("set_image_base_pls"))
    else:
        source = tmp_dir / "archives" / selected_archive
        target = tmp_dir / "extracted" / selected_archive
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
        st.rerun()
elif table_exist:
    uploaded_image = st.file_uploader(
        label=t("image_upload_label"),
        type=["jpg", "jpeg", "png"],
        help=t("image_upload_help"),
    )
    if uploaded_image is not None:
        col1, col2 = st.columns(2)
        col1.subheader(t("uploaded_image_header"))
        col1.caption(t("uploaded_image_caption"))
        col1.image(uploaded_image, use_column_width=True)

        with open(tmp_path, "wb") as f:
            f.write(uploaded_image.read())

        col2.subheader(t("similar_images_header"))
        results = store.search(str(tmp_path), limit=top_k, table_name=table_name)
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
else:
    st.warning(t("table_not_exist", table_name))
