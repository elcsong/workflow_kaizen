"""학습 모드 Phase 탭 컴포넌트.

Sprint 4 범위: Phase 1·2·3 모두 추출. 외부 의존성(LLM 스트리밍, 세션 매니저,
transcript API)은 호출자가 인자로 주입.
"""
from __future__ import annotations

import os
from typing import Any, Callable, MutableMapping

import pandas as pd

from english_app.services.knowledge_extractor import to_bank_row
from english_app.services.video import extract_video_id_from_url
from english_app.ui.tips import TIPS

# Step 5 Quick Capture preview 키 — 세션 상태에 저장된 ExtractedEntry
_QUICK_CAPTURE_PREVIEW_KEY = "step5_quick_capture_preview"


def render_phase1(
    *,
    st,
    sess: MutableMapping,
    on_dirty: Callable[[], None],
) -> None:
    """Phase 1: Listening — Step 1~3 (자막 OFF)."""
    st.subheader("Phase 1: Proper Listening (Steps 1-3)", help=TIPS["phase1"])
    st.markdown(
        "* **Step 1: Just Listen** - Relax and grasp the context (No input needed)."
    )

    col_s2, col_s3 = st.columns(2)

    with col_s2:
        val = st.text_area(
            "Step 2: Note Taking (Main Ideas)",
            value=sess["phase1"].get("notes", ""),
            height=300,
            help=TIPS["p1_step2"],
            key="p1_step2_notes",
        )
        if val != sess["phase1"].get("notes", ""):
            sess["phase1"]["notes"] = val
            on_dirty()

        if st.button(
            "📥 Copy from Step 2",
            help="Copy Step 2 notes here to fill in the blanks.",
        ):
            new_val = sess["phase1"].get("notes", "")
            sess["phase1"]["missed_parts"] = new_val
            st.session_state["p1_step3_missed"] = new_val
            on_dirty()
            st.rerun()

    with col_s3:
        val = st.text_area(
            "Step 3: Listen Again (Missed Parts)",
            value=sess["phase1"].get("missed_parts", ""),
            height=300,
            help=TIPS["p1_step3"],
            key="p1_step3_missed",
        )
        if val != sess["phase1"].get("missed_parts", ""):
            sess["phase1"]["missed_parts"] = val
            on_dirty()


