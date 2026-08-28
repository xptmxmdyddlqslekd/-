import streamlit as st
import pandas as pd
import math

# 페이지 기본 설정
st.set_page_config(page_title="작가와의 만남 통합 검색", layout="wide", page_icon="📚")

# ---------------------------------------------------------
# 한글 초성 검색용 함수
# ---------------------------------------------------------
CHO_LIST = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ',
    'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]

def get_chosung(text):
    result = []
    for char in str(text):
        if '가' <= char <= '힣':
            code = ord(char) - 44032
            cho_idx = code // 588
            result.append(CHO_LIST[cho_idx])
        else:
            result.append(char)
    return "".join(result)

def is_chosung_query(query):
    return all(c in CHO_LIST or c.isspace() for c in query)

# ---------------------------------------------------------
# 데이터 로드
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("integrated_author_events.csv")
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"데이터 파일(integrated_author_events.csv)을 불러오지 못했습니다: {e}")
        return pd.DataFrame()

df = load_data()

# Session State 초기화
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# ---------------------------------------------------------
# 메인 화면
# ---------------------------------------------------------
st.title("📚 작가와의 만남 통합 검색 서비스")
st.caption("출판사, 강연 대상, 세부 학년, 주제별로 원하시는 작가 강연을 손쉽게 찾아보세요.")

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["🔍 강연 검색하기", "⭐ 내 보관함", "📄 원본 데이터 보기 및 다운로드"])

    # ==================== TAB 1: 강연 검색 ====================
    with tab1:
        # --- 사이드바 필터 ---
        st.sidebar.header("🎛️ 조건별 필터")

        if st.sidebar.button("🔄 모든 필터 초기화", use_container_width=True):
            st.session_state.clear()
            st.session_state.current_page = 1
            st.session_state.bookmarks = []
            st.rerun()

        st.sidebar.markdown("---")

        all_publishers = sorted([p for p in df["출판사"].unique() if p])
        selected_publisher = st.sidebar.multiselect(
            "🏢 출판사 선택 (선택 안 함 = 전체)",
            options=all_publishers,
            default=[],
            key="filter_pub"
        )

        target_options = ["유아", "저학년", "중학년", "고학년", "초등", "청소년", "성인", "교사"]
        selected_targets = st.sidebar.multiselect(
            "🎯 강연 대상 선택",
            options=target_options,
            default=[],
            key="filter_target"
        )

        topic_options = ["그림책", "문학", "창작", "교양/문화", "사회", "인문", "과학", "환경", "역사"]
        selected_topics = st.sidebar.multiselect(
            "🏷️ 주요 주제 선택",
            options=topic_options,
            default=[],
            key="filter_topic"
        )

        methods = ["전체", "비대면", "대면"]
        selected_method = st.sidebar.radio("💻 강연 방식", options=methods, index=0, key="filter_method")

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💌 제보 및 문의")
        st.sidebar.caption("수정 사항이나 신규 강연 제보가 있다면 알려주세요.")
        st.sidebar.markdown("[👉 강연 정보 제보/수정 요청](https://forms.google.com)", unsafe_allow_html=True)

        # --- 메인 검색창 ---
        st.markdown("### 🔎 키워드 직접 검색")
        search_query = st.text_input(
            "작가명, 도서/강연 제목, 주제어 또는 초성(예: ㄱㄱㅅ, ㅂㅎㄴ)으로 검색하세요",
            "",
            key="search_input"
        )

        filtered_df = df.copy()

        if selected_publisher:
            filtered_df = filtered_df[filtered_df["출판사"].isin(selected_publisher)]

        if selected_targets:
            target_pattern = "|".join(selected_targets)
            filtered_df = filtered_df[filtered_df["대상"].str.contains(target_pattern, na=False)]

        if selected_topics:
            topic_pattern = "|".join(selected_topics)
            filtered_df = filtered_df[filtered_df["주제/소개"].str.contains(topic_pattern, na=False)]

        if selected_method != "전체":
            filtered_df = filtered_df[filtered_df["강연방식"].str.contains(selected_method, na=False)]

        if search_query.strip():
            q = search_query.strip()
            if is_chosung_query(q):
                filtered_df["작가_초성"] = filtered_df["작가"].apply(get_chosung)
                filtered_df["제목_초성"] = filtered_df["도서/강연제목"].apply(get_chosung)
                
                filtered_df = filtered_df[
                    filtered_df["작가_초성"].str.contains(q, case=False, na=False) |
                    filtered_df["제목_초성"].str.contains(q, case=False, na=False)
                ]
            else:
                filtered_df = filtered_df[
                    filtered_df["작가"].str.contains(q, case=False, na=False) |
                    filtered_df["도서/강연제목"].str.contains(q, case=False, na=False) |
                    filtered_df["주제/소개"].str.contains(q, case=False, na=False) |
                    filtered_df["대상"].str.contains(q, case=False, na=False)
                ]

        st.markdown("---")
        
        if len(filtered_df) == 0:
            st.subheader("총 0건의 강연이 검색되었습니다.")
            st.info("검색 조건에 일치하는 결과가 없습니다. 필터를 조정해 보세요.")
        else:
            top_col1, top_col2 = st.columns([3, 2])
            with top_col1:
                st.subheader(f"총 {len(filtered_df):,}건의 강연이 검색되었습니다.")
            
            with top_col2:
                view_mode = st.radio(
                    "📱 보기 방식 선택",
                    ["📋 한눈에 보기 (엑셀 표 형태)", "🎴 상세 보기 (카드 형태)"],
                    horizontal=True,
                    key="view_mode"
                )

            # ==================== [MODE 1] 표 형태 ====================
            if "표 형태" in view_mode:
                st.markdown("##### 💡 검색된 결과를 엑셀처럼 한눈에 조회합니다.")
                
                # 이미지URL 컬럼이 있으면 표에 추가
                display_cols = ["도서/강연제목", "작가", "출판사", "대상", "강연방식", "주제/소개", "상세페이지"]
                if "이미지URL" in filtered_df.columns:
                    display_cols.insert(0, "이미지URL")

                show_df = filtered_df[display_cols].reset_index(drop=True)

                col_config = {
                    "상세페이지": st.column_config.LinkColumn("상세페이지 링크", display_text="👉 신청하기")
                }
                if "이미지URL" in show_df.columns:
                    col_config["이미지URL"] = st.column_config.ImageColumn("표지", help="도서 표지 썸네일")

                st.dataframe(
                    show_df,
                    use_container_width=True,
                    height=550,
                    column_config=col_config
                )

            # ==================== [MODE 2] 카드 형태 ====================
            else:
                items_per_page = 10
                total_pages = math.ceil(len(filtered_df) / items_per_page)

                if st.session_state.current_page > total_pages:
                    st.session_state.current_page = 1

                head_col1, head_col2 = st.columns([3, 1])
                with head_col1:
                    st.caption(f"페이지 {st.session_state.current_page} / {total_pages}")
                
                with head_col2:
                    target_p = st.number_input(
                        "🎯 페이지 바로 이동", 
                        min_value=1, 
                        max_value=total_pages, 
                        value=st.session_state.current_page,
                        step=1,
                        key="direct_page_input"
                    )
                    if target_p != st.session_state.current_page:
                        st.session_state.current_page = target_p
                        st.rerun()

                start_idx = (st.session_state.current_page - 1) * items_per_page
                end_idx = start_idx + items_per_page

                current_batch = filtered_df.iloc[start_idx:end_idx]

                for idx, row in current_batch.iterrows():
                    with st.container():
                        st.markdown(f"#### 📖 {row['도서/강연제목']}")
                        
                        # 표지 이미지 유무에 따른 컬럼 레이아웃 분기
                        has_img = "이미지URL" in row and str(row['이미지URL']).startswith("http")
                        
                        if has_img:
                            img_col, col1, col2, col3, col4 = st.columns([1, 2.5, 2, 1.2, 1])
                            with img_col:
                                st.image(row['이미지URL'], width=90)
                        else:
                            col1, col2, col3, col4 = st.columns([2.5, 2, 1.2, 1])

                        with col1:
                            st.write(f"**✍️ 작가:** {row['작가'] if row['작가'] else '미기재'}")
                            st.write(f"**🏢 출판사:** {row['출판사']}")
                        with col2:
                            st.write(f"**🎯 대상:** {row['대상'] if row['대상'] else '전체/미지정'}")
                            st.write(f"**💻 강연 방식:** {row['강연방식'] if row['강연방식'] else '대면'}")
                        with col3:
                            url = str(row['상세페이지']).strip()
                            if url and url.startswith("http"):
                                st.link_button("👉 상세/신청", url)
                            else:
                                st.caption("상세링크 없음")
                        with col4:
                            item_id = f"{row['출판사']}_{row['작가']}_{row['도서/강연제목']}"
                            is_bookmarked = item_id in [b.get('id') for b in st.session_state.bookmarks]
                            
                            btn_label = "⭐ 보관됨" if is_bookmarked else "☆ 보관하기"
                            if st.button(btn_label, key=f"bm_{idx}"):
                                if is_bookmarked:
                                    st.session_state.bookmarks = [b for b in st.session_state.bookmarks if b.get('id') != item_id]
                                else:
                                    st.session_state.bookmarks.append({
                                        "id": item_id,
                                        "제목": row['도서/강연제목'],
                                        "작가": row['작가'],
                                        "출판사": row['출판사'],
                                        "대상": row['대상'],
                                        "강연방식": row['강연방식'],
                                        "상세페이지": row['상세페이지']
                                    })
                                st.rerun()

                        if row['주제/소개']:
                            st.caption(f"💡 주제/소개: {row['주제/소개']}")
                        
                        st.divider()

                # 하단 페이지 1~10 단추
                st.markdown("<br>", unsafe_allow_html=True)
                max_visible_buttons = 10
                curr = st.session_state.current_page
                
                start_page = max(1, curr - max_visible_buttons // 2)
                end_page = min(total_pages, start_page + max_visible_buttons - 1)
                if end_page - start_page + 1 < max_visible_buttons:
                    start_page = max(1, end_page - max_visible_buttons + 1)

                btn_cols = st.columns(end_page - start_page + 3)

                with btn_cols[0]:
                    if st.button("◀ 이전", disabled=(curr == 1)):
                        st.session_state.current_page -= 1
                        st.rerun()

                for i, p_num in enumerate(range(start_page, end_page + 1)):
                    with btn_cols[i + 1]:
                        is_current = (p_num == curr)
                        label = f"**[{p_num}]**" if is_current else f"{p_num}"
                        if st.button(label, key=f"page_btn_{p_num}"):
                            st.session_state.current_page = p_num
                            st.rerun()

                with btn_cols[-1]:
                    if st.button("다음 ▶", disabled=(curr == total_pages)):
                        st.session_state.current_page += 1
                        st.rerun()

    # ==================== TAB 2: 내 보관함 ====================
    with tab2:
        st.markdown("### ⭐ 관심 강연 보관함")
        st.write("검색하며 담아둔 강연 목록입니다. 보고서 작성이나 인쇄용으로 활용하세요.")

        if not st.session_state.bookmarks:
            st.info("아직 보관된 강연이 없습니다. 검색 결과에서 보관하기 버튼을 눌러보세요.")
        else:
            bm_df = pd.DataFrame(st.session_state.bookmarks)
            
            col_b1, col_b2 = st.columns([1, 4])
            with col_b1:
                if st.button("🗑️ 전체 비우기"):
                    st.session_state.bookmarks = []
                    st.rerun()

            st.markdown("---")
            for b_idx, b_item in enumerate(st.session_state.bookmarks):
                st.markdown(f"**{b_idx+1}. 《{b_item['제목']}》 - {b_item['작가']} 작가**")
                st.write(f"- 출판사: {b_item['출판사']} | 대상: {b_item['대상']} | 방식: {b_item['강연방식']}")
                if b_item['상세페이지']:
                    st.markdown(f"  [👉 상세페이지 바로가기]({b_item['상세페이지']})")
                st.divider()

            st.subheader("🖨️ 인쇄 및 표 형태 보기")
            st.dataframe(bm_df[["제목", "작가", "출판사", "대상", "강연방식", "상세페이지"]], use_container_width=True)

    # ==================== TAB 3: 원본 데이터 보기 ====================
    with tab3:
        st.markdown("### 📊 베이스 데이터 전체 목록 (총 2,644건)")
        st.write("통합 데이터베이스의 전체 항목을 표 형태로 조회하고 CSV 파일로 다운로드할 수 있습니다.")

        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 원본 데이터 (CSV) 다운로드",
            data=csv_data,
            file_name="작가와의_만남_통합데이터.csv",
            mime="text/csv"
        )

        st.dataframe(df, use_container_width=True, height=600)
