"""สร้างคอลัมน์ชื่อไทย (จีนกลาง) (ฮกเกี้ยน) (แต้จิ๋ว) ใน fengshen-characters.md

ใช้: python tools/translit_names.py   (รันจากที่ใดก็ได้)
- คำอ่านรายตัวอักษร: tools/name_readings.tsv (แก้ที่นั่นแล้วรันใหม่)
- กติกา: TRANSLITERATION.md, TRANSLITERATION_HOKKIEN.md, TRANSLITERATION_TEOCHEW.md
- สามคอลัมน์นี้ถอดเสียงทุกอักษรในคอลัมน์ “ชื่อจีน” ไม่แปลส่วนใดเป็นคำไทย
  (ต่างจากคอลัมน์ “ชื่อไทย” เดิมที่แปลคำเรียก เช่น 童子 = เด็กรับใช้)
- ท้ายสคริปต์ทดสอบกับตัวอย่างในตารางทั้งสาม ถ้าไม่ตรงจะพิมพ์ MISMATCH
"""
import io, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, 'fengshen-characters.md')
TSV = os.path.join(ROOT, 'tools', 'name_readings.tsv')

# ---------- คำอ่านรายตัวอักษร ----------
MD_R, HK, TC = {}, {}, {}
for line in open(TSV, encoding='utf-8'):
    if line.strip() and not line.startswith('#'):
        c, m, h, t = line.rstrip('\n').split('\t')[:4]
        MD_R[c], HK[c], TC[c] = m, h, t

# คำอ่านทั้งคำ (ขั้นที่ 1 ของหัวข้อแหล่งคำอ่าน) และเสียงเฉพาะของชื่อ
# จีนกลาง: อักษรหลายเสียงที่ชื่อนั้นใช้เสียงอื่นจากค่าใน TSV
MD_WORD = {
    '哪吒': ['ne2', 'zha1'],  # TRANSLITERATION.md
    '姬叔乾': ['ji1', 'shu1', 'gan1'],  # 乾 gān ตามคอลัมน์ชื่อไทยเดิม (จีซูกาน) ชื่ออื่นใช้ qián
}
HK_WORD = {
    '哪吒': ['lo5', 'tshia1'],  # Wiktionary 哪吒 tw: Lô-chhia
    '聖母': ['sing3', 'bo2'],   # Wiktionary 聖母 tw: sèng-bó
    '老子': ['noo2', 'tsu2'],   # Wiktionary 老子 tw: Nó͘-chú
    '姬叔乾': ['ki1', 'siok4', 'kan1'],  # 乾 gān literary kan (Wiktionary)
}
TC_WORD = {
    '哪吒': ['na5', 'za1'],     # Wiktionary 哪吒
    '聖母': ['sian3', 'bho2'],  # Wiktionary 聖母
    '老子': ['lao6', 'zê2'],    # Wiktionary 老子 (Wiktionary ze2 = ตารางโครงการ zê2)
    '姬叔乾': ['gi1', 'sog4', 'gang1'],  # 乾 gān = gang1 (Wiktionary)
}

# D035: เสียงแซ่ ใช้เมื่ออักษรเป็นแซ่ต้นชื่อเท่านั้น เฉพาะอักษรที่ Wiktionary (2026-11-09) ระบุว่าใช้เป็นแซ่
# (“incl. surname” / “surname”) ฮกเกี้ยนใช้แถว tw/tp ส่วนแต้จิ๋วใช้ซัวเถา (เขียนแบบตารางโครงการ)
HK_SURNAME = {'黃': 'ng5', '陳': 'tan5', '丘': 'khu1', '劉': 'lau5', '呂': 'lu7', '張': 'tiunn1',
              '彭': 'phinn5', '徐': 'tshi5', '戴': 'te3', '方': 'png1', '楊': 'iunn5', '歐': 'au1',
              '洪': 'ang5', '白': 'peh8', '胡': 'oo5', '董': 'tang2', '蔡': 'tshua3', '蔣': 'tsiunn2',
              '薛': 'sih4', '郭': 'kueh4', '鄭': 'tinn7', '錢': 'tsinn5', '麥': 'beh8'}
