"""Shared chatbot visual language with light and dark Sidekick themes."""

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --bg:#f1f3ed; --surface:#ffffff; --raised:#e7ebe3; --border:#b8c0b8;
  --text:#111412; --muted:#626b64; --acid:#9dcc16; --acid-text:#111412;
  --orange:#e95735; --blue:#157fa8; --grid:rgb(17 20 18 / 5%);
  --shadow:rgb(17 20 18 / 14%); --mono:'DM Mono',monospace; --sans:'Manrope',sans-serif;
}
html[data-sidekick-theme='dark'] {
  --bg:#111412; --surface:#181c19; --raised:#202522; --border:#343a35;
  --text:#e9e9e3; --muted:#909690; --acid:#c7ff37; --acid-text:#111412;
  --orange:#ff6947; --blue:#209dd7; --grid:rgb(255 255 255 / 2.5%); --shadow:rgb(0 0 0 / 24%);
  color-scheme:dark;
}
footer,.built-with,.show-api,.api-docs { display:none!important; }
html,body,gradio-app { background:var(--bg)!important; color:var(--text)!important; }
body { background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px)!important; background-size:42px 42px!important; }
.gradio-container { width:100%!important; max-width:1080px!important; min-width:0!important; margin:0 auto!important; padding:34px 24px 48px!important; background:transparent!important; color:var(--text)!important; font-family:var(--sans)!important; }
.gradio-container * { min-width:0; }
.block,.form { background:transparent!important; box-shadow:none!important; }
.chatbot,.chatbot *,.block,.form,button,input,textarea { border-radius:0!important; }

#title-row { align-items:center!important; flex-wrap:nowrap!important; gap:28px!important; margin-bottom:28px!important; padding-bottom:20px!important; border-bottom:3px solid var(--text)!important; }
#header-copy,#sidekick-header { margin:0!important; padding:0!important; }
.sidekick-brand { display:grid; grid-template-columns:auto 1fr; align-items:center; gap:20px; }
.sidekick-mark { display:grid; grid-template-columns:repeat(2,18px); grid-template-rows:repeat(2,18px); gap:4px; width:40px; }
.mark-block { display:block; }.mark-acid{background:var(--acid)}.mark-blue{background:var(--blue)}.mark-orange{background:var(--orange);grid-column:2}
.sidekick-headings p { margin:0!important; }
.sidekick-eyebrow { color:var(--muted)!important; font:400 9px var(--mono)!important; letter-spacing:.12em; text-transform:uppercase; }
.sidekick-headings h1 { margin:4px 0!important; color:var(--text)!important; font:800 clamp(1.8rem,4vw,2.6rem)/.95 var(--sans)!important; letter-spacing:-.055em!important; }
.sidekick-headings h1 span { color:var(--acid); font-weight:400; }
.sidekick-subtitle { color:var(--muted)!important; font:400 11px var(--mono)!important; letter-spacing:.04em; }
#interface-controls { width:180px!important; min-width:180px!important; max-width:180px!important; flex:0 0 180px!important; gap:7px!important; margin-left:auto!important; }
#language-label p { margin:0!important; color:var(--muted)!important; font:400 10px var(--mono)!important; letter-spacing:.08em; text-transform:uppercase; }
#language-selector .wrap,
#language-selector .secondary-wrap,
#language-selector .wrap-inner,
#language-selector input,
#language-selector button {
  min-height:34px!important; height:34px!important; border-color:var(--border)!important;
  background:var(--surface)!important; color:var(--text)!important;
}
#language-selector input { font:400 11px var(--mono)!important; letter-spacing:.04em!important; }
#language-selector button svg { fill:var(--text)!important; color:var(--text)!important; }
#language-selector .wrap:focus-within { border-color:var(--acid)!important; box-shadow:0 0 0 1px var(--acid)!important; }
#language-selector [role='listbox'],
#language-selector ul,
body > [data-radix-popper-content-wrapper] [role='listbox'] {
  border-color:var(--border)!important; background:var(--surface)!important; color:var(--text)!important;
}
#language-selector [role='option'],
body > [data-radix-popper-content-wrapper] [role='option'] {
  background:var(--surface)!important; color:var(--text)!important; font:400 11px var(--mono)!important;
}
#language-selector [role='option'][data-highlighted],
body > [data-radix-popper-content-wrapper] [role='option'][data-highlighted] {
  background:var(--raised)!important; color:var(--text)!important;
}
#theme-button { min-height:34px!important; height:34px!important; }

