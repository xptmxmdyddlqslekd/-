import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="작가와의 만남 통합 검색", layout="wide", page_icon="📚")

st.title("📚 작가와의 만남 통합 검색 서비스")
st.caption("책씨앗, 문학동네, 위즈덤하우스, 책읽는곰, 비룡소, 사계절 등 출판사별 작가 강연 검색")

# 1. 데이터 불러오기 함수
@st.cache_data
def load_data():
    try:
        # 통합 CSV 파일 로드
        df = pd.read_csv("integrated_author_events.csv")
        # 결측치(빈값) 처리
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"데이터 파일(integrated_author_events.csv)을 불러오지 못했습니다: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 검색 필터")

    # 출판사 필터
    all_publishers = sorted([p for p in df["출판사"].unique() if p])
    selected_publisher = st.sidebar.multiselect(
        "출판사 선택", 
        options=all_publishers, 
        default=all_publishers[:10] if len(all_publishers) > 10 else all_publishers
    )

    # 강연 방식 필터
    methods = ["전체", "비대면", "대면"]
    selected_method = st.sidebar.radio("강연 방식", options=methods, index=0)

    # --- 메인 검색창 ---
    st.markdown("### 🔎 키워드 검색")
    search_query = st.text_input(
        "작가명, 도서/강연 제목, 주제 키워드(예: 환경, 공룡, 우정, 그림책 등)를 입력하세요", 
        ""
    )

    # --- 데이터 필터링 로직 ---
    filtered_df = df.copy()

    # 1) 출판사 필터
    if selected_publisher:
        filtered_df = filtered_df[filtered_df["출판사"].isin(selected_publisher)]

    # 2) 강연 방식 필터
    if selected_method != "전체":
        filtered_df = filtered_df[filtered_df["강연방식"].str.contains(selected_method, na=False)]

    # 3) 검색어 필터
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
        st.info("검색 결과가 없습니다. 다른 검색어나 필터를 사용해 보세요.")
    else:
        # 결과를 10개씩 페이지네이션 형태로 보여주기
        items_per_page = 10
        total_pages = (len(filtered_df) - 1) // items_per_page + 1
        page = st.number_input("페이지", min_value=1, max_value=total_pages, value=1, step=1)

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