TC_SURNAME = {'陳': 'dang5', '丘': 'ku1', '孫': 'sêng1', '張': 'dion1', '戴': 'do3', '方': 'bung1',
              '洪': 'ang5', '王': 'heng5', '胡': 'ou5', '董': 'dang2', '費': 'bi3', '郭': 'guêh4',
              '馬': 'bhe2', '高': 'go1'}
# ชื่อที่อักษรแรกไม่ใช่แซ่ (ไม่ใช้ HK_SURNAME / TC_SURNAME)
NOT_SURNAME = {'黃龍真人', '石磯', '白鶴童子', '白雲童子', '白雲童兒', '三妖', '九頭雉雞精'}

# =====================================================================
# จีนกลาง (TRANSLITERATION.md)
# =====================================================================
MD_INIT = [('zh', 'จ', None), ('ch', 'ช', 'ฉ'), ('sh', 'ซ', 'ส'), ('b', 'ป', None), ('p', 'พ', 'ผ'),
           ('m', 'ม', 'หม'), ('f', 'ฟ', 'ฝ'), ('d', 'ต', None), ('t', 'ท', 'ถ'), ('n', 'น', 'หน'),
           ('l', 'ล', 'หล'), ('g', 'ก', None), ('k', 'ค', 'ข'), ('h', 'ฮ', 'ห'), ('j', 'จ', None),
           ('q', 'ช', 'ฉ'), ('x', 'ซ', 'ส'), ('r', 'ร', 'หร'), ('z', 'จ', None), ('c', 'ช', 'ฉ'),
           ('s', 'ซ', 'ส'), ('', 'อ', None)]
MD_RIME = {
    'a': 'CTา', 'o': 'CTอ', 'e': 'เCTอ', 'ai': 'ไCT', 'ei': 'เCTย', 'ao': 'เCTา', 'ou': 'โCTว',
    'an': 'CTาน', 'en': 'เCิTน', 'ang': 'CTาง', 'eng': 'เCิTง', 'ong': 'CTง',
    'i': 'CีT', 'ia': 'เCีTย', 'ie': 'เCีTย', 'iao': 'เCีTยว', 'iu': 'CิTว', 'ian': 'เCีTยน',
    'in': 'CิTน', 'iang': 'เCีTยง', 'ing': 'CิTง', 'iong': 'CฺยTง',
    'u': 'CูT', 'ua': 'CวTา', 'uo': 'CัTว', 'uai': 'ไCวT', 'ui': 'CุTย', 'uan': 'CTวน',
    'un': 'CุTน', 'uang': 'CTวง', 'v': 'CีTว์', 've': 'เCวีTย',
}
MD_RIME_JQX = {'u': 'CวีT', 'ue': 'เCวีTย', 'uan': 'เCวีTยน', 'un': 'CวิTน'}
MD_YW = {  # พยางค์ขึ้นต้นด้วย y / w: (แม่แบบ, พยัญชนะ)
    'yi': ('CีT', 'อ'), 'yin': ('CิTน', 'อ'), 'ying': ('CิTง', 'อ'), 'wu': ('CูT', 'อ'),
    'yu': ('CวีT', 'อ'), 'ya': ('CTา', 'y'), 'yan': ('เCีTยน', 'y'), 'yang': ('CTาง', 'y'),
    'ye': ('เCT', 'y'), 'yao': ('เCTา', 'y'), 'you': ('โCTว', 'y'), 'yong': ('CTง', 'y'),
    'yue': ('เCวT', 'y'), 'yuan': ('CTวน', 'y'), 'yun': ('CุTน', 'y'),
    'wa': ('CTา', 'w'), 'wo': ('CTอ', 'w'), 'wai': ('ไCT', 'w'), 'wei': ('เCTย', 'w'),
    'wan': ('CTาน', 'w'), 'wen': ('เCิTน', 'w'), 'wang': ('CัTง', 'w'), 'weng': ('เCิTง', 'w'),
}
MD_TONE_MID = {1: '', 2: '๋', 3: '่', 4: '้'}


