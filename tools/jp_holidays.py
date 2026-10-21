"""日本の祝日（祝日法のルールで計算。外部ライブラリなし、1980〜2099年向け）。"""
import datetime as dt


def _nth_monday(y, m, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(7 - d.weekday()) % 7)   # 最初の月曜
    return d + dt.timedelta(weeks=n - 1)


def _base(y):
    h = {dt.date(y, 1, 1): "元日", dt.date(y, 2, 11): "建国記念の日", dt.date(y, 2, 23): "天皇誕生日",
         dt.date(y, 4, 29): "昭和の日", dt.date(y, 5, 3): "憲法記念日", dt.date(y, 5, 4): "みどりの日",
         dt.date(y, 5, 5): "こどもの日", dt.date(y, 8, 11): "山の日", dt.date(y, 11, 3): "文化の日",
         dt.date(y, 11, 23): "勤労感謝の日",
         _nth_monday(y, 1, 2): "成人の日", _nth_monday(y, 7, 3): "海の日",
         _nth_monday(y, 9, 3): "敬老の日", _nth_monday(y, 10, 2): "スポーツの日"}
    k = y - 1980
    h[dt.date(y, 3, int(20.8431 + 0.242194 * k - k // 4))] = "春分の日"
    h[dt.date(y, 9, int(23.2488 + 0.242194 * k - k // 4))] = "秋分の日"
    return h


def holidays(y):
    h = _base(y)
    # 振替休日：日曜の祝日のあと、最初の祝日でない日
    for d in sorted(h):
        if d.weekday() == 6:
            n = d + dt.timedelta(days=1)
            while n in h: n += dt.timedelta(days=1)
            h[n] = "振替休日"
    # 国民の休日：祝日に挟まれた平日
    for d in sorted(h):
        n = d + dt.timedelta(days=2)
        mid = d + dt.timedelta(days=1)
        if n in h and mid not in h and mid.weekday() != 6:
            h[mid] = "国民の休日"
    return h


_cache = {}


def name(d):
    if d.year not in _cache: _cache[d.year] = holidays(d.year)
    return _cache[d.year].get(d)
