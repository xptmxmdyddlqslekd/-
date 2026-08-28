import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="작가와의 만남 통합 검색", layout="wide", page_icon="📚")

st.title("📚 작가와의 만남 통합 검색 서비스")
st.caption("출판사, 강연 대상, 주제별로 원하시는 작가 강연을 손쉽게 찾아보세요.")

# 1. 데이터 불러오기
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

if not df.empty:
    # 탭 구성: [강연 검색] / [원본 데이터 확인]
    tab1, tab2 = st.tabs(["🔍 강연 검색하기", "📄 원본 데이터 보기 및 다운로드"])

    # ==================== TAB 1: 강연 검색 ====================
    with tab1:
        st.sidebar.header("🎛️ 조건별 필터")

        # 1. 출판사 필터 (처음 접속 시 아무것도 선택되지 않음)
        all_publishers = sorted([p for p in df["출판사"].unique() if p])
        selected_publisher = st.sidebar.multiselect(
            "🏢 출판사 선택 (선택 안 함 = 전체)",
            options=all_publishers,
            default=[]  # 기본 선택 없음
        )

        # 2. 대상(나이대) 필터
        target_options = ["유아", "저학년", "고학년", "초등", "청소년", "성인", "교사"]
        selected_targets = st.sidebar.multiselect(
            "🎯 강연 대상 선택 (선택 안 함 = 전체)",
            options=target_options,
            default=[]
        )

        # 3. 주제/분야 필터
        topic_options = ["그림책", "문학", "창작", "교양/문화", "사회", "인문", "과학"]
        selected_topics = st.sidebar.multiselect(
            "🏷️ 주요 주제 선택 (선택 안 함 = 전체)",
            options=topic_options,
            default=[]
        )

        # 4. 강연 방식 필터
        methods = ["전체", "비대면", "대면"]
        selected_method = st.sidebar.radio("💻 강연 방식", options=methods, index=0)

        # --- 메인 검색창 ---
        st.markdown("### 🔎 키워드 직접 검색")
        search_query = st.text_input(
            "작가명, 도서/강연 제목, 세부 주제어 등으로 검색하세요",
            ""
        )

        # --- 데이터 필터링 조건 적용 ---
        filtered_df = df.copy()

        # 출판사 선택이 있는 경우만 필터링 (선택 없으면 전체 포함)
        if selected_publisher:
            filtered_df = filtered_df[filtered_df["출판사"].isin(selected_publisher)]

        # 대상 필터 적용 (다중 선택 처리)
        if selected_targets:
            target_pattern = "|".join(selected_targets)
            filtered_df = filtered_df[filtered_df["대상"].str.contains(target_pattern, na=False)]

        # 주제 필터 적용
        if selected_topics:
            topic_pattern = "|".join(selected_topics)
            filtered_df = filtered_df[filtered_df["주제/소개"].str.contains(topic_pattern, na=False)]

        # 강연 방식 필터
        if selected_method != "전체":
            filtered_df = filtered_df[filtered_df["강연방식"].str.contains(selected_method, na=False)]

        # 검색어 입력 필터
        if search_query.strip():
            q = search_query.strip()
            filtered_df = filtered_df[
                filtered_df["작가"].str.contains(q, case=False, na=False) |
                filtered_df["도서/강연제목"].str.contains(q, case=False, na=False) |
                filtered_df["주제/소개"].str.contains(q, case=False, na=False) |
                filtered_df["대상"].str.contains(q, case=False, na=False)
            ]

        # --- 검색 결과 출력 ---
        st.markdown("---")
        st.subheader(f"총 {len(filtered_df):,}건의 강연이 검색되었습니다.")

        if len(filtered_df) == 0:
            st.info("검색 조건에 일치하는 결과가 없습니다. 필터를 조정해 보세요.")
        else:
            items_per_page = 10
            total_pages = (len(filtered_df) - 1) // items_per_page + 1
            
            page_col1, page_col2 = st.columns([1, 4])
            with page_col1:
                page = st.number_input("페이지 선택", min_value=1, max_value=total_pages, value=1, step=1)

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page

            current_batch = filtered_df.iloc[start_idx:end_idx]

            for idx, row in current_batch.iterrows():
                with st.container():
                    st.markdown(f"#### 📖 {row['도서/강연제목']}")
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**✍️ 작가:** {row['작가'] if row['작가'] else '미기재'}")
                        st.write(f"**🏢 출판사:** {row['출판사']}")
                    with col2:
                        st.write(f"**🎯 대상:** {row['대상'] if row['대상'] else '전체/미지정'}")
                        st.write(f"**💻 강연 방식:** {row['강연방식'] if row['강연방식'] else '대면'}")
                    with col3:
                        url = str(row['상세페이지']).strip()
                        if url and url.startswith("http"):
                            st.link_button("👉 상세페이지/신청", url)
                        else:
                            st.caption("상세링크 없음")

                    if row['주제/소개']:
                        st.caption(f"💡 주제/소개: {row['주제/소개']}")
                    
                    st.divider()

    # ==================== TAB 2: 원본 데이터 보기 ====================
    with tab2:
        st.markdown("### 📊 베이스 데이터 전체 목록 (총 2,644건)")
        st.write("통합 데이터베이스의 전체 항목을 표 형태로 조회하고 CSV 파일로 다운로드할 수 있습니다.")

        # CSV 다운로드 버튼
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 원본 데이터 (CSV) 다운로드",
            data=csv_data,
            file_name="작가와의_만남_통합데이터.csv",
            mime="text/csv"
        )

        st.dataframe(df, use_container_width=True, height=600)