def mandarin(rd):
    m = re.fullmatch(r'([a-zv]+)([1-5])', rd)
    assert m, rd
    body, tone = m.group(1), int(m.group(2))
    tone = 1 if tone == 5 else tone
    if body == 'er':
        tpl, low, high = 'เCTอร์', 'อ', None
    elif body in MD_YW:
        tpl, k = MD_YW[body]
        low, high = {'อ': ('อ', None), 'y': ('ย', 'หย'), 'w': ('ว', 'หว')}[k]
    else:
        for ini, low, high in MD_INIT:
            if body.startswith(ini):
                rime = body[len(ini):]
                break
        else:
            raise ValueError(rd)
        if ini in ('j', 'q', 'x') and rime in MD_RIME_JQX:
            tpl = MD_RIME_JQX[rime]
        elif ini in ('z', 'c', 's', 'zh', 'ch', 'sh', 'r') and rime == 'i':
            tpl = 'CืTอ'
        else:
            tpl = MD_RIME[rime]
    if high is None:
        c, mark = low, MD_TONE_MID[tone]
    else:
        c, mark = {1: (low, ''), 2: (high, ''), 3: (high, '่'), 4: (low, '่')}[tone]
    return tpl.replace('C', c).replace('T', mark)


def pinyin_to_num(p):
    """พินอินมีเครื่องหมายเสียง (Wiktionary) → เลขเสียง ü = v"""
    s = unicodedata.normalize('NFD', p.lower())
    tone = 5
    for k, v in {'̄': 1, '́': 2, '̌': 3, '̀': 4}.items():
        if k in s:
            tone = v
            s = s.replace(k, '')
    s = s.replace('ü', 'v')
    return f'{s}{tone}'


# =====================================================================
# ฮกเกี้ยน / แต้จิ๋ว
# =====================================================================
HK_INIT = [('tsh', 'ช', 'ฉ'), ('ts', 'จ', None), ('ph', 'พ', 'ผ'), ('th', 'ท', 'ถ'),
           ('kh', 'ค', 'ข'), ('ng', 'ง', 'หง'), ('p', 'ป', None), ('b', 'บ', None),
           ('m', 'ม', 'หม'), ('t', 'ต', None), ('n', 'น', 'หน'), ('l', 'ล', 'หล'),
           ('k', 'ก', None), ('g', 'ง', 'หง'), ('h', 'ฮ', 'ห'), ('s', 'ซ', 'ส'),
           ('j', 'ย', 'หย'), ('', 'อ', None)]
TC_INIT = [('bh', 'บ', None), ('gh', 'ง', 'หง'), ('ng', 'ง', 'หง'), ('b', 'ป', None),
           ('p', 'พ', 'ผ'), ('m', 'ม', 'หม'), ('d', 'ต', None), ('t', 'ท', 'ถ'),
           ('n', 'น', 'หน'), ('l', 'ล', 'หล'), ('g', 'ก', None), ('k', 'ค', 'ข'),
           ('h', 'ฮ', 'ห'), ('z', 'จ', None), ('c', 'ช', 'ฉ'), ('s', 'ซ', 'ส'),
           ('r', 'ย', 'หย'), ('', 'อ', None)]