def render_phase2(
    *,
    st,
    sess: MutableMapping,
    on_dirty: Callable[[], None],
    ai_provider: str,
    ai_model_name: str,
    selected_model_id: str,
    stream_ai_explanation: Callable[..., Any],
    transcript_api,
    extract_knowledge_entry: Callable[..., Any] | None = None,
) -> None:
    """Phase 2: Analysis & Learning — Step 4~6 + AI 튜터 + 단어/문법 뱅크."""
    st.subheader("Phase 2: Analysis & Learning (Steps 4-6)", help=TIPS["phase2"])
    st.markdown("* **Step 6: Verify** - Turn off subtitles and listen again.")
    st.divider()

    # Step 4: Direct Translation
    st.markdown("### Step 4: Direct Translation (Compare with Notes)")
    st.caption("Turn on subtitles and compare them with your notes from Phase 1.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_area(
            "Your Step 2 Notes (Read Only):",
            value=sess["phase1"].get("notes", ""),
            height=200,
            disabled=True,
            key="step4_review_notes",
        )
    with c2:
        st.text_area(
            "Your Step 3 Missed Parts (Read Only):",
            value=sess["phase1"].get("missed_parts", ""),
            height=200,
            disabled=True,
            key="step4_review_missed",
        )
    with c3:
        transcript_text = sess.get("video_transcript", "")
        if not transcript_text:
            video_id = sess.get("video_id") or extract_video_id_from_url(
                sess.get("video_url", "")
            )
            if video_id and not sess.get("video_id"):
                sess["video_id"] = video_id
            if video_id:
                try:
                    api = transcript_api()
                    transcript_data = api.fetch(
                        video_id, languages=["en", "en-US", "en-GB"]
                    )
                    transcript_text = " ".join([item.text for item in transcript_data])
                    sess["video_transcript"] = transcript_text
                    on_dirty()
                except Exception as exc:  # noqa: BLE001
                    st.caption(f"⚠️ Could not fetch transcript: {str(exc)[:50]}")
        st.text_area(
            "📜 YouTube Script (Transcript):",
            value=transcript_text or "(No transcript available)",
            height=200,
            disabled=True,
            key="step4_youtube_script",
        )

    st.divider()
    st.markdown("### ⚡ Step 5: Quick Capture (Error Analysis)")
    st.caption(
        "모르는 단어/표현을 입력하면 AI가 본문 맥락을 찾고 자동으로 Bank로 정리합니다."
    )
    p2 = sess["phase2"]

    _render_step5_quick_capture(
        st=st,
        sess=sess,
        on_dirty=on_dirty,
        ai_provider=ai_provider,
        ai_model_name=ai_model_name,
        selected_model_id=selected_model_id,
        extract_knowledge_entry=extract_knowledge_entry,
    )

    st.divider()

    # Grammar AI Tutor — 긴 문장 심화 분석은 별도 유지
    with st.expander("📐 Grammar Deep Dive (긴 문장 심화 분석)", expanded=False):
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            val = st.text_area(
                "Analyze difficult sentence structures:",
                value=p2.get("grammar_issues", ""),
                height=150,
                help=TIPS["p2_step5_grammar"],
                key="input_grammar_issues",
            )
            if val != p2.get("grammar_issues", ""):
                sess["phase2"]["grammar_issues"] = val
                on_dirty()

        with col_g2:
            st.write("")
            st.write("")
            just_streamed = False
            if st.button(
                "🤖 Ask AI to Explain",
                help="Get explanation for the text above",
            ):
                if not p2.get("grammar_issues", "").strip():
                    st.warning("Please enter some text to analyze first.")
                else:
                    st.markdown(f"**🤖 AI Explanation ({ai_model_name}):**")
                    streamed = st.write_stream(
                        stream_ai_explanation(
                            p2.get("grammar_issues"),
                            ai_provider,
                            selected_model_id,
                            context=sess.get("video_transcript", ""),
                        )
                    )
                    st.session_state["ai_explanation"] = streamed
                    just_streamed = True

        if "ai_explanation" in st.session_state and not just_streamed:
            st.info(
                f"**🤖 AI Explanation ({ai_model_name}):**\n\n"
                f"{st.session_state['ai_explanation']}"
            )
            if st.button("Clear Explanation", key="clear_ai"):
                del st.session_state["ai_explanation"]
                st.rerun()

    # Linking — freeform 유지 (LLM 음성 분석 한계)
    with st.expander(
        "🔊 Linking & Pronunciation (Sound)",
        expanded=bool(p2.get("linking_issues")),
    ):
        val = st.text_area(
            "Write down sounds you couldn't catch:",
            value=p2.get("linking_issues", ""),
            height=150,
            help=TIPS["p2_step5_linking"],
            key="input_linking_issues",
        )
        if val != p2.get("linking_issues", ""):
            sess["phase2"]["linking_issues"] = val
            on_dirty()

    # General notes
    st.write("")
    val = st.text_area(
        "📝 General Analysis Notes",
        value=p2.get("notes", ""),
        height=100,
        help=TIPS["p2_step5_notes"],
        key="p2_general_notes",
    )
    if val != p2.get("notes", ""):
        sess["phase2"]["notes"] = val
        on_dirty()

    # Legacy notes — 기존 vocab_issues / linking_issues 보존 (읽기 전용)
    legacy_vocab = p2.get("vocab_issues", "")
    if legacy_vocab.strip():
        with st.expander(
            "📜 Legacy Vocab Notes (이전 freeform 기록)", expanded=False
        ):
            st.text_area(
                "Read-only legacy vocabulary notes",
                value=legacy_vocab,
                height=120,
                disabled=True,
                key="legacy_vocab_view",
                label_visibility="collapsed",
            )
            st.caption(
                "다음 이터레이션에서 일괄 마이그레이션 예정 — 지금은 참고용."
            )

    st.divider()
    st.subheader("📚 Personal Knowledge Bank")
    bank_tab1, bank_tab2 = st.tabs(["Vocabulary Bank", "Grammar Bank"])

    with bank_tab1:
        st.caption("Collect unknown words here:")
        current_vocab = p2.get("vocab_list", [])
        initial_vocab_df = (
            pd.DataFrame(current_vocab)
            if current_vocab
            else pd.DataFrame(columns=["Word", "Meaning", "Example"])
        )
        edited = st.data_editor(
            initial_vocab_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Word": st.column_config.TextColumn("Word", width="small"),
                "Meaning": st.column_config.TextColumn("Meaning", width="medium"),
                "Example": st.column_config.TextColumn("Example", width="large"),
            },
            key=f"vocab_editor_{sess['id']}",
        )
        if st.button("💾 Save Vocabulary", key="save_vocab_btn"):
            new_vocab = [
                row
                for row in edited.to_dict("records")
                if any(str(v).strip() for v in row.values() if v is not None)
            ]
            sess["phase2"]["vocab_list"] = new_vocab
            on_dirty()
            st.toast("Vocabulary saved!", icon="✅")

    with bank_tab2:
        st.caption("Collect sentence patterns & grammar points here:")
        current_grammar = p2.get("grammar_list", [])
        initial_grammar_df = (
            pd.DataFrame(current_grammar)
            if current_grammar
            else pd.DataFrame(columns=["Sentence/Pattern", "Grammar Point", "My Note"])
        )
        edited = st.data_editor(
            initial_grammar_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Sentence/Pattern": st.column_config.TextColumn(
                    "Sentence/Pattern", width="large"
                ),
                "Grammar Point": st.column_config.TextColumn(
                    "Grammar Point", width="medium"
                ),
                "My Note": st.column_config.TextColumn("My Note", width="large"),
            },
            key=f"grammar_editor_{sess['id']}",
        )
        if st.button("💾 Save Grammar", key="save_grammar_btn"):
            new_grammar = [
                row
                for row in edited.to_dict("records")
                if any(str(v).strip() for v in row.values() if v is not None)
            ]
            sess["phase2"]["grammar_list"] = new_grammar
            on_dirty()
            st.toast("Grammar saved!", icon="✅")


