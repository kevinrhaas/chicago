/* Classic, tiny head script: share appearance across portal and renderer before paint. */
(() => {
  const keys = ['scifi', 'spaceage', 'steampunk'];
  let skin = 'scifi';
  try { const saved = localStorage.getItem('chicago4d.skin'); if (keys.includes(saved)) skin = saved; } catch {}
  document.documentElement.dataset.skin = skin;
  try { document.documentElement.dataset.theme = localStorage.getItem('chicago4d.theme') || (skin === 'spaceage' ? 'light' : 'dark'); } catch {}
  try { if (Number(sessionStorage.getItem('chicago4d.transfer')) > Date.now() - 15000) document.documentElement.dataset.transfer = 'true'; } catch {}
  function apply(value) {
    if (!keys.includes(value)) return;
    document.documentElement.dataset.skin = value;
    const tone = value === 'spaceage' ? 'light' : 'dark';
    document.documentElement.dataset.theme = tone;
    try { localStorage.setItem('chicago4d.theme', tone); } catch {}
    document.querySelectorAll('[data-skin-choice]').forEach(select => { select.value = value; });
    try { localStorage.setItem('chicago4d.skin', value); } catch {}
  }
  document.addEventListener('DOMContentLoaded', () => {
    let choice = document.getElementById('skin-choice');
    if (!choice && document.querySelector('.gate-card')) {
      const controls = document.createElement('div'); controls.className = 'skin-tools';
      const home = new URL('../', document.baseURI);
      controls.innerHTML = '<a>All periods</a><label>Interface <select aria-label="Interface appearance"><option value="scifi">Sci-fi</option><option value="spaceage">Space Age · 1960s</option><option value="steampunk">Steampunk</option></select></label>';
      controls.querySelector('a').href = home.href;
      document.querySelector('.gate-card').append(controls);
      choice = controls.querySelector('select');
    }
    const settings = document.querySelector('[data-panel="settings"]');
    if (settings && choice) {
      const group = document.createElement('div'); group.className = 'settings-group skin-tools';
      const label = document.createElement('label'); label.textContent = 'Interface appearance ';
      const setting = choice.cloneNode(true); setting.removeAttribute('id'); label.append(setting); group.append(label); settings.prepend(group);
      setting.dataset.skinChoice = ''; setting.value = skin; setting.addEventListener('change', () => apply(setting.value));
    }
    if (choice) { choice.dataset.skinChoice = ''; choice.value = skin; choice.addEventListener('change', () => apply(choice.value)); }
  });
})();
