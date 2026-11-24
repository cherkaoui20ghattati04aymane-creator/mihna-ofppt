'use strict';
/* État Gemini honnête : « connecté » uniquement après un test réel réussi. La clé n'est jamais transmise au navigateur. */
export function geminiStatusBox(ui, initial, onChange) {
  const {h, api, button, badge, toast} = ui;
  const box = h('div', {class: 'gemini-status', 'aria-live': 'polite'});
  let status = initial || {enabled: false, state: 'disabled', label: 'Gemini indisponible', reasons: []};
  const colors = {connected: 'green', configured: 'amber', error: 'amber', disabled: 'gray'};
  function render() {
    const parts = [h('div', {class: 'suggestion-head'}, badge(status.label || 'Gemini', colors[status.state] || 'gray'))];
    if (status.reasons?.length) parts.push(h('ul', {class: 'match-details'}, status.reasons.map(r => h('li', {}, r))));
    const check = status.last_check;
    if (check) parts.push(h('p', {class: 'meta'}, 'Dernier test réel : ' + (check.ok ? 'réussi' : 'échec — ' + (check.error_label || '')) +
      ' · modèle ' + check.model + ' · ' + check.latency_ms + ' ms · ' + new Date(check.checked_at).toLocaleTimeString('fr-FR')));
    if (status.enabled) {
      parts.push(h('div', {class: 'actions'}, button('Tester la connexion Gemini', async () => {
        const r = await api('/ai/verify', {method: 'POST', body: {}});
        status = r.status; render(); onChange?.(status);
        toast(r.result.ok ? 'Gemini répond : connexion réelle confirmée.' : 'Test Gemini échoué : ' + (r.result.message || r.result.error_label), !r.result.ok);
      }, false, 'spark')));
      parts.push(h('p', {class: 'meta'}, 'Le test envoie une phrase courte, sans aucune donnée personnelle. Le mode local reste toujours disponible.'));
    } else {
      parts.push(h('p', {class: 'meta'}, 'Le mode local fonctionne sans connexion. Pour activer Gemini : renseignez GEMINI_ENABLED, GEMINI_API_KEY et GEMINI_FREE_TIER_CONFIRMED dans .env puis redémarrez.'));
    }
    box.replaceChildren(...parts);
  }
  render();
  return box;
}
