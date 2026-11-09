"""เทียบคำอ่านใน tools/name_readings.tsv กับแม่แบบ {{zh-pron}} ของ Wiktionary

ใช้: python tools/check_readings_wikt.py <โฟลเดอร์หน้า raw> [--fetch]
  --fetch  ดาวน์โหลดหน้า raw (action=raw) ของทุกอักษรลงโฟลเดอร์ก่อน
ผล: พิมพ์อักษรที่คำอ่านใน TSV ไม่อยู่ในรายการของ Wiktionary พร้อมหมายเหตุ literary/vernacular

การแปลงอักขรวิธี
- ฮกเกี้ยน: Wiktionary ใช้ POJ มีเครื่องหมายเสียง → แปลงเป็นไท่หลอเลขเสียง
- แต้จิ๋ว: Wiktionary ใช้ e = [ɯ], ê = [e] ส่วนตารางโครงการใช้ ê = [ɯ], e = [e]
  จึงสลับ e/ê ยกเว้นหลัง i/u (iê, uê หมายถึง [ie] [ue] ทั้งสองระบบ)
"""
import io, os, re, sys, time, unicodedata, urllib.parse, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = os.path.join(ROOT, 'tools', 'name_readings.tsv')
GENERAL = {'tw', 'xm', 'tp', 'kh'}  # ไต้หวันทั่วไป / เซี่ยเหมิน / ไทเป / เกาสง


def page_path(d, c):
    return os.path.join(d, f'{ord(c[0]):x}{"_" + str(len(c)) if len(c) > 1 else ""}.txt')


def fetch(d, chars):
    os.makedirs(d, exist_ok=True)
    for c in chars:
        p = page_path(d, c)
        if os.path.exists(p):
            continue
        url = 'https://en.wiktionary.org/w/index.php?title=' + urllib.parse.quote(c) + '&action=raw'
        req = urllib.request.Request(url, headers={'User-Agent': 'translate-project-reading-check/1.0'})
        open(p, 'w', encoding='utf-8').write(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))
        time.sleep(0.25)


TONE = {'́': 2, '̀': 3, '̂': 5, '̌': 6, '̄': 7, '̍': 8}


def poj_to_tl(s):
    out = []
    for syl in s.split('-'):
        syl = unicodedata.normalize('NFD', syl.strip().lower())
        tone = None
        for k, v in TONE.items():
            if k in syl:
                tone = v
                syl = syl.replace(k, '')
        syl = syl.replace('͘', 'o').replace('ⁿ', 'nn')  # o͘ → oo
        syl = unicodedata.normalize('NFC', syl)
        syl = syl.replace('chh', 'tsh').replace('ch', 'ts')
        syl = re.sub(r'oa', 'ua', syl)
        syl = re.sub(r'oe', 'ue', syl)
        syl = re.sub(r'eng$', 'ing', syl)
        syl = re.sub(r'ek$', 'ik', syl)
        if tone is None:
            tone = 4 if re.search(r'[ptkh]$', syl) else 1
        out.append(f'{syl}{tone}')
    return ' '.join(out)


def md_num(p):
    """พินอินมีเครื่องหมายเสียง → เลขเสียง ü = v (เหมือน translit_names.pinyin_to_num)"""
    s = unicodedata.normalize('NFD', p.lower())
    tone = 5
    for k, v in {'̄': 1, '́': 2, '̌': 3, '̀': 4}.items():
        if k in s:
            tone = v
            s = s.replace(k, '')
    return s.replace('ü', 'v') + str(tone)


def wikt_tc_to_project(s):
    s = re.sub(r'(?<![iu])ê', '\0', s)
    s = re.sub(r'(?<![iu])e', 'ê', s)
    return s.replace('\0', 'e')


def tc_note_to_project(note):
    # สลับ e/ê เฉพาะคำที่เป็นเป่งอิม (ลงท้ายด้วยเลขเสียง) ไม่ยุ่งกับข้อความอังกฤษ
    return re.sub(r'[a-zê]+[1-8]', lambda m: wikt_tc_to_project(m.group(0)), note)


