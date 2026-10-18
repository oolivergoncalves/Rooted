"""Ask the Graph: the Coordinator Agent answers by traversing the graph and never writes Cypher."""
import json
from html import escape as esc

import streamlit as st

from agents import coordinator_agent
from graph import queries, tools
from services.utils import fmt_datetime, session_label
from ui import components as c
from ui import layout

session = layout.setup()
layout.page_header(session, "Ask the Graph",
                   "The Coordinator Agent answers by walking recorded connections. It never writes Cypher.",
                   title_class="greet care-greet")

if not queries.list_plants():
    st.info("This garden has no plants yet. Add one from Home (＋ Add Plant) to ask questions about it.")
    st.stop()

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

EXAMPLES = {
    "Why is there a task?": "Why was the Monstera task created?",
    "What happened after watering?": "What happened to the Monstera since it was watered?",
    "How did the soil change?": "How did the Monstera observations change?",
    "Who handled it?": "Which agents handled the Monstera?",
    "What do we know?": "What do we know about the Monstera?",
}
with st.container(key="ask-examples"):
    examples = list(EXAMPLES.items())
    cols = st.columns(len(examples))
    for col, (label, text) in zip(cols, examples):
        if col.button(label, key=f"ex_{label}", use_container_width=True):
            st.session_state["q"] = text

with st.container(key="panel_ask"):
    question = st.text_input("Question", key="q", placeholder="Why was the Monstera task created?")
    st.markdown('<div class="ask-tip">Tip: name a plant and use words like why, since, change, handled or know.</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    plants = queries.list_plants()
    hint = c1.selectbox("About plant", [""] + [p["name"] for p in plants],
                        format_func=lambda n: n or "Detect from the question")
    depth = c2.slider("Depth (hops across sessions / superseded observations)", 1, tools.MAX_DEPTH, tools.MAX_DEPTH)
    if st.button("Ask", type="primary") and question.strip():
        st.session_state["answer"] = coordinator_agent.answer_question(question, session["id"], hint, depth)

ans = st.session_state.get("answer")
if ans:
    with st.container(key="panel_answer"):
        st.markdown(c.chip(ans["label"], ans["tone"]), unsafe_allow_html=True)
        st.markdown(f'<div class="why"><p>{esc(ans["sentence"])}</p></div>', unsafe_allow_html=True)
        if ans["learned_at"]:
            st.caption(f"Learned in {session_label(ans['learned_session'])} on {fmt_datetime(ans['learned_at'])}. "
                       "Nothing new has been recorded about this plant since.")
        if ans["paths"]:
            st.markdown('<div class="ptitle" style="margin-top:.8rem">Path walked</div>', unsafe_allow_html=True)
            for path in ans["paths"]:
                st.markdown(' <span style="color:#2f5d3a">→</span> '.join(c.chip(x, "gray") for x in path),
                            unsafe_allow_html=True)
        if ans["facts"]:
            for fact in ans["facts"]:
                st.write("• " + fact)

        st.markdown('<div class="ptitle" style="margin-top:.8rem">Trace</div>', unsafe_allow_html=True)
        if ans["trace"]:
            st.table([{"Tool": t["tool"], "Arguments": json.dumps(t["args"]), "Time (ms)": t["ms"], "Rows": t["rows"]}
                      for t in ans["trace"]])
        else:
            st.caption("No tool ran." if ans["outcome"] != "answered_from_memory"
                       else "No traversal ran: the answer came from a stored finding.")
        st.caption(f"Tool chosen by: {ans['route_source']} · Sentence by: {ans['sentence_source']} · "
                   f"Check: {ans['check']}")
        spec = tools.TOOLS.get(ans["tool"])
        if spec and spec["cypher"]:
            with st.expander(f"Cypher behind “{ans['tool']}”"):
                for q in spec["cypher"]:
                    st.code(q.strip(), language="cypher")