# rime -> (แม่แบบ, ชนิด) ชนิด: L คำเป็น, S คำตายสระสั้น, D คำตายสระยาว; K = ช่องไม้ไต่คู้
COMMON = {
    'a': ('CTา', 'L'), 'e': ('แCT', 'L'), 'i': ('CีT', 'L'), 'o': ('โCT', 'L'), 'u': ('CูT', 'L'),
    'ai': ('ไCT', 'L'), 'ia': ('เCีTย', 'L'), 'iu': ('CิTว', 'L'), 'ua': ('CัTว', 'L'),
    'ui': ('CุTย', 'L'), 'uai': ('ไCTว', 'L'),
    'ah': ('CTะ', 'S'), 'ih': ('CิT', 'S'), 'uh': ('CุT', 'S'), 'eh': ('แCTะ', 'S'),
    'oh': ('โCTะ', 'S'), 'iah': ('เCีTยะ', 'S'), 'uah': ('CัTวะ', 'S'),
    'am': ('CTำ', 'L'), 'im': ('CิTม', 'L'), 'iam': ('เCีTยม', 'L'), 'ang': ('CัTง', 'L'),
    'iang': ('เCีTยง', 'L'), 'iong': ('CฺยTง', 'L'),
    'ng': ('CึTง', 'L'), 'm': ('CึTม', 'L'),
}
HK_RIME = dict(COMMON, **{
    'oo': ('CTอ', 'L'), 'au': ('เCTา', 'L'), 'io': ('เCีTย', 'L'), 'iau': ('เCีTยว', 'L'),
    'ue': ('CTวย', 'L'), 'ooh': ('เCTาะ', 'S'), 'ioh': ('เCีTยะ', 'S'),
    'an': ('CัTน', 'L'), 'in': ('CิTน', 'L'), 'un': ('CุTน', 'L'), 'ian': ('เCีTยน', 'L'),
    'uan': ('CTวน', 'L'), 'ing': ('เCTง', 'L'), 'ong': ('CTอง', 'L'),
    'ap': ('CัTบ', 'S'), 'ip': ('CิTบ', 'S'), 'iap': ('เCีTยบ', 'D'), 'at': ('CัTด', 'S'),
    'it': ('CิTด', 'S'), 'ut': ('CุTด', 'S'), 'iat': ('เCีTยด', 'D'), 'uat': ('CTวด', 'D'),
    'ak': ('CัTก', 'S'), 'ik': ('เCKก', 'S'), 'ok': ('CTก', 'S'), 'iak': ('เCีTยก', 'D'),
    'iok': ('CฺยTก', 'S'),
    # D039: ueh [ueʔ] = เ-วะ (ว ควบ) เช่น 郭 kueh เกวะ (แซ่)
    'ueh': ('เCวTะ', 'S'),
})
TC_RIME = dict(COMMON, **{
    'ê': ('CืTอ', 'L'), 'ao': ('เCTา', 'L'), 'ou': ('โCTว', 'L'), 'oi': ('โCTย', 'L'),
    # D038: ซัวเถาใช้ io; iê / iêng เป็นของสำเนียงแต้จิ๋ว (潮州) จึงไม่รับในตารางนี้
    'io': ('เCีTย', 'L'), 'ioh': ('เCีTยะ', 'S'), 'iao': ('เCีTยว', 'L'), 'uê': ('CTวย', 'L'), 'êh': ('CึT', 'S'),
    'eng': ('เCTง', 'L'), 'ing': ('CิTง', 'L'), 'ong': ('CTง', 'L'), 'uang': ('CTวง', 'L'),
    'ung': ('CุTง', 'L'),
    # D036: êng [ɯŋ] ซัวเถา เช่น 殷 銀 艮
    'êng': ('CืTง', 'L'),
    # D039: uêh [ueʔ] = เ-วะ (ว ควบ) เช่น 月 ghuêh8 เงวะ, 郭 guêh4 เกวะ (แซ่)
    'uêh': ('เCวTะ', 'S'),
    'ab': ('CัTบ', 'S'), 'ib': ('CิTบ', 'S'), 'iab': ('เCีTยบ', 'D'), 'ag': ('CัTก', 'S'),
    'eg': ('เCKก', 'S'), 'ig': ('CิTก', 'S'), 'og': ('CTก', 'S'), 'iag': ('เCีTยก', 'D'),
    'iog': ('CฺยTก', 'S'), 'ug': ('CุTก', 'S'), 'uag': ('CTวก', 'D'),
})
HK_TONE = {1: 'สามัญ', 2: 'โท', 3: 'เอก', 4: 'เอก', 5: 'จัตวา', 6: 'เอก', 7: 'เอก', 8: 'ตรี'}
TC_TONE = {1: 'สามัญ', 2: 'โท', 3: 'เอก', 4: 'เอก', 5: 'ตรี', 6: 'จัตวา', 7: 'เอก', 8: 'ตรี'}
MID_MARK = {'สามัญ': '', 'เอก': '่', 'โท': '้', 'ตรี': '๊', 'จัตวา': '๋'}


def hk_nasal(r):
    return r.replace('nn', '')


def tc_nasal(r):
    return re.sub(r'(?<!g)n(h?)$', r'\1', r)


DIALECT = {
    'hk': (HK_INIT, HK_RIME, HK_TONE, hk_nasal),
    'tc': (TC_INIT, TC_RIME, TC_TONE, tc_nasal),
}


