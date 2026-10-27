import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="축구 선수 기록 분석", page_icon="⚽", layout="wide")

st.title("⚽ 축구 선수 기록 분석 프로그램")
st.caption("프로 선수의 기록을 직접 입력하고 통계와 그래프로 비교하는 웹 앱")

COLUMNS = [
    "선수 이름", "시즌/대회", "출전 경기", "출전 시간(분)", "골", "도움",
    "전체 슈팅", "유효 슈팅", "패스 성공", "패스 시도"
]

if "players" not in st.session_state:
    st.session_state.players = pd.DataFrame(columns=COLUMNS)

def calculate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """원본 기록에 분석용 통계 열을 추가한다."""
    result = df.copy()
    numeric_cols = ["출전 경기", "출전 시간(분)", "골", "도움", "전체 슈팅",
                    "유효 슈팅", "패스 성공", "패스 시도"]
    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)

    result["공격 포인트"] = result["골"] + result["도움"]
    result["경기당 득점"] = result.apply(
        lambda row: row["골"] / row["출전 경기"] if row["출전 경기"] > 0 else 0, axis=1
    )
    result["경기당 공격 포인트"] = result.apply(
        lambda row: row["공격 포인트"] / row["출전 경기"] if row["출전 경기"] > 0 else 0, axis=1
    )
    result["슈팅 유효율(%)"] = result.apply(
        lambda row: row["유효 슈팅"] / row["전체 슈팅"] * 100 if row["전체 슈팅"] > 0 else 0, axis=1
    )
    result["패스 성공률(%)"] = result.apply(
        lambda row: row["패스 성공"] / row["패스 시도"] * 100 if row["패스 시도"] > 0 else 0, axis=1
    )
    return result

def validate_record(record: dict, existing: pd.DataFrame):
    name = str(record["선수 이름"]).strip()
    if not name:
        return "선수 이름을 입력해 주세요."
    if not str(record["시즌/대회"]).strip():
        return "시즌 또는 대회명을 입력해 주세요."

    numeric_cols = [c for c in COLUMNS if c not in ["선수 이름", "시즌/대회"]]
    for col in numeric_cols:
        if record[col] < 0:
            return f"'{col}'은(는) 음수일 수 없습니다."

    if record["유효 슈팅"] > record["전체 슈팅"]:
        return "유효 슈팅 수는 전체 슈팅 수보다 클 수 없습니다."
    if record["패스 성공"] > record["패스 시도"]:
        return "패스 성공 수는 패스 시도 수보다 클 수 없습니다."
    if record["출전 경기"] == 0 and (
        record["골"] > 0 or record["도움"] > 0 or record["출전 시간(분)"] > 0
    ):
        return "출전 경기가 0이면 골, 도움, 출전 시간도 0으로 입력해 주세요."

    duplicate = existing[
        (existing["선수 이름"].astype(str).str.casefold() == name.casefold()) &
        (existing["시즌/대회"].astype(str).str.casefold() == str(record["시즌/대회"]).strip().casefold())
    ]
    if not duplicate.empty:
        return "같은 선수와 시즌/대회 기록이 이미 있습니다. 기존 기록을 수정하거나 다른 시즌을 입력해 주세요."
    return None

with st.sidebar:
    st.header("메뉴")
    page = st.radio("이동할 화면", ["기록 입력", "기록 분석", "데이터 관리", "사용 안내"])
    st.divider()
    st.metric("등록된 기록", len(st.session_state.players))
    st.caption("실제 선수 기록을 사용할 때는 선수와 시즌/대회 기준을 동일하게 맞춰 비교하세요.")