#workspace-row { align-items:stretch!important; gap:18px!important; }
#sidekick-chat { height:430px!important; min-height:430px!important; border:1px solid var(--border)!important; background:color-mix(in srgb,var(--surface) 94%,transparent)!important; box-shadow:14px 14px 0 var(--shadow)!important; }
.message-row :is(.message,.message-bubble,.bubble),.message-row :is(.message,.message-bubble,.bubble) :is(p,li) { font:400 16px/1.65 var(--sans)!important; }
.message-row.user-row .message,.message-row[data-role='user'] .message { background:var(--acid)!important; color:var(--acid-text)!important; }
.message-row.user-row .message *,.message-row[data-role='user'] .message * { color:var(--acid-text)!important; }
.message-row.bot-row .message,.message-row.bot-row .message-bubble,.message-row[data-role='assistant'] .message,.message-row[data-role='assistant'] .message-bubble { border-left:2px solid var(--orange)!important; background:var(--raised)!important; color:var(--text)!important; padding-left:18px!important; }
.message-row :is(code,pre) { font-family:var(--mono)!important; }
#sidekick-chat .icon-button,#sidekick-chat button.icon-button { min-width:0!important; min-height:0!important; width:auto!important; height:auto!important; padding:4px!important; border:0!important; background:transparent!important; color:var(--muted)!important; box-shadow:none!important; }

#plan-panel { height:100%; min-height:430px; padding:20px!important; border:1px solid var(--border)!important; background:var(--surface)!important; }
#plan-panel h3 { margin:0 0 18px!important; padding-bottom:10px; border-bottom:2px solid var(--acid); color:var(--text)!important; font:500 11px var(--mono)!important; letter-spacing:.14em; text-transform:uppercase; }
#plan-panel ul { list-style:none; padding:0; margin:0; }
#plan-panel li { display:flex; align-items:flex-start; gap:10px; margin:12px 0; color:var(--text); font:500 13px/1.45 var(--sans); }
.plan-placeholder { color:var(--muted); font:400 13px/1.55 var(--sans); }
.plan-mark { flex:none; width:10px; height:10px; margin-top:4px; border:2px solid var(--border); background:transparent; }
#plan-panel li.in_progress .plan-mark { border-color:var(--blue); background:var(--blue); }
#plan-panel li.completed { color:var(--muted); text-decoration:line-through; }
#plan-panel li.completed .plan-mark { border-color:var(--acid); background:var(--acid); }

#ask-panel { gap:0!important; margin-top:24px!important; border:1px solid var(--border)!important; background:var(--surface)!important; }
#ask-panel>div { gap:0!important; }
textarea,input[type='text'] { min-height:52px!important; padding:14px 15px!important; border:0!important; border-bottom:1px solid var(--border)!important; background:var(--surface)!important; color:var(--text)!important; font:400 16px/1.5 var(--sans)!important; }
#criteria-input textarea { border-bottom:0!important; }
textarea:focus,input[type='text']:focus { outline:none!important; box-shadow:inset 3px 0 0 var(--acid)!important; }
textarea::placeholder,input::placeholder { color:var(--muted)!important; opacity:1!important; }
#action-row { gap:8px!important; margin-top:10px!important; }
button { min-height:48px!important; border:1px solid var(--border)!important; background:var(--surface)!important; color:var(--text)!important; font:500 11px/1.2 var(--mono)!important; letter-spacing:.09em!important; text-transform:uppercase!important; }
button:hover { border-color:var(--blue)!important; color:var(--blue)!important; }
#go-button { border-color:var(--acid)!important; background:var(--acid)!important; color:var(--acid-text)!important; }
#approve-button { border-color:var(--orange)!important; background:var(--orange)!important; color:#111412!important; }
#reset-button:hover { border-color:var(--orange)!important; color:var(--orange)!important; }

@media (max-width:760px) {
  .gradio-container{padding:22px 14px 34px!important} #title-row{flex-wrap:wrap!important;gap:16px!important}
  #interface-controls{width:100%!important;max-width:none!important;margin-left:0!important}
  #workspace-row{flex-direction:column!important} #sidekick-chat{box-shadow:8px 8px 0 var(--shadow)!important}
  #plan-panel{min-height:180px} .message-row :is(.message,.message-bubble,.bubble),.message-row :is(.message,.message-bubble,.bubble) :is(p,li){font-size:15px!important}
}
"""

JS = r"""
() => {
  const root = document.documentElement;
  const preferred = localStorage.getItem('sidekick-theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  root.dataset.sidekickTheme = preferred;
  window.toggleSidekickTheme = () => {
    const next = root.dataset.sidekickTheme === 'dark' ? 'light' : 'dark';
    root.dataset.sidekickTheme = next;
    localStorage.setItem('sidekick-theme', next);
  };
  document.title = (navigator.language || '').toLowerCase().startsWith('es')
    ? 'Sidekick — Asistente personal' : 'Sidekick — Personal coworker';
  setTimeout(() => document.querySelector('#message-input textarea')?.focus(), 400);
}
"""
