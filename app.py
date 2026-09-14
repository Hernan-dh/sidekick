"""Bilingual Gradio app for Sidekick. Run with: uv run python app.py"""

import html
import gradio as gr
import styles
from sidekick import Sidekick

LAUNCH_STYLE = {"theme": gr.themes.Base(), "css": styles.CSS, "js": styles.JS}
UI_TEXT = {
    "Español": {
        "eyebrow": "Tu compañero de trabajo personal",
        "subtitle": "Planifica, investiga y actúa con supervisión humana",
        "plan": "Plan", "plan_empty": "Sidekick mostrará acá su plan mientras trabaja.",
        "message": "¿Qué querés que haga Sidekick?",
        "criteria": "¿Cómo sabremos que la tarea está terminada?",
        "reset": "Reiniciar", "approve": "Aprobar y continuar", "go": "Comenzar", "theme": "Tema",
    },
    "English": {
        "eyebrow": "Your personal coworker",
        "subtitle": "Plans, researches, and acts with human oversight",
        "plan": "Plan", "plan_empty": "Sidekick will show its plan here while it works.",
        "message": "What would you like Sidekick to do?",
        "criteria": "How will we know the task is complete?",
        "reset": "Reset", "approve": "Approve and continue", "go": "Start", "theme": "Theme",
    },
}


def text_for(language: str) -> dict[str, str]:
    return UI_TEXT.get(language, UI_TEXT["English"])


def header_html(language: str) -> str:
    text = text_for(language)
    return f"""
    <div class="sidekick-brand">
      <div class="sidekick-mark" aria-hidden="true">
        <span class="mark-block mark-acid"></span><span class="mark-block mark-blue"></span>
        <span class="mark-block mark-orange"></span>
      </div>
      <div class="sidekick-headings">
        <p class="sidekick-eyebrow">{text['eyebrow']}</p>
        <h1>SIDE<span>/</span>KICK</h1>
        <p class="sidekick-subtitle">{text['subtitle']}</p>
      </div>
    </div>"""


def render_todos(todos, language="English"):
    text = text_for(language)
    if not todos:
        items = f'<div class="plan-placeholder">{html.escape(text["plan_empty"])}</div>'
    else:
        items = "<ul>" + "".join(
            f'<li class="{todo["status"]}"><span class="plan-mark"></span>'
            f'{html.escape(todo["content"])}</li>' for todo in todos
        ) + "</ul>"
    return f"<h3>{html.escape(text['plan'])}</h3>{items}"


def localized_ui(language: str):
    text = text_for(language)
    return (
        header_html(language), gr.update(placeholder=text["message"]),
        gr.update(placeholder=text["criteria"]), gr.update(value=text["reset"]),
        gr.update(value=text["approve"]), gr.update(value=text["go"]),
        gr.update(value=f"◐ {text['theme']}"),
    )


def initialize_language(browser_language: str) -> str:
    return "Español" if (browser_language or "").lower().startswith("es") else "English"


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick, gr.update(interactive=True)


async def process_message(sidekick, message, success_criteria, history, language):
    if sidekick is None:
        return history, gr.update(visible=False), sidekick
    results = await sidekick.run_turn(message, success_criteria, history, language)
    return results, gr.update(visible=sidekick.paused), sidekick


async def approve(sidekick, history):
    results = await sidekick.resume(history)
    return results, gr.update(visible=sidekick.paused), sidekick


def watch_todos(sidekick, language):
    return render_todos(sidekick.todos if sidekick else [], language)


async def reset(sidekick):
    if sidekick:
        sidekick.cleanup()
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, gr.update(visible=False), new_sidekick


def free_resources(sidekick):
    if sidekick:
        sidekick.cleanup()


with gr.Blocks(title="Sidekick", delete_cache=(3600, 86400)) as ui:
    sidekick = gr.State(delete_callback=free_resources)
    with gr.Row(elem_id="title-row"):
        with gr.Column(scale=1, min_width=0, elem_id="header-copy"):
            header = gr.HTML(header_html("English"), elem_id="sidekick-header")
        with gr.Column(scale=0, min_width=170, elem_id="interface-controls"):
            gr.Markdown("Idioma / Language", elem_id="language-label")
            language = gr.Dropdown(
                choices=["Español", "English"], value="English", show_label=False,
                container=False, interactive=True, elem_id="language-selector",
            )
            theme_button = gr.Button("◐ Theme", elem_id="theme-button")

    with gr.Row(elem_id="workspace-row"):
        chatbot = gr.Chatbot(show_label=False, height=430, scale=3, elem_id="sidekick-chat")
        with gr.Column(scale=1, min_width=230):
            todos_panel = gr.HTML(render_todos([], "English"), elem_id="plan-panel")
    with gr.Group(elem_id="ask-panel"):
        message = gr.Textbox(
            show_label=False, placeholder=UI_TEXT["English"]["message"],
            container=False, elem_id="message-input",
        )
        success_criteria = gr.Textbox(
            show_label=False, placeholder=UI_TEXT["English"]["criteria"],
            container=False, elem_id="criteria-input",
        )
    with gr.Row(elem_id="action-row"):
        reset_button = gr.Button(UI_TEXT["English"]["reset"], elem_id="reset-button")
        approve_button = gr.Button(
            UI_TEXT["English"]["approve"], visible=False, elem_id="approve-button",
        )
        go_button = gr.Button(
            UI_TEXT["English"]["go"], variant="primary", elem_id="go-button", interactive=False,
        )

    timer = gr.Timer(1)
    browser_language = gr.Textbox(visible=False)
    ui.load(setup, [], [sidekick, go_button])
    detect_language = ui.load(
        initialize_language, browser_language, language, js="() => navigator.language || ''",
    )
    detect_language.then(
        localized_ui, language,
        [header, message, success_criteria, reset_button, approve_button, go_button, theme_button],
    )
    timer.tick(watch_todos, [sidekick, language], todos_panel, show_progress="hidden")
    request_inputs = [sidekick, message, success_criteria, chatbot, language]
    request_outputs = [chatbot, approve_button, sidekick]
    message.submit(process_message, request_inputs, request_outputs)
    success_criteria.submit(process_message, request_inputs, request_outputs)
    go_button.click(process_message, request_inputs, request_outputs)
    approve_button.click(approve, [sidekick, chatbot], [chatbot, approve_button, sidekick])
    reset_button.click(reset, sidekick, [message, success_criteria, chatbot, approve_button, sidekick])
    language.change(
        localized_ui, language,
        [header, message, success_criteria, reset_button, approve_button, go_button, theme_button],
        js="(language) => { document.title = language === 'Español' ? 'Sidekick — Asistente personal' : 'Sidekick — Personal coworker'; return language; }",
    )
    theme_button.click(fn=None, js="() => window.toggleSidekickTheme()")

ui.queue(default_concurrency_limit=1)

if __name__ == "__main__":
    ui.launch(inbrowser=True, **LAUNCH_STYLE)