if page == "기록 입력":
    st.subheader("선수 기록 직접 입력")
    st.write("각 선수의 **같은 시즌 또는 같은 대회 기준 기록**을 입력하는 것을 권장합니다.")
    with st.form("player_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("선수 이름", placeholder="예: 손흥민")
            competition = st.text_input("시즌/대회", placeholder="예: 2023-24 프리미어리그")
            appearances = st.number_input("출전 경기", min_value=0, max_value=100, value=0, step=1)
            minutes = st.number_input("출전 시간(분)", min_value=0, max_value=10000, value=0, step=1)
            goals = st.number_input("골", min_value=0, max_value=500, value=0, step=1)
            assists = st.number_input("도움", min_value=0, max_value=500, value=0, step=1)
        with col2:
            shots = st.number_input("전체 슈팅", min_value=0, max_value=2000, value=0, step=1)
            shots_on_target = st.number_input("유효 슈팅", min_value=0, max_value=2000, value=0, step=1)
            passes_completed = st.number_input("패스 성공", min_value=0, max_value=20000, value=0, step=1)
            passes_attempted = st.number_input("패스 시도", min_value=0, max_value=30000, value=0, step=1)
        submitted = st.form_submit_button("선수 기록 저장", type="primary")

    if submitted:
        record = {
            "선수 이름": name.strip(),
            "시즌/대회": competition.strip(),
            "출전 경기": int(appearances),
            "출전 시간(분)": int(minutes),
            "골": int(goals),
            "도움": int(assists),
            "전체 슈팅": int(shots),
            "유효 슈팅": int(shots_on_target),
            "패스 성공": int(passes_completed),
            "패스 시도": int(passes_attempted),
        }
        error = validate_record(record, st.session_state.players)
        if error:
            st.error(error)
        else:
            st.session_state.players = pd.concat(
                [st.session_state.players, pd.DataFrame([record])], ignore_index=True
            )
            st.success(f"{record['선수 이름']}의 기록을 저장했습니다.")

    st.info("참고: 이 프로그램은 입력한 기록을 분석합니다. 자동으로 인터넷에서 실제 기록을 가져오지는 않습니다.")

elif page == "기록 분석":
    st.subheader("선수 기록 분석 및 비교")
    if st.session_state.players.empty:
        st.warning("분석할 기록이 없습니다. 먼저 '기록 입력' 메뉴에서 선수를 등록해 주세요.")
    else:
        raw = st.session_state.players.copy()
        stats = calculate_stats(raw)
        total_goals = int(stats["골"].sum())
        total_assists = int(stats["도움"].sum())
        total_players = len(stats)
        c1, c2, c3 = st.columns(3)
        c1.metric("등록 기록 수", total_players)
        c2.metric("총 골", total_goals)
        c3.metric("총 도움", total_assists)

        st.markdown("### 전체 기록 및 계산 결과")
        display_cols = COLUMNS + ["공격 포인트", "경기당 득점", "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"]
        shown = stats[display_cols].copy()
        for col in ["경기당 득점", "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"]:
            shown[col] = shown[col].round(2)
        st.dataframe(shown, use_container_width=True, hide_index=True)

        st.markdown("### 순위 보기")
        metric = st.selectbox("순위 기준 선택", ["골", "도움", "공격 포인트", "경기당 득점", "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"])
        ranked = stats.sort_values(metric, ascending=False)[["선수 이름", "시즌/대회", metric]]
        st.dataframe(ranked.reset_index(drop=True), use_container_width=True, hide_index=True)

        st.markdown("### 선수 비교 그래프")
        names = stats.apply(lambda r: f"{r['선수 이름']} ({r['시즌/대회']})", axis=1).tolist()
        selected = st.multiselect("비교할 선수 기록 선택 (최대 6개)", names, default=names[:min(3, len(names))])
        if selected:
            chart_data = stats.assign(표시이름=names)
            chart_data = chart_data[chart_data["표시이름"].isin(selected)]
            chart_metric = st.selectbox("그래프로 비교할 항목", ["골", "도움", "공격 포인트", "경기당 득점", "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"])
            if len(selected) > 6:
                st.warning("그래프는 한 번에 최대 6개 기록까지 비교하는 것을 권장합니다.")
                chart_data = chart_data.head(6)
            st.bar_chart(chart_data.set_index("표시이름")[[chart_metric]])
        else:
            st.info("비교할 선수 기록을 하나 이상 선택해 주세요.")

        st.markdown("### 간단한 기록 해석")
        if not stats.empty:
            top_scorer = stats.sort_values("골", ascending=False).iloc[0]
            top_assist = stats.sort_values("도움", ascending=False).iloc[0]
            st.write(f"- 가장 많은 골을 기록한 항목: **{top_scorer['선수 이름']}** ({int(top_scorer['골'])}골)")
            st.write(f"- 가장 많은 도움을 기록한 항목: **{top_assist['선수 이름']}** ({int(top_assist['도움'])}도움)")
            st.caption("이 결과는 입력된 데이터에 한정되며, 선수의 전체 실력을 단정하는 평가가 아닙니다.")

elif page == "데이터 관리":
    st.subheader("기록 관리")
    if st.session_state.players.empty:
        st.info("아직 등록된 기록이 없습니다.")
    else:
        st.dataframe(st.session_state.players, use_container_width=True, hide_index=True)
        csv_bytes = st.session_state.players.to_csv(index=False).encode("utf-8-sig")
        st.download_button("현재 기록을 CSV로 다운로드", data=csv_bytes, file_name="football_player_records.csv", mime="text/csv")

        st.markdown("### 기록 삭제")
        labels = [
            f"{i}: {row['선수 이름']} / {row['시즌/대회']}"
            for i, row in st.session_state.players.iterrows()
        ]
        choice = st.selectbox("삭제할 기록 선택", labels)
        if st.button("선택한 기록 삭제", type="secondary"):
            idx = int(choice.split(":")[0])
            st.session_state.players = st.session_state.players.drop(index=idx).reset_index(drop=True)
            st.success("선택한 기록을 삭제했습니다.")
            st.rerun()

    st.markdown("### CSV 파일 불러오기")
    uploaded = st.file_uploader("이전에 저장한 football_player_records.csv 파일 선택", type=["csv"])
    if uploaded is not None:
        try:
            incoming = pd.read_csv(uploaded)
            missing = [c for c in COLUMNS if c not in incoming.columns]
            if missing:
                st.error("파일에 필요한 열이 없습니다: " + ", ".join(missing))
            else:
                incoming = incoming[COLUMNS].copy()
                numeric_cols = [c for c in COLUMNS if c not in ["선수 이름", "시즌/대회"]]
                for col in numeric_cols:
                    incoming[col] = pd.to_numeric(incoming[col], errors="raise")
                if st.button("CSV 기록 추가"):
                    combined = st.session_state.players.copy()
                    added = 0
                    errors = []
                    for _, row in incoming.iterrows():
                        record = row.to_dict()
                        for col in numeric_cols:
                            record[col] = int(record[col])
                        error = validate_record(record, combined)
                        if error:
                            errors.append(f"{record.get('선수 이름', '이름 없음')}: {error}")
                        else:
                            combined = pd.concat([combined, pd.DataFrame([record])], ignore_index=True)
                            added += 1
                    st.session_state.players = combined
                    st.success(f"{added}개의 기록을 추가했습니다.")
                    if errors:
                        st.warning("일부 기록은 추가하지 않았습니다:\n\n" + "\n".join(errors[:10]))
        except Exception as exc:
            st.error(f"CSV 파일을 읽지 못했습니다. 열 이름과 숫자 형식을 확인해 주세요. ({exc})")

else:
    st.subheader("사용 안내")
    st.markdown("""
    1. **기록 입력** 메뉴에서 선수 이름과 시즌/대회를 입력합니다.
    2. 골, 도움, 슈팅, 패스 등 해당 시즌/대회의 기록을 입력하고 저장합니다.
    3. **기록 분석** 메뉴에서 계산 결과와 순위를 확인합니다.
    4. 그래프에서 비교할 선수와 통계 항목을 선택합니다.
    5. **데이터 관리** 메뉴에서 기록을 CSV 파일로 다운로드해 보관하거나, 이전 CSV 파일을 불러옵니다.

    ### 기록을 입력할 때 주의할 점
    - 손흥민과 메시를 비교할 때는 가능한 한 같은 시즌 또는 같은 대회 기준을 사용하세요.
    - 서로 다른 대회나 기간의 기록을 비교하면 경기 수와 경기 환경이 달라 결과 해석에 한계가 생길 수 있습니다.
    - 이 프로그램은 입력한 기록을 바탕으로 계산하며, 실제 선수 기록을 자동으로 가져오지 않습니다.
    - 입력한 값이 정확한지 공식 리그·구단 기록 등 신뢰할 수 있는 출처에서 확인하세요.
    """)

st.divider()
st.caption("수행평가 프로젝트 예시 · 실제 선수 기록을 입력하기 전 계산식과 오류 처리 기능을 직접 테스트하세요.")