def render_phase3(
    *,
    st,
    sess: MutableMapping,
    on_dirty: Callable[[], None],
    save_audio: Callable[[str, bytes], str],
    audio_dir: str,
    ai_provider: str | None = None,
    ai_model_name: str | None = None,
    selected_model_id: str | None = None,
    stream_summary_critique: Callable[..., Any] | None = None,
) -> None:
    """Phase 3: Shadowing & Output — Step 7~10.

    AI 인자(ai_provider, selected_model_id, stream_summary_critique)가 전달되면
    Step 10에 "🤖 첨삭 받기" 버튼을 표출. 인자 미제공 시 비활성.
    """
    st.subheader("Phase 3: Shadowing & Utilization (Steps 7-10)", help=TIPS["phase3"])
    st.markdown(
        "* **Step 7: Review** (21:23) - Final review of missed parts.\n"
        "* **Step 8: Shadowing** (21:35) - Mimic intonation/speed (No input needed)."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🎙️ Step 9: Recording", help=TIPS["p3_step9"])
        audio_val = st.audio_input("Record Shadowing/Summary")
        if audio_val:
            st.audio(audio_val)
            if st.button("Save Recording"):
                bytes_data = audio_val.read()
                fname = save_audio(sess["id"], bytes_data)
                sess["phase3"]["audio_file"] = fname
                st.success("Saved!")
                on_dirty()
        saved = sess["phase3"].get("audio_file")
        if saved:
            st.info(f"Saved: {saved}")
            path = os.path.join(audio_dir, saved)
            if os.path.exists(path):
                st.audio(path)

    with c2:
        st.markdown("### ✍️ Step 10: Output", help=TIPS["p3_step10"])
        val = st.text_area(
            "Summary (Your Own Words):",
            value=sess["phase3"].get("summary", ""),
            height=300,
            key="p3_summary_output",
        )
        if val != sess["phase3"].get("summary", ""):
            sess["phase3"]["summary"] = val
            on_dirty()

        # Step 10 AI 첨삭 — 원문 transcript와 사용자 요약 비교
        if stream_summary_critique is not None and ai_provider and selected_model_id:
            transcript_text = sess.get("video_transcript", "")
            critique_disabled = not val.strip() or not transcript_text
            help_msg = None
            if not val.strip():
                help_msg = "요약을 먼저 작성해 주세요."
            elif not transcript_text:
                help_msg = "원문 transcript가 없으면 첨삭이 어렵습니다 (자막 없는 영상)."

            just_critiqued = False
            if st.button(
                "🤖 첨삭 받기 (Compare with Source)",
                help=help_msg or "원문과 비교해 첨삭 결과를 받습니다",
                disabled=critique_disabled,
            ):
                st.markdown(
                    f"**🤖 Step 10 첨삭 ({ai_model_name}):**"
                )
                streamed = st.write_stream(
                    stream_summary_critique(
                        val,
                        transcript_text,
                        ai_provider,
                        selected_model_id,
                    )
                )
                st.session_state["p3_critique"] = streamed
                just_critiqued = True

            if "p3_critique" in st.session_state and not just_critiqued:
                with st.expander(
                    f"📋 이전 첨삭 결과 ({ai_model_name})",
                    expanded=True,
                ):
                    st.markdown(st.session_state["p3_critique"])
                    if st.button("Clear Critique", key="clear_p3_critique"):
                        del st.session_state["p3_critique"]
                        st.rerun()


def _render_step5_quick_capture(
    *,
    st,
    sess: MutableMapping,
    on_dirty: Callable[[], None],
    ai_provider: str,
    ai_model_name: str,
    selected_model_id: str,
    extract_knowledge_entry: Callable[..., Any] | None,
) -> None:
    """Step 5 Quick Capture — 입력→AI 분석→Preview 카드→Bank 저장."""
    transcript_text = sess.get("video_transcript", "")
    extractor_ready = (
        extract_knowledge_entry is not None
        and ai_provider
        and selected_model_id
    )

    user_input = st.text_input(
        "모르는 단어 또는 표현",
        placeholder="예: neurobiological / not only X but also Y",
        key="step5_capture_input",
    )

    capture_clicked = st.button(
        "🤖 분석 & 정리",
        type="primary",
        disabled=not extractor_ready or not user_input.strip(),
        help=(
            None if extractor_ready
            else "AI 추출기가 연결되지 않았습니다 — Provider 설정을 확인하세요"
        ),
    )

    if capture_clicked and extractor_ready and user_input.strip():
        with st.spinner(f"본문에서 맥락 찾는 중... ({ai_model_name})"):
            entry = extract_knowledge_entry(
                user_input=user_input,
                transcript=transcript_text,
                provider=ai_provider,
                model_name=selected_model_id,
            )
        # ExtractedEntry는 frozen dataclass — dict로 변환해 세션에 저장
        st.session_state[_QUICK_CAPTURE_PREVIEW_KEY] = {
            "bank": entry.bank,
            "word_or_pattern": entry.word_or_pattern,
            "meaning": entry.meaning,
            "quote": entry.quote,
            "example": entry.example,
            "note": entry.note,
        }
        st.rerun()

    preview = st.session_state.get(_QUICK_CAPTURE_PREVIEW_KEY)
    if not preview:
        return

    with st.container(border=True):
        st.markdown("**📋 분석 결과 (Preview)**")
        bank_label = st.selectbox(
            "분류",
            options=["Vocabulary", "Grammar"],
            index=0 if preview.get("bank") == "vocabulary" else 1,
            key="step5_preview_bank",
        )
        new_bank = "vocabulary" if bank_label == "Vocabulary" else "grammar"

        if preview.get("quote"):
            st.markdown(f"📍 **본문 위치**")
            st.info(preview["quote"])
        else:
            st.caption("📍 본문에서 정확한 위치를 찾지 못했습니다.")

        edited_word = st.text_input(
            "Word / Pattern",
            value=preview.get("word_or_pattern", ""),
            key="step5_preview_word",
        )
        edited_meaning = st.text_input(
            "📖 뜻 (Meaning)",
            value=preview.get("meaning", ""),
            key="step5_preview_meaning",
        )
        edited_example = st.text_area(
            "💡 예시 (Example)",
            value=preview.get("example", ""),
            height=68,
            key="step5_preview_example",
        )
        edited_note = st.text_area(
            "📝 메모 (Note)",
            value=preview.get("note", ""),
            height=68,
            key="step5_preview_note",
        )

        c_save, c_discard = st.columns([1, 1])
        with c_save:
            if st.button(
                "✅ Bank에 저장", type="primary", use_container_width=True,
                key="step5_preview_save",
            ):
                from english_app.models import ExtractedEntry
                final = ExtractedEntry(
                    bank=new_bank,
                    word_or_pattern=edited_word.strip(),
                    meaning=edited_meaning.strip(),
                    quote=preview.get("quote", ""),
                    example=edited_example.strip(),
                    note=edited_note.strip(),
                )
                row = to_bank_row(final)
                # ✨ 마커 — AI 자동 추가 항목 표식
                row["✨"] = "🤖"
                if final.bank == "vocabulary":
                    sess["phase2"].setdefault("vocab_list", [])
                    sess["phase2"]["vocab_list"] = list(sess["phase2"]["vocab_list"]) + [row]
                else:
                    sess["phase2"].setdefault("grammar_list", [])
                    sess["phase2"]["grammar_list"] = list(sess["phase2"]["grammar_list"]) + [row]
                on_dirty()
                st.session_state.pop(_QUICK_CAPTURE_PREVIEW_KEY, None)
                # 입력창 비우기
                st.session_state["step5_capture_input"] = ""
                st.toast(
                    f"✅ {bank_label} Bank에 저장됨", icon="📚",
                )
                st.rerun()
        with c_discard:
            if st.button(
                "🗑️ 폐기", use_container_width=True,
                key="step5_preview_discard",
            ):
                st.session_state.pop(_QUICK_CAPTURE_PREVIEW_KEY, None)
                st.rerun()
