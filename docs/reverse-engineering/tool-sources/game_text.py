"""Decode game text through Windows CP936, retaining legacy private-use mappings."""
import ctypes
import os


def decode_game_text(raw):
    if not raw:return ''
    if os.name!='nt':return raw.decode('gbk')
    convert=ctypes.windll.kernel32.MultiByteToWideChar
    convert.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_char_p,ctypes.c_int,
                      ctypes.POINTER(ctypes.c_wchar),ctypes.c_int]
    convert.restype=ctypes.c_int
    count=convert(936,8,raw,len(raw),None,0)
    if not count:raise UnicodeDecodeError('cp936',raw,0,len(raw),'Windows CP936 conversion failed')
    output=ctypes.create_unicode_buffer(count)
    if convert(936,8,raw,len(raw),output,count)!=count:
        raise ValueError('Inconsistent Windows CP936 conversion length')
    return output[:count]


def visible_text(text):
    return ''.join(f'\\u{ord(char):04X}' if 0xE000<=ord(char)<=0xF8FF else char for char in text)
