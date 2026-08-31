import streamlit as st
import pandas as pd
import math

# 페이지 기본 설정
st.set_page_config(page_title="작가와의 만남 통합 검색", layout="wide")

# ---------------------------------------------------------
# 미니멀리즘 CSS 스펙
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 전체 바탕 및 기본 폰트 */
    .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0F172A;
    }

    /* 실시간 통계 카운터 카드 */
    .stat-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        border: 1px solid #E2E8F0;
    }
    .stat-label {
        font-size: 12px;
        color: #64748B;
        font-weight: 500;
        margin-bottom: 2px;
    }
    .stat-value {
        font-size: 18px;
        color: #0F172A;
        font-weight: 700;
    }

    /* Input & Select 요소 커스텀 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }
    
    /* 버튼 커스텀 */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    /* 탭 스타일링 */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

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
    csv_file = "integrated_author_events.csv"
    try:
        df = pd.read_csv(csv_file)
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"데이터 파일을 불러오지 못했습니다: {e}")
        return pd.DataFrame()

df = load_data()

# Session State 초기화
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

def set_page(page_num):
    st.session_state.current_page = page_num

# ---------------------------------------------------------
# 사이드바 컨트롤 센터
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 필터 및 설정")
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("홈으로", use_container_width=True):
            st.session_state.clear()
            st.session_state.current_page = 1
            st.session_state.bookmarks = []
            st.rerun()
    with col_sb2:
        if st.button("초기화", use_container_width=True):
            st.session_state.clear()
            st.session_state.current_page = 1
            st.session_state.bookmarks = []
            st.rerun()

    st.markdown("---")

    all_publishers = sorted([p for p in df["출판사"].unique() if p]) if not df.empty else []
    selected_publisher = st.multiselect(
        "출판사",
        options=all_publishers,
        default=[],
        key="filter_pub"
    )

    target_options = ["유아", "저학년", "중학년", "고학년", "초등", "청소년", "성인", "교사"]
    selected_targets = st.multiselect(
        "대상",
        options=target_options,
        default=[],
        key="filter_target"
    )

    topic_options = ["그림책", "문학", "창작", "교양/문화", "사회", "인문", "과학", "환경", "역사"]
    selected_topics = st.multiselect(
        "주요 주제",
        options=topic_options,
        default=[],
        key="filter_topic"
    )

    selected_method = st.radio("강연 방식", options=["전체", "비대면", "대면"], index=0, key="filter_method")

    st.markdown("---")
    st.caption("정보 수정 및 제보")
    st.markdown("[강연 정보 제보하기](https://forms.google.com)", unsafe_allow_html=True)


# ---------------------------------------------------------
# 메인 영역 헤더 & 통계
# ---------------------------------------------------------
filtered_df = df.copy() if not df.empty else pd.DataFrame()

if not filtered_df.empty:
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

hero_col, stat1, stat2, stat3 = st.columns([3, 1, 1, 1])

with hero_col:
    st.markdown("""
        <h2 style='margin:0; font-weight:700; color:#0F172A; font-size:24px;'>작가와의 만남 통합 검색</h2>
        <p style='margin:4px 0 0 0; color:#64748B; font-size:13px;'>출판사별 작가 강연 정보를 한곳에서 검색하고 관리하세요.</p>
    """, unsafe_allow_html=True)

with stat1:
    st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">전체 데이터</div>
            <div class="stat-value">{len(df):,}건</div>
        </div>
    """, unsafe_allow_html=True)

with stat2:
    st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">검색 결과</div>
            <div class="stat-value" style="color:#2563EB;">{len(filtered_df):,}건</div>
        </div>
    """, unsafe_allow_html=True)

with stat3:
    st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">보관함</div>
            <div class="stat-value" style="color:#059669;">{len(st.session_state.bookmarks):,}개</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 탭 메인 콘텐츠