def syllable(rd, dialect):
    inits, rimes, tones, nasal = DIALECT[dialect]
    m = re.fullmatch(r'([a-zê]+)(\d)', rd)
    assert m, rd
    body, tone = m.group(1), int(m.group(2))
    for ini, low, high in inits:
        if body.startswith(ini):
            rime = body[len(ini):]
            if rime == '' and ini in ('ng', 'm'):  # พยางค์ที่ไม่มีสระ
                low, high, rime = 'อ', None, ini
            elif rime == '':
                continue
            rime = nasal(rime)
            if rime in rimes:
                break
    else:
        raise ValueError(rd)
    tpl, kind = rimes[rime]
    target = tones[tone]
    mid = high is None
    if kind == 'L':
        if mid:
            c, mark = low, MID_MARK[target]
        else:
            c, mark = {'สามัญ': (low, ''), 'เอก': (high, '่'), 'โท': (low, '่'),
                       'ตรี': (low, '้'), 'จัตวา': (high, '')}[target]
    elif target == 'เอก':
        c, mark = (low if mid else high), ''
    elif target == 'ตรี':
        c, mark = (low, '๊') if mid else (low, '' if kind == 'S' else '้')
    else:
        raise ValueError(f'คำตายเสียง{target}: {rd}')
    return tpl.replace('C', c).replace('K', mark if mark else '็').replace('T', mark)


# =====================================================================
def readings(zh, lang):
    """รายการคำอ่านของทั้งชื่อ ตามลำดับ: คำอ่านทั้งคำ → เสียงแซ่ → คำอ่านรายตัว"""
    R, W, SN = {'md': (MD_R, MD_WORD, {}), 'hk': (HK, HK_WORD, HK_SURNAME),
                'tc': (TC, TC_WORD, TC_SURNAME)}[lang]
    if zh in W:
        return list(W[zh])
    out, i = [], 0
    while i < len(zh):
        for w, rds in W.items():
            if len(w) > 1 and zh.startswith(w, i):
                out += rds
                i += len(w)
                break
        else:
            c = zh[i]
            out.append(SN[c] if i == 0 and c in SN and zh not in NOT_SURNAME else R[c])
            i += 1
    return out


def render(zh, lang):
    rds = readings(zh, lang)
    return ''.join(mandarin(r) if lang == 'md' else syllable(r, lang) for r in rds)


HEADER = '| ชื่อไทย | ชื่อไทย (จีนกลาง) | ชื่อไทย (ฮกเกี้ยน) | ชื่อไทย (แต้จิ๋ว) | ชื่อจีน | บทแรก |'


def build():
    lines = open(MD, encoding='utf-8').read().split('\n')
    out = []
    for l in lines:
        if l.startswith('| ชื่อไทย |'):
            out.append(HEADER)
        elif l.startswith('| --- |'):
            out.append('| --- | --- | --- | --- | --- | --- |')
        elif l.startswith('| '):
            cells = [c.strip() for c in l.strip('|').split('|')]
            th, zh, ch = cells[0], cells[-2], cells[-1]  # รับได้ทุกจำนวนคอลัมน์
            out.append(f'| {th} | {render(zh, "md")} | {render(zh, "hk")} | {render(zh, "tc")} | {zh} | {ch} |')
        else:
            out.append(l)
    open(MD, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))