def clauses(note):
    """แยกหมายเหตุเป็นวลี ด้วย ; ขึ้นบรรทัดใหม่ และจุลภาคที่ตามด้วยข้อความรูป “คำอ่าน - หมายเหตุ”
    (เช่น “khùi - vernacular, khì - literary” แต่ไม่แยก “pek - literary, surname”)
    แยกเฉพาะระดับนอกวงเล็บ เช่นไม่ผ่า “(Jinjiang, Philippines)”"""
    out, buf, depth = [], '', 0
    for i, ch in enumerate(note):
        depth += (ch == '(') - (ch == ')')
        if depth == 0 and (ch in ';\n' or (ch == ',' and re.match(r',\s*[^,;()]*\s-\s', note[i:]))):
            out.append(buf)
            buf = ''
        else:
            buf += ch
    return out + [buf]


POJ_TOKEN = re.compile(r"[a-zA-ZÀ-ɏ̀-ͯⁿ͘-]+")


TC_OTHER = ('Chaozhou', 'Jieyang', 'Chaoyang', 'Chenghai', 'Raoping', 'Puning', 'Huilai')


def tc_non_shantou(note):
    """คำอ่านแต้จิ๋วที่หมายเหตุระบุว่าเป็นของสำเนียงอื่น ไม่ใช่ซัวเถา"""
    res = set()

    def other(place):
        return 'Shantou' not in place and any(p in place for p in TC_OTHER)
    # “diên1 (Chaozhou)” และ “(ling5 - Chenghai)” ในวงเล็บ: ตัดเฉพาะคำอ่านในวงเล็บนั้น
    for rd, place in re.findall(r'([a-zê]+[1-8])\s*\(([^)-]*)\)', note):
        if other(place):
            res.add(rd)
    for rds, place in re.findall(r'\(([a-zê0-9/ ]+) - ([^)]*)\)', note):
        if other(place):
            res |= set(re.findall(r'[a-zê]+[1-8]', rds))
    # “io5 - Shantou; iê5 - Chaozhou”: ดูเฉพาะข้อความนอกวงเล็บ
    for seg in clauses(re.sub(r'\([^)]*\)', '', note)):
        if ' - ' in seg:
            rds, place = seg.split(' - ', 1)
            if other(place):
                res |= set(re.findall(r'[a-zê]+[1-8]', rds))
    return res


def literary(note, conv, token):
    """ดึงคำอ่านที่หมายเหตุระบุว่า literary เฉพาะ token ที่มีรูปตรงระบบอักษรโรมันของภาษานั้น
    (ฮกเกี้ยน: POJ ไม่มีเลข; แต้จิ๋ว: เป่งอิมมีเลขเสียง) เพื่อไม่ให้ข้อความอังกฤษหรือระบบอื่นหลุดเข้ามา"""
    res = set()
    for seg in clauses(note):
        if ' - ' in seg and 'literary' in seg.split(' - ', 1)[1]:
            for rd in re.split(r'[/,]', seg.split(' - ', 1)[0].split(':')[-1]):
                rd = re.sub(r'\(.*?\)', '', rd).strip()
                if rd and token.fullmatch(rd):
                    res.add(conv(rd))
    return res


def blocks(text):
    for m in re.finditer(r'\{\{zh-pron(.*?)\n\}\}', text, re.S):
        f = {}
        for line in m.group(1).split('\n|'):
            if '=' in line:
                k, v = line.split('=', 1)
                f[k.strip().lstrip('|')] = v.strip()
        yield f


def hk_candidates(mn):
    res = []
    for item in mn.split('/'):
        if ':' in item:
            regs, rd = item.split(':', 1)
            regs = set(regs.split(','))
        else:
            regs, rd = set(), item
        rd = re.sub(r'\(.*?\)', '', rd).strip()
        if rd:
            res.append((poj_to_tl(rd), regs))
    return res


