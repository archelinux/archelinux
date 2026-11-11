#!/usr/bin/env python3
"""Build the 4K vector wallpaper from the standalone Arche SVG symbol."""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', ns)
symbol = ET.parse(root / 'assets/arche-logo.svg').getroot()
assert symbol.attrib['viewBox'] == '0 0 208 208'
wallpaper = ET.Element(f'{{{ns}}}svg', {
    'width': '3840', 'height': '2160', 'viewBox': '0 0 3840 2160',
    'role': 'img', 'aria-labelledby': 'title',
})
ET.SubElement(wallpaper, f'{{{ns}}}title', {'id': 'title'}).text = 'Arche 4K wallpaper'
ET.SubElement(wallpaper, f'{{{ns}}}path', {'fill': '#000', 'd': 'M0 0H3840V2160H0Z'})
group = ET.SubElement(wallpaper, f'{{{ns}}}g', {
    'transform': f'translate(1600 760) scale({640 / 208})',
})
for child in symbol:
    if child.tag != f'{{{ns}}}title':
        group.append(deepcopy(child))
ET.indent(wallpaper)
data = ET.tostring(wallpaper, encoding='unicode') + '\n'
for path in (
    root / 'assets/arche-wallpaper-4k.svg',
    root / 'pkgs/arche-tui-stack/files/usr/share/backgrounds/archelinux/litho-dark.svg',
):
    path.write_text(data)
    print(f'Wrote {path}')