def selftest():
    bad = 0
    tests = {
        'md': [('tong1', 'ทง'), ('tong2', 'ถง'), ('tong3', 'ถ่ง'), ('tong4', 'ท่ง'), ('da2', 'ต๋า'),
               ('de2', 'เต๋อ'), ('bo2', 'ป๋อ'), ('wang2', 'หวัง'), ('rong2', 'หรง'), ('ping2', 'ผิง'),
               ('fu2', 'ฝู'), ('tian2', 'เถียน'), ('ji3', 'จี่'), ('bei3', 'เป่ย'), ('jiu3', 'จิ่ว'),
               ('hai3', 'ไห่'), ('nv3', 'หนี่ว์'), ('xiao3', 'เสี่ยว'), ('li3', 'หลี่'), ('zhong4', 'จ้ง'),
               ('zhou4', 'โจ้ว'), ('deng4', 'เติ้ง'), ('tai4', 'ไท่'), ('shang4', 'ซ่าง'), ('hu4', 'ฮู่'),
               ('lu4', 'ลู่'), ('zhen4', 'เจิ้น'), ('er4', 'เอ้อร์'), ('zi3', 'จื่อ'), ('si1', 'ซือ'),
               ('chi2', 'ฉือ'), ('jie2', 'เจี๋ย'), ('xiang4', 'เซี่ยง'), ('xiong2', 'สฺยง'), ('qiong2', 'ฉฺยง'), ('hua4', 'ฮว่า'),
               ('kuo4', 'คั่ว'), ('luo2', 'หลัว'), ('kuai4', 'ไคว่'), ('sui3', 'สุ่ย'), ('duan4', 'ต้วน'),
               ('lve4', 'เลวี่ย'), ('ju4', 'จวี้'), ('xuan1', 'เซวียน'), ('quan2', 'เฉวียน'), ('jun1', 'จวิน'),
               ('yi2', 'อี๋'), ('yin3', 'อิ่น'), ('ying4', 'อิ้ง'), ('wu2', 'อู๋'), ('yu2', 'อวี๋'), ('yu4', 'อวี้'),
               ('ya2', 'หยา'), ('yan2', 'เหยียน'), ('ye3', 'เหย่'), ('yao2', 'เหยา'), ('you2', 'โหยว'),
               ('yong3', 'หย่ง'), ('yue4', 'เยว่'), ('yuan2', 'หยวน'), ('yun3', 'หยุ่น'), ('wa2', 'หวา'),
               ('wo3', 'หว่อ'), ('wai2', 'ไหว'), ('wei2', 'เหวย'), ('wan2', 'หวาน'), ('wen2', 'เหวิน'),
               ('wang4', 'วั่ง'), ('weng2', 'เหวิง'), ('ne2', 'เหนอ'), ('zha1', 'จา')],
        'hk': [('kau2', 'เก้า'), ('ho2', 'โฮ่'), ('poo3', 'ป่อ'), ('pak4', 'ปัก'), ('hok4', 'หก'),
               ('tshit4', 'ฉิด'), ('bun5', 'บุ๋น'), ('ong5', 'อ๋อง'), ('liong5', 'หลฺยง'), ('giok8', 'งฺยก'), ('bing5', 'เบ๋ง'), ('tua7', 'ตั่ว'),
               ('ji7', 'หยี่'), ('tsap8', 'จั๊บ'), ('lak8', 'ลัก'), ('liap8', 'เลี้ยบ'), ('suann1', 'ซัว'),
               ('peh8', 'แป๊ะ'), ('kueh4', 'เกวะ'), ('tik4', 'เต็ก'), ('kian3', 'เกี่ยน'), ('hong5', 'หอง'), ('te3', 'แต่'),
               ('thau5', 'เถา'), ('sng1', 'ซึง')],
        'tc': [('gong1', 'กง'), ('san1', 'ซา'), ('gao2', 'เก้า'), ('bou3', 'โป่ว'), ('cig4', 'ฉิก'),
               ('dang5', 'ตั๊ง'), ('lim5', 'ลิ้ม'), ('na5', 'น้า'), ('zo6', 'โจ๋'), ('ngou6', 'โหงว'),
               ('ri7', 'หยี่'), ('zab8', 'จั๊บ'), ('lag8', 'ลัก'), ('hê5', 'ฮื้อ'), ('dio5', 'เตี๊ย'),
               ('ng5', 'อึ๊ง'), ('bhung5', 'บุ๊ง'), ('goi1', 'โกย'), ('heng1', 'เฮง'), ('suan1', 'ซัว'),
               ('tao5', 'เท้า'), ('beh8', 'แป๊ะ'),
               ('hêng1', 'ฮืง'), ('ngêng5', 'งื้ง'), ('gêng3', 'กื่ง'),  # D036
               ('guêh4', 'เกวะ'), ('ghuêh8', 'เงวะ')],                    # D039
    }
    for lang, cases in tests.items():
        for rd, exp in cases:
            got = mandarin(rd) if lang == 'md' else syllable(rd, lang)
            if got != exp:
                bad += 1
                print(f'{lang.upper()} MISMATCH {rd}: {got} ≠ {exp}')
    return bad


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if selftest() == 0:
        build()
        print('done')
