"""Static guards for the dashboard modules (no browser needed).

The CV Studio once crashed on load because it destructured a helper (`navlink`)
that `uiKit()` did not provide. These checks keep the module contract honest.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dashboard'


def _kit_names():
    source = (ROOT / 'js' / 'ui.js').read_text(encoding='utf-8')
    body = re.search(r'function uiKit\(\)\{return \{(.*?)\};\}', source).group(1)
    return {part.split(':')[0].strip() for part in body.split(',') if part.strip()}


def test_modules_only_use_helpers_they_receive_from_ui_kit():
    provided = _kit_names()
    ui_source = (ROOT / 'js' / 'ui.js').read_text(encoding='utf-8')
    ui_helpers = set(re.findall(r'^(?:async )?function (\w+)\(', ui_source, re.M))
    for module in ('cv-studio.js', 'career-ai.js'):
        source = (ROOT / 'js' / module).read_text(encoding='utf-8')
        received = set()
        for match in re.finditer(r'const \{([^}]*)\}=ui;', source):
            received |= {name.strip() for name in match.group(1).split(',') if name.strip()}
        assert received <= provided, (module, sorted(received - provided))
        local = set(re.findall(r'function (\w+)\(', source)) | set(re.findall(r'(?:const|let) (\w+)=', source))
        for helper in ui_helpers:
            if re.search(r'(?<![\w.])' + helper + r'\(', source) and helper not in local:
                assert helper in received, f'{module} calls {helper}() without receiving it from uiKit()'


def test_hidden_attribute_wins_over_button_display_rules():
    css = (ROOT / 'css' / 'mihna.css').read_text(encoding='utf-8')
    assert '[hidden]{display:none!important}' in css
    assert 'mihna.css' in (ROOT / 'css' / 'style.css').read_text(encoding='utf-8-sig')


def test_tailoring_source_selector_lists_only_original_cvs():
    source = (ROOT / 'js' / 'cv-studio.js').read_text(encoding='utf-8')
    assert "c.cv_kind!=='tailored').map(c=>[c.id,c.name]),'Choisir le CV original'" in source


def test_dashboard_modules_parse_as_es_modules():
    """`node --check file.js` does not parse ES modules strictly; check every module in module mode."""
    import shutil
    import subprocess
    node = shutil.which('node')
    if not node:
        import pytest
        pytest.skip('Node.js absent : vérification syntaxique JavaScript non exécutée.')
    for path in sorted((ROOT / 'js').glob('*.js')):
        result = subprocess.run([node, '--input-type=module', '--check'], input=path.read_bytes(), capture_output=True)
        assert result.returncode == 0, (path.name, result.stderr.decode(errors='replace')[-400:])