def main():
    d = sys.argv[1]
    rows = [l.rstrip('\n').split('\t') for l in open(TSV, encoding='utf-8')
            if l.strip() and not l.startswith('#')]
    if '--fetch' in sys.argv:
        fetch(d, [r[0] for r in rows])
    bad = 0
    unlabeled = []
    for r in rows:
        tc_labeled_st = set()
        c, md, hk, tc = r[0], r[1], r[2], r[3]
        p = page_path(d, c)
        if not os.path.exists(p):
            print(f'{c}\tไม่มีหน้า')
            continue
        hks, tcs, notes, hk_lit, tc_lit, tc_other = [], [], [], set(), set(), set()
        bl = list(blocks(open(p, encoding='utf-8').read()))

        def m_list(f):
            # จีนกลาง: บางหน้าเขียน m=<อักษรจีน> (ให้แม่แบบเติมพินอินเอง) ไม่นับเป็นพินอิน
            return [md_num(x.strip()) for x in f.get('m', '').split(',')
                    if x.strip() and '=' not in x and not re.search(r'[一-鿿]', x)]

        def m_placeholder(f):
            return bool(re.search(r'[一-鿿]', f.get('m', '')))
        mds = [x for f in bl for x in m_list(f)]
        # ใช้บล็อกที่ตรงกับพินอินที่เลือก (เสียงคนละความหมายไม่ปนกัน) รวมกับบล็อก m=<อักษรจีน>
        # ซึ่งผูกพินอินไม่ได้แต่เป็นเสียงหลักของหน้า (เช่น 一 叔 突) ถ้าไม่มีบล็อกใดตรง ใช้ทุกบล็อก
        sel = [f for f in bl if md in m_list(f) or m_placeholder(f)]
        if not any(md in m_list(f) for f in sel):
            sel = bl
        for f in sel:
            if 'mn' in f:
                hks += hk_candidates(f['mn'])
                if 'mn_note' in f:
                    notes.append('HK[' + f.get('m', '?') + ']: ' + f['mn_note'])
                    hk_lit |= literary(f['mn_note'], poj_to_tl, POJ_TOKEN)
            if 'mn-t' in f:
                tcs += [wikt_tc_to_project(x.strip()) for x in f['mn-t'].split('/') if x.strip()]
                if 'mn-t_note' in f:
                    n = tc_note_to_project(f['mn-t_note'])
                    notes.append('TC[' + f.get('m', '?') + ']: ' + n)
                    tc_lit |= literary(n, lambda x: x, re.compile(r'[a-zê]+[1-8]'))
                    tc_other |= tc_non_shantou(n)
                    # คำอ่านที่หมายเหตุระบุว่าเป็นซัวเถาโดยตรง
                    tc_labeled_st.update(re.findall(r'([a-zê]+[1-8])\s*\([^)]*Shantou', n))
                    for seg in clauses(n):
                        if 'Shantou' in seg and ' - ' in seg:
                            tc_labeled_st.update(re.findall(r'[a-zê]+[1-8]', seg.split(' - ', 1)[0]))
        # แต้จิ๋ว: ตัดคำอ่านที่หมายเหตุระบุว่าเป็นของสำเนียงอื่น (ตารางยึดซัวเถา)
        tc_all = tcs
        tcs = [x for x in tcs if x not in tc_other]
        tc_lit -= tc_other
        hk_set = {h for h, _ in hks}
        flags = []
        if tc_all and not tcs:
            flags.append(f'TC ไม่มีคำอ่านซัวเถา (แหล่งให้เฉพาะสำเนียงอื่น: {tc_all})')
        elif tc in tcs and tc not in tc_labeled_st:
            unlabeled.append(c)
        if mds and md not in mds:
            flags.append(f'MD {md} ∉ {mds}')
        if hks and hk not in hk_set:
            gen = sorted({h for h, regs in hks if not regs or regs & GENERAL})
            flags.append(f'HK {hk} ∉ {gen or sorted(hk_set)}')
        elif hk_lit and hk not in hk_lit:
            flags.append(f'HK {hk} ไม่ใช่ literary {sorted(hk_lit)}')
        if tcs and tc not in tcs:
            flags.append(f'TC {tc} ∉ {tcs}')
        elif tc_lit and tc not in tc_lit:
            flags.append(f'TC {tc} ไม่ใช่ literary {sorted(tc_lit)}')
        if not hks:
            flags.append('HK: Wiktionary ไม่มีข้อมูล')
        if not tc_all:
            flags.append('TC: Wiktionary ไม่มีข้อมูล')
        if flags:
            bad += 1
            print(f'{c}\t' + ' | '.join(flags) + ('\n\t' + '\n\t'.join(notes) if notes else ''))
    print(f'\nแต้จิ๋วที่ตรงแหล่งแต่แหล่งไม่ได้ระบุจุดสำเนียง (ยังไม่ยืนยันว่าเป็นซัวเถา) {len(unlabeled)} อักษร')
    print(f'รวม {len(rows)} อักษร มีข้อสังเกต {bad}')


if __name__ == '__main__':
    main()
