import streamlit as st
import requests
import random
import re
import base64

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "EEVE-Korean-10.8B"

TOPICS = {
    "동물": ["기린", "코끼리", "펭귄", "늑대", "하마", "토끼", "여우", "호랑이", "부엉이", "사자"],
    "과일": ["사과", "바나나", "수박", "포도", "딸기", "복숭아", "파인애플", "키위", "오렌지", "자두"],
    "직업": ["의사", "경찰", "소방관", "선생님", "요리사", "프로그래머", "운동선수", "가수", "배우", "디자이너"],
    "교통수단": ["자전거", "기차", "비행기", "버스", "자동차", "오토바이", "지하철", "택시", "트럭", "요트"],
    "음식": ["김치", "떡볶이", "치킨", "비빔밥", "라면", "초밥", "불고기", "스파게티", "피자", "햄버거"]
}

SYSTEM_PROMPT = """
당신은 '라이어 게임(Liar Game)'에 참가한 플레이어입니다. 다음 규칙과 역할 지침을 철저히 따르세요:

🎮 [게임 개요]
- 게임은 총 3~8명의 플레이어로 진행되며, 각 플레이어는 'Player N' 형식의 이름을 가집니다.
- 모든 플레이어는 ‘일반’ 또는 ‘라이어’ 역할 중 하나를 가집니다. 이 역할은 비공개이며, 당신만 자신의 역할을 압니다.
- 일반 플레이어는 '제시어(keyword)'를 알고 있고, 이를 기반으로 애매하고 자연스러운 힌트를 제시해야 합니다.
- 라이어는 제시어를 모릅니다. 하지만 들키지 않기 위해 마치 알고 있는 것처럼 힌트를 줘야 합니다.

🎲 [발언 순서]
- 발언 순서는 게임 시작 시 무작위로 정해지며, 모든 라운드에서 동일하게 유지됩니다.

🗣️ [힌트 라운드 규칙]
- 게임은 총 3라운드이며, 각 라운드에서 모든 플레이어는 한 문장으로 힌트를 제시합니다.
- 힌트는 제시어를 직접 언급하거나 노골적으로 암시하면 안 됩니다.
- 힌트는 너무 어색하거나 뜬금없으면 안 됩니다. 가능한 한 자연스럽고 사람처럼 행동하세요.

🕵️ [추측 라운드 규칙]
- 힌트 라운드 이후, 모든 플레이어는 다른 플레이어들의 힌트를 보고 라이어가 누구일지 추측합니다.
- 누가 수상한지, 누가 일반 플레이어처럼 보이는지 짧은 코멘트를 남기세요.
- 존재하지 않는 플레이어나 라운드를 언급하지 마세요.
- 다른 플레이어가 사람이거나 AI인지 구분할 수 없습니다. 오직 'Player N' 형식의 이름으로만 판단하세요.
- 추측은 자연스럽고 사람처럼 말해야 하며, 절대 단정짓지 말고 추측에 기반하세요.
- 라이어는 본인이 라이어로 보이지 않도록 다른 사람이 라이어로 보이도록 유도해야 합니다.

🎭 [예시]
힌트 예시:
- "목이 정말 길죠."
- "조용한 성격인 것 같아요."
- "다리가 은근히 눈에 띄네요."

※ 힌트는 모두 한 문장이어야 하며, 너무 구체적이거나 너무 일반적이지 않아야 합니다.
※ 제시어를 직접 언급하거나 뚜렷한 연상어는 피하세요.
※ 자연스럽고 짧게 말하는 것이 중요합니다.

추측 멘트 예시:
- "Player 3은 힌트가 좀 무난했어. 일반일 수도 있을 것 같아."
- "Player 2는 말이 너무 조심스러웠어. 수상해."
"""


