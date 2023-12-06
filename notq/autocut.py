from notq.constants import *

def autocut_approx_height(s, is_compact_rendering):
    res = (len(s) + AUTOCUT_LINE_LEN - 1) // AUTOCUT_LINE_LEN
    if not is_compact_rendering:
        # suuper rough check for some bigger things
        res += s.count('<img') * AUTOCUT_IMAGE_HEIGHT # like images
        res += min(s.count('http'), s.count('youtu')) * AUTOCUT_YOUTUBE_HEIGHT # and youtube embeds
    return res

def autocut_at_delim(text, approx_height, is_compact_rendering, delim):
    fragments = text.split(delim)
    height = 0
    res = ""
    for f in fragments:
        if res:
            res += delim
        res += f
        height += autocut_approx_height(f, is_compact_rendering)
        if height > 0.9 * approx_height and height < 1.5 * approx_height:
            return res
        elif height >= 1.5 * approx_height:
            return None
    return text

def autocut_crude(text, approx_height, is_compact_rendering):
    while autocut_approx_height(text, is_compact_rendering) > 1.5 * approx_height:
        l = len(text) * 4 // 5
        text = text[:l]
    return text

def autocut(text, approx_height, is_compact_rendering):
    if autocut_approx_height(text, is_compact_rendering) < approx_height:
        return text
    res = autocut_at_delim(text, approx_height, is_compact_rendering, '\n')
    if not res:
        res = autocut_at_delim(text, approx_height, is_compact_rendering, ' ')
    if not res:
        res = autocut_crude(text, approx_height, is_compact_rendering)
    return res
