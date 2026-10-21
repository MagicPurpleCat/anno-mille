"""Шапка установщика: знак и надпись ANNO MILLE из логотипа главного меню -> tools/installer_header.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logo  # noqa: E402

im = logo.menu_logo("C")
im = im.crop(im.getbbox())
k = 470 / im.width
im = im.resize((470, round(im.height * k)), logo.Image.LANCZOS)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "installer_header.png")
im.save(out)
print(out, im.size)