def get_ai_response(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        return res.json().get("message", {}).get("content", "")
    except Exception as e:
        return f"[ERROR] {e}"

def set_background(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url('data:image/png;base64,{encoded}');
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: #f5f5f5;
        }}
        .block-container {{ background-color: rgba(0, 0, 0, 0.6); padding: 2rem; border-radius: 1rem; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{ color: #f5f5f5 !important; }}
        </style>
    """, unsafe_allow_html=True)

st.set_page_config("라이어 게임", layout="centered")
set_background("bg.png")
st.title("🎭 라이어 게임")

if "started" not in st.session_state:
    st.session_state.started = False
if "round" not in st.session_state:
    st.session_state.round = 1
if "hints" not in st.session_state:
    st.session_state.hints = []
if "guesses" not in st.session_state:
    st.session_state.guesses = []
if "votes" not in st.session_state:
    st.session_state.votes = {}

if not st.session_state.started and st.session_state.round == 1:
    total_players = st.slider("플레이어 수", 3, 8, 5)
    human_players = st.slider("사람 수 (나머지는 AI)", 0, total_players, 1)
    if st.button("게임 시작"):
        topic = random.choice(list(TOPICS.keys()))
        keyword = random.choice(TOPICS[topic])
        names = [f"Player {i+1}" for i in range(total_players)]
        roles = ["Human"] * human_players + ["AI"] * (total_players - human_players)
        combined = list(zip(names, roles))
        random.shuffle(combined)
        player_names, roles = zip(*combined)
        player_names, roles = list(player_names), list(roles)
        liar_idx = random.randint(0, total_players - 1)
        player_order = player_names.copy()
        random.shuffle(player_order)

        st.session_state.update({
            "started": True,
            "topic": topic,
            "keyword": keyword,
            "player_names": player_names,
            "roles": roles,
            "liar_idx": liar_idx,
            "player_order": player_order,
            "round": 1,
            "hints": [],
            "guesses": [],
            "votes": {}
        })
        st.rerun()

if st.session_state.started:
    st.markdown(f"### 📢 발표 순서: {', '.join(st.session_state.player_order)}")
    st.progress(st.session_state.round / 3)
    round_num = st.session_state.round
    st.subheader(f"🧠 주제: {st.session_state.topic} | 라운드 {round_num}")
    hints = {}
    guesses = {}

    for player in st.session_state.player_order:
        idx = st.session_state.player_names.index(player)
        role = st.session_state.roles[idx]
        is_liar = idx == st.session_state.liar_idx

        st.markdown(f"#### {player}의 힌트 입력")
        key = f"hint_{player}_{round_num}"
        if role == "Human":
            if is_liar:
                st.warning("⚠️ 당신은 라이어입니다. 제시어는 모릅니다.")
            else:
                st.success(f"✅ 당신은 일반 플레이어입니다. 제시어: {st.session_state.keyword}")
            if key not in st.session_state:
                st.session_state[key] = ""
            hint = st.text_input("힌트를 입력하세요 (1문장)", key=key)
            if hint.strip() == "":
                st.stop()
            hints[player] = hint
            if st.session_state[key].strip() == "":
                st.stop()
            hints[player] = st.session_state[key]
        else:
            if key not in st.session_state:
                prompt = (
                    f"힌트 라운드 입니다. 주제는 '{st.session_state.topic}'이며 " +
                    ("당신은 라이어입니다. 제시어는 모릅니다. 최대한 라이어인게 티가 나지 않도록" if is_liar else f"제시어는 '{st.session_state.keyword}'입니다. 당신은 일반 플레이어입니다. 제시어를 직접 언급하지 말고") +
                    " 한 문장 힌트를 주세요."
                )
                st.session_state[key] = get_ai_response(prompt)
            hints[player] = st.session_state[key]
            st.markdown(f"💬 {hints[player]}")

    st.session_state.hints.append(hints)

    st.markdown("---")
    st.markdown("### 🕵️ 추측 시간")
    for player in st.session_state.player_order:
        idx = st.session_state.player_names.index(player)
        role = st.session_state.roles[idx]
        is_liar = idx == st.session_state.liar_idx

        st.markdown(f"#### {player}의 추측")
        key = f"guess_{player}_{round_num}"
        if role == "Human":
            for p in st.session_state.player_order:
                if p != player:
                    st.markdown(f"- {p}: {hints[p]}")
            if key not in st.session_state:
                st.session_state[key] = ""
            guess = st.text_input("누가 수상한가요?", key=key)
            if guess.strip() == "":
                st.stop()
            guesses[player] = guess
        else:
            if f"guess_{player}_{round_num}" not in st.session_state:
                summary = "\n".join([f"{p}: {hints[p]}" for p in st.session_state.player_order if p != player])
                prompt = (
                    f"추측 라운드 입니다. 당신은 {'라이어' if is_liar else '일반 플레이어'}입니다. 주제는 '{st.session_state.topic}'이며 " +
                    ("제시어는 모릅니다." if is_liar else f"제시어는 '{st.session_state.keyword}'입니다.") +
                    f"\n다음은 다른 플레이어의 힌트입니다:\n{summary}\n1문장으로 누가 라이어일지 자연스럽게 추측하세요."
                )
                st.session_state[f"guess_{player}_{round_num}"] = get_ai_response(prompt)
            guesses[player] = st.session_state[f"guess_{player}_{round_num}"]
            st.markdown(f"💬 {guesses[player]}")

    st.session_state.guesses.append(guesses)

    if st.button("다음 라운드로"):
        if st.session_state.round >= 3:
            st.session_state.started = False
        else:
            st.session_state.round += 1
        st.rerun()

if not st.session_state.started and st.session_state.round == 3:
    st.subheader("🗳️ 최종 투표")
    votes = {}
    for player in st.session_state.player_names:
        role = st.session_state.roles[st.session_state.player_names.index(player)]
        if role == "Human":
            vote = st.text_input(f"{player}의 투표 (Player N 입력)", key=f"vote_{player}")
        else:
            all_hints = "\n".join([f"{p}: {h[p]}" for h in st.session_state.hints for p in h])
            all_guesses = "\n".join([f"[Round {i+1} 추측] " + ", ".join([f"{p}: {g[p]}" for p in g]) for i, g in enumerate(st.session_state.guesses)])
            prompt = f"""
                    당신은 최종 투표를 하는 AI 플레이어입니다.
                    
                    아래는 전체 게임 동안 모든 플레이어가 제시한 힌트와 추측입니다.
                    
                    {all_hints}
                    
                    {all_guesses}
                    
                    이 내용을 바탕으로, 가장 수상한 라이어를 추리해 주세요.
                    정확히 'Player N' 형식으로 한 명만 출력하세요. (다른 말 없이 이름만!)
                    """
            # prompt = f"아래 힌트를 참고하여 라이어로 의심되는 한 명을 정확히 'Player N' 형식으로 출력하세요.\n{all_hints}"
            vote = get_ai_response(prompt)
            match = re.search(r"Player \d+", vote)
            vote = match.group() if match else "Unknown"
        if vote:
            votes[vote] = votes.get(vote, 0) + 1
    st.session_state.votes = votes

    st.markdown("### 📊 투표 결과")
    for name in st.session_state.player_names:
        st.markdown(f"- {name}: {votes.get(name, 0)}표")

    most_voted = max(votes, key=votes.get)
    liar_name = st.session_state.player_names[st.session_state.liar_idx]
    if most_voted == liar_name:
        st.success(f"✅ 라이어 {liar_name}이(가) 적발되었습니다! 일반 플레이어 승리!")
    else:
        st.error(f"😈 라이어 {liar_name}이(가) 들키지 않았습니다. 라이어 승리!")

    st.markdown(f"🎯 제시어: {st.session_state.keyword}")