# ---------------------------------------------------------
if not df.empty:
    tab1, tab2, tab3 = st.tabs(["강연 검색", "관심 보관함", "전체 데이터"])

    # ==================== TAB 1: 강연 검색 ====================
    with tab1:
        search_col, sub_search_col = st.columns([3, 2])
        with search_col:
            search_query = st.text_input(
                "키워드 검색",
                placeholder="제목, 작가명, 주제어 또는 초성(예: ㄱㄱㅅ) 검색",
                key="search_input",
                label_visibility="collapsed"
            )
        with sub_search_col:
            sub_query = st.text_input(
                "결과 내 재검색",
                placeholder="검색 결과 내 추가 키워드 입력",
                key="sub_search",
                label_visibility="collapsed"
            )

        if search_query.strip():
            q = search_query.strip()
            if is_chosung_query(q):
                filtered_df["제목_초성"] = filtered_df["도서/강연제목"].apply(get_chosung)
                filtered_df["작가_초성"] = filtered_df["작가"].apply(get_chosung)
                filtered_df = filtered_df[
                    filtered_df["제목_초성"].str.contains(q, case=False, na=False) |
                    filtered_df["작가_초성"].str.contains(q, case=False, na=False)
                ]
            else:
                filtered_df = filtered_df[
                    filtered_df["도서/강연제목"].str.contains(q, case=False, na=False) |
                    filtered_df["작가"].str.contains(q, case=False, na=False) |
                    filtered_df["주제/소개"].str.contains(q, case=False, na=False) |
                    filtered_df["대상"].str.contains(q, case=False, na=False)
                ]

        if sub_query.strip():
            sq = sub_query.strip()
            filtered_df = filtered_df[
                filtered_df["도서/강연제목"].str.contains(sq, case=False, na=False) |
                filtered_df["작가"].str.contains(sq, case=False, na=False) |
                filtered_df["주제/소개"].str.contains(sq, case=False, na=False) |
                filtered_df["출판사"].str.contains(sq, case=False, na=False)
            ]

        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 2])
        with ctrl_col1:
            sort_option = st.selectbox(
                "정렬 기준",
                ["기본순", "도서/강연제목순", "작가명순", "출판사순"],
                key="sort_opt",
                label_visibility="collapsed"
            )
            if sort_option == "도서/강연제목순":
                filtered_df = filtered_df.sort_values(by="도서/강연제목").reset_index(drop=True)
            elif sort_option == "작가명순":
                filtered_df = filtered_df.sort_values(by="작가").reset_index(drop=True)
            elif sort_option == "출판사순":
                filtered_df = filtered_df.sort_values(by="출판사").reset_index(drop=True)

        with ctrl_col3:
            view_mode = st.radio(
                "뷰 모드",
                ["카드 보기", "표 보기"],
                horizontal=True,
                key="view_mode",
                label_visibility="collapsed"
            )

        st.markdown("<hr style='margin: 12px 0 20px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        if len(filtered_df) == 0:
            st.info("검색 조건과 일치하는 데이터가 없습니다.")
        else:
            # ==================== [MODE 1] 카드 형태 ====================
            if "카드" in view_mode:
                items_per_page = 10
                total_pages = math.ceil(len(filtered_df) / items_per_page)

                if st.session_state.current_page > total_pages:
                    st.session_state.current_page = max(1, total_pages)

                start_idx = (st.session_state.current_page - 1) * items_per_page
                current_batch = filtered_df.iloc[start_idx:start_idx + items_per_page].reset_index(drop=True)

                for idx in range(0, len(current_batch), 2):
                    c1, c2 = st.columns(2)
                    
                    # 좌측 카드
                    with c1:
                        row = current_batch.iloc[idx]
                        display_title = row['도서/강연제목']
                        item_id = f"{row['출판사']}_{row['작가']}_{display_title}"
                        is_bookmarked = item_id in [b.get('id') for b in st.session_state.bookmarks]

                        with st.container():
                            st.markdown(f"""
                            <div style="border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; background: white; margin-bottom: 12px;">
                                <h4 style="margin:0 0 8px 0; color:#0F172A; font-size:15px; font-weight:600;">{display_title}</h4>
                                <p style="margin:0 0 4px 0; font-size:13px; color:#475569;">작가: {row['작가']} | 출판사: {row['출판사']}</p>
                                <p style="margin:0 0 8px 0; font-size:13px; color:#475569;">대상: {row['대상']} | 방식: {row['강연방식']}</p>
                                <p style="margin:0 0 12px 0; font-size:12px; color:#64748B; background:#F8FAFC; padding:8px; border-radius:6px; line-height:1.4;">{row['주제/소개'] if row['주제/소개'] else '주제 정보가 없습니다.'}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            btn_c1, btn_c2 = st.columns([1, 1])
                            with btn_c1:
                                url = str(row['상세페이지']).strip()
                                if url and url.startswith("http"):
                                    st.link_button("상세페이지", url, use_container_width=True)
                                else:
                                    st.caption("상세링크 없음")
                            with btn_c2:
                                btn_label = "보관됨" if is_bookmarked else "보관하기"
                                if st.button(btn_label, key=f"bm_{idx}", use_container_width=True):
                                    if is_bookmarked:
                                        st.session_state.bookmarks = [b for b in st.session_state.bookmarks if b.get('id') != item_id]
                                    else:
                                        st.session_state.bookmarks.append({
                                            "id": item_id, "제목": display_title, "작가": row['작가'],
                                            "출판사": row['출판사'], "대상": row['대상'], "강연방식": row['강연방식'],
                                            "상세페이지": row['상세페이지']
                                        })
                                    st.rerun()

                    # 우측 카드
                    if idx + 1 < len(current_batch):
                        with c2:
                            row = current_batch.iloc[idx + 1]
                            display_title = row['도서/강연제목']
                            item_id = f"{row['출판사']}_{row['작가']}_{display_title}"
                            is_bookmarked = item_id in [b.get('id') for b in st.session_state.bookmarks]

                            with st.container():
                                st.markdown(f"""
                                <div style="border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; background: white; margin-bottom: 12px;">
                                    <h4 style="margin:0 0 8px 0; color:#0F172A; font-size:15px; font-weight:600;">{display_title}</h4>
                                    <p style="margin:0 0 4px 0; font-size:13px; color:#475569;">작가: {row['작가']} | 출판사: {row['출판사']}</p>
                                    <p style="margin:0 0 8px 0; font-size:13px; color:#475569;">대상: {row['대상']} | 방식: {row['강연방식']}</p>
                                    <p style="margin:0 0 12px 0; font-size:12px; color:#64748B; background:#F8FAFC; padding:8px; border-radius:6px; line-height:1.4;">{row['주제/소개'] if row['주제/소개'] else '주제 정보가 없습니다.'}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                btn_c1, btn_c2 = st.columns([1, 1])
                                with btn_c1:
                                    url = str(row['상세페이지']).strip()
                                    if url and url.startswith("http"):
                                        st.link_button("상세페이지", url, use_container_width=True)
                                    else:
                                        st.caption("상세링크 없음")
                                with btn_c2:
                                    btn_label = "보관됨" if is_bookmarked else "보관하기"
                                    if st.button(btn_label, key=f"bm_{idx+1}", use_container_width=True):
                                        if is_bookmarked:
                                            st.session_state.bookmarks = [b for b in st.session_state.bookmarks if b.get('id') != item_id]
                                        else:
                                            st.session_state.bookmarks.append({
                                                "id": item_id, "제목": display_title, "작가": row['작가'],
                                                "출판사": row['출판사'], "대상": row['대상'], "강연방식": row['강연방식'],
                                                "상세페이지": row['상세페이지']
                                            })
                                        st.rerun()

                # 하단 페이지네이션 (페이지 직입력 기능 포함)
                st.markdown("<br>", unsafe_allow_html=True)
                p_col1, p_col2, p_col3, p_col4 = st.columns([1.5, 1, 1.5, 1.5])
                
                with p_col1:
                    if st.button("이전 페이지", disabled=(st.session_state.current_page == 1), use_container_width=True):
                        set_page(st.session_state.current_page - 1)
                        st.rerun()
                
                with p_col2:
                    input_page = st.number_input(
                        "페이지 입력",
                        min_value=1,
                        max_value=total_pages,
                        value=st.session_state.current_page,
                        step=1,
                        label_visibility="collapsed",
                        key="page_input"
                    )
                    if input_page != st.session_state.current_page:
                        set_page(input_page)
                        st.rerun()
                
                with p_col3:
                    st.markdown(f"<p style='margin-top:8px; font-weight:500; font-size:14px; color:#64748B;'>/ {total_pages} 페이지</p>", unsafe_allow_html=True)
                
                with p_col4:
                    if st.button("다음 페이지", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
                        set_page(st.session_state.current_page + 1)
                        st.rerun()

            # ==================== [MODE 2] 표 형태 ====================
            else:
                table_df = filtered_df.copy().reset_index(drop=True)
                bookmarked_ids = [b.get('id') for b in st.session_state.bookmarks]
                table_df["선택"] = table_df.apply(
                    lambda r: f"{r['출판사']}_{r['작가']}_{r['도서/강연제목']}" in bookmarked_ids, axis=1
                )

                display_cols = ["선택", "도서/강연제목", "작가", "출판사", "대상", "강연방식", "주제/소개", "상세페이지"]
                col_config = {
                    "선택": st.column_config.CheckboxColumn("보관"),
                    "상세페이지": st.column_config.LinkColumn("링크", display_text="신청하기")
                }

                edited_df = st.data_editor(
                    table_df[display_cols],
                    use_container_width=True,
                    height=550,
                    column_config=col_config,
                    disabled=[c for c in display_cols if c != "선택"],
                    key="table_editor"
                )

                if st.button("선택 항목 보관함 업데이트", use_container_width=True):
                    selected_rows = edited_df[edited_df["선택"] == True]
                    new_bookmarks = []
                    for _, row in selected_rows.iterrows():
                        item_id = f"{row['출판사']}_{row['작가']}_{row['도서/강연제목']}"
                        new_bookmarks.append({
                            "id": item_id, "제목": row['도서/강연제목'], "작가": row['작가'],
                            "출판사": row['출판사'], "대상": row['대상'], "강연방식": row['강연방식'],
                            "상세페이지": row['상세페이지']
                        })
                    st.session_state.bookmarks = new_bookmarks
                    st.success("보관함 목록이 업데이트되었습니다.")
                    st.rerun()

    # ==================== TAB 2: 내 보관함 ====================
    with tab2:
        if not st.session_state.bookmarks:
            st.info("보관된 강연 항목이 없습니다.")
        else:
            b_head1, b_head2 = st.columns([4, 1])
            with b_head1:
                st.markdown("### 보관된 강연 목록")
            with b_head2:
                if st.button("전체 비우기", use_container_width=True):
                    st.session_state.bookmarks = []
                    st.rerun()

            bm_df = pd.DataFrame(st.session_state.bookmarks)
            st.dataframe(bm_df[["제목", "작가", "출판사", "대상", "강연방식", "상세페이지"]], use_container_width=True)

    # ==================== TAB 3: 원본 데이터 ====================
    with tab3:
        st.markdown(f"### 전체 데이터 목록 ({len(df):,}건)")
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSV 다운로드",
            data=csv_data,
            file_name="integrated_author_events.csv",
            mime="text/csv"
        )
        st.dataframe(df, use_container_width=True, height=600)
