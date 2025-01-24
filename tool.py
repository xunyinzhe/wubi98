'''
根据词汇生成码表

# Test
python -m doctest -v .\tool.py

# Usage
# 生成简码表
python .\tool.py jian .\data\chars.txt .\wubi98_jm.dict.yaml
# 生成词语表
python .\tool.py conv .\ci\words.txt .\wubi98_ci.dict.yaml
# 添加词频信息
python .\tool.py conv .\ci\words.txt .\wubi98_ci.dict.yaml
'''
import os

import argparse
import datetime
import collections

import jieba

dict_head = '''# Rim Dictionary
# Encoding: utf-8
# Date: {}
---
name: {}
version: "0.1"
sort: by_weight
columns:
  - text
  - code
  - weight
  - stem
encoder:
  exclude_patterns:
    - '^z.*$'
  rules:
    - length_equal: 2
      formula: "AaAbBaBb"
    - length_equal: 3
      formula: "AaBaCaCb"
    - length_in_range: [4, 32]
      formula: "AaBaCaZa"
...
'''

def load_wubi_dict(filename):
    """ 载入全字单字码表
    """
    wubi_dict = {}
    with open(filename, 'r', encoding='utf-8') as infile:
        started = False
        for line in infile:
            if not started: # 略过...前面的几行
                started = line.strip() == '...'
            else:
                line = line.strip()
                if line: # 略过空行
                    char, code = line.split('\t')[:2]
                    wubi_dict[char] = code
    return wubi_dict


def load_characters(filename):
    """ 载入字表。

    字表文件就是一行一个字，把这些字都读取出来，放到一个列表中返回。
    """
    characters = []
    with open(filename, 'r', encoding='utf-8') as infile:
        for line in infile:
            character = line.strip()
            if character: # 略过空行
                characters.append(character)
    return characters


def get_wubi_code(wubi_dict, word):
    """ 生成词语的五笔编码。

    >>> wubi_dict = load_wubi_dict('wubi98.dict.yaml')
    >>> get_wubi_code(wubi_dict, '工')
    'aaaa'
    >>> get_wubi_code(wubi_dict, '机器')
    'swkk'
    >>> get_wubi_code(wubi_dict, '计算机')
    'ytsw'
    >>> get_wubi_code(wubi_dict, '光明日报')
    'ijjr'
    >>> get_wubi_code(wubi_dict, '电子计算机')
    'jbys'
    >>> get_wubi_code(wubi_dict, '中华人民共和国')
    'kwwl'
    """
    # 确保所有的字都在dict中
    for c in word:
        wubi_dict[c]

    if len(word) == 1:
        return wubi_dict[word]
    elif len(word) == 2:
        # 取第一字首二码、第二字首二码
        code1 = wubi_dict[word[0]]
        code2 = wubi_dict[word[1]]
        return code1[:2] + code2[:2]
    elif len(word) == 3:
        # 取第一字首码、第二字首码、第三字首二码
        code1 = wubi_dict[word[0]]
        code2 = wubi_dict[word[1]]
        code3 = wubi_dict[word[2]]
        return code1[0] + code2[0] + code3[:2]
    else:
        code1 = wubi_dict[word[0]]
        code2 = wubi_dict[word[1]]
        code3 = wubi_dict[word[2]]
        codeL = wubi_dict[word[-1]]
        return code1[0] + code2[0] + code3[0] + codeL[0]


def freq(infile_name, outfile_name, weight):
    """ 生成词频信息
    """
    with open(infile_name, 'r', encoding='utf-8') as infile:
        in_lines = [line.rstrip() for line in infile.readlines()]

    with open(outfile_name, 'w', encoding='utf-8') as outfile:

        separator = '...'
        if separator in in_lines:
            head = in_lines[:in_lines.index(separator)+1]
            body = in_lines[in_lines.index(separator)+1:]
            for line in head:
                outfile.write(f'{line}\n')
        else:
            body = in_lines

        for line in body:
            items = line.strip().split('\t', 2)
            if len(items) == 1:
                word = items[0]
                freq = jieba.suggest_freq(word)
                if freq >= weight:
                    outfile.write(f'{word}\t{freq}\n')
            elif len(items) == 2:
                word, code = items
                freq = jieba.suggest_freq(word)
                if freq >= weight:
                    outfile.write(f'{word}\t{code}\t{freq}\n')
            else:
                word, code, other = items
                freq = jieba.suggest_freq(word)
                if freq >= weight:
                    other = other.split('\t', 1)[1]
                    outfile.write(f'{word}\t{code}\t{freq}\t{other}\n')


def conv(infile_name, outfile_name, dictionary):
    """ 为词添加编码
    """
    wubi_dict = load_wubi_dict(dictionary)

    with open(infile_name, 'r', encoding='utf-8') as infile, \
        open(outfile_name, 'w', encoding='utf-8') as outfile:

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        outfile.write(dict_head.format(now, 'wubi98_ci'))

        for line in infile:
            word = line.strip()
            # 忽略单字
            if len(word) > 1:
                try:
                    code = get_wubi_code(wubi_dict, word)
                    outfile.write(f'{word}\t{code}\n')
                except:
                    print(word, '无编码')


def jian(infile_name, outfile_name, dictionary):
    """ 根据单字全码生成简码。

    一级简码就是只有一个字母的码，按一个键就能出现，二级两个字母，三级三个字母，三级简码的意义就已经不大了，四级就全码。
    一级字表，二级字表，三级字表，这些是《按照通用规范汉字表》的对汉字进行的分类，最常用的是一级。

    一级简码很直接，固定的25个字母。
    二级简码是常用字中的609个字，二级简码按键25*25=625个，但有些按键组合没有对应的字，就用不到。
    三级简码按照结巴分词的词频来确定，词频高的优先占用，另外全码就是三码的字优先占用。
    """
    # 一级简码
    simple_codes_01 = collections.OrderedDict([
        ("我", 'q'),
        ("人", 'w'),
        ("有", 'e'),
        ("的", 'r'),
        ("和", 't'),
        ("主", 'y'),
        ("产", 'u'),
        ("不", 'i'),
        ("为", 'o'),
        ("这", 'p'),
        ("工", 'a'),
        ("要", 's'),
        ("在", 'd'),
        ("地", 'f'),
        ("一", 'g'),
        ("上", 'h'),
        ("是", 'j'),
        ("中", 'k'),
        ("国", 'l'),
        ("经", 'x'),
        ("以", 'c'),
        ("发", 'v'),
        ("了", 'b'),
        ("民", 'n'),
        ("同", 'm'),
    ])


    # 二级简码
    NULL = '〇'
    SIMPLE_CODES_02_INDEXES = 'gfdsahjklmtrewqyuiopnbvcx'
    SIMPLE_CODES_02_CHART = [
        # g f d s a   h j k l m   t r e w q   y u i o p   n b v c x
        ('五于天末开' '下理事画现' '麦珀表珍万' '玉来求亚琛' '与击妻到互'), # g
        ('十寺城某域' '直刊吉雷南' '才垢协零无' '坊增示赤过' '志坡雪支坶'), # f
        ('三夺大厅左' '还百右面而' '故原历其克' '太辜砂矿达' '成破肆友龙'), # d
        ('本票顶林模' '相查可柬贾' '枚析杉机构' '术样档杰枕' '札李根权楷'), # s
        ('七革苦莆式' '牙划或苗贡' '攻区功共匹' '芳蒋东蘑芝' '艺节切芭药'), # a 

        ('睛睦非盯瞒' '步旧占卤贞' '睡睥肯具餐' '虔瞳叔虚瞎' '虑〇眼眸此'), # h
        ('量时晨果晓' '早昌蝇曙遇' '鉴蚯明蛤晚' '影暗晃显蛇' '电最归坚昆'), # j
        ('号叶顺呆呀' '足虽吕喂员' '吃听另只兄' '唁咬吵嘛喧' '叫啊啸吧哟'), # k
        ('车团因困轼' '四辊回田轴' '略斩男界罗' '罚较〇辘连' '思囝轨轻累'), # l
        ('赋财央崧曲' '由则迥崭册' '败冈骨内见' '丹赠峭〇迪' '岂邮〇峻幽'), # m

        ('年等知条长' '处得和备身' '秩稀务答稳' '入冬秒秋乏' '乐秀委么每'), # t
        ('后质拓打找' '看提扣押抽' '手折拥兵换' '搞拉泉扩近' '所报扫反指'), # r
        ('且肚须采肛' '毡胆加舆觅' '用貌朋办胸' '肪胶膛脏边' '力服妥肥脂'), # e
        ('全什估休代' '个介保佃仙' '八风佣从你' '信们偿伙伫' '亿他分公化'), # w
        ('钱针然钉氏' '外旬名甸负' '儿勿角欠多' '久匀尔炙锭' '包迎争色〇'), # q

        ('证计诚订试' '让刘识亩市' '放义衣认询' '方详就亦亮' '记享良充率'), # y
        ('半斗头亲并' '着间问闸端' '道交前闪次' '六立冰普〇' '闷疗妆痛北'), # u
        ('光汗尖浦江' '小浊溃泗油' '少汽肖没沟' '济洋水渡党' '沁波当汉涨'), # i
        ('精庄类床席' '业烛燥库灿' '庭粕粗府底' '广粒应炎迷' '断籽数序鹿'), # o
        ('家守害宁赛' '寂审宫军宙' '客宾农空宛' '社实宵灾之' '官字安〇它'), # p

        ('那导居懒异' '收慢避惭届' '改怕尾恰懈' '心习尿屡忱' '已敢恨怪尼'), # n
        ('卫际承阿陈' '耻阳职阵出' '降孤阴队陶' '及联孙耿辽' '也子限取陛'), # b
        ('建寻姑杂既' '肃旭如姻妯' '九婢姐妗婚' '妨嫌录灵退' '恳好妇妈姆'), # v
        ('马对参牺戏' '〇〇台〇观' '矣〇能难物' '叉〇〇〇〇' '予邓艰双〇'), # c
        ('线结顷缚红' '引旨强细贯' '乡绵组给约' '纺弱纱继综' '纪级绍弘比'), # x
    ]
    SIMPLE_CODES_02_STR = ''.join(SIMPLE_CODES_02_CHART)

    def simple_codes_02(code):
        row = SIMPLE_CODES_02_INDEXES.index(code[0])
        col = SIMPLE_CODES_02_INDEXES.index(code[1])
        return SIMPLE_CODES_02_CHART[row][col]


    # 三级简码
    wubi_dict = load_wubi_dict(dictionary)
    # 载入字表，取前3500个字，也就是《通用汉字规范》中的一级字表
    characters = load_characters(infile_name)[:3501]
    
    # 获取字的频率
    freqs = {}
    for character in characters:
        freqs[character] = jieba.suggest_freq(character)
    # 再按字频排序
    characters_sorted = sorted(list(characters), key=lambda x: freqs[x], reverse=True)

    simple_codes_03 = {}
    for character in characters_sorted:
        # 跳过一级简码
        if character in simple_codes_01:
            continue
        # 跳过二级简码
        if character in SIMPLE_CODES_02_STR:
            continue

        code = wubi_dict.get(character, '')
        # 无编码
        if not code:
            print(f"No Code: {character}")
            continue

        code3 = code[:3]
        # 全码即三码优先
        if code3 not in simple_codes_03 or code3 == code:
            simple_codes_03[code3] = character

    with open(outfile_name, 'w', encoding='utf-8') as f:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(dict_head.format(now, 'wubi98_jm'))
        # 一级简码
        for character in simple_codes_01:
            code = simple_codes_01[character]
            weight = jieba.suggest_freq(character)
            full_code = wubi_dict[character]
            f.write(f"{character}\t{code}\t{weight}\t{full_code}\n")
        # 二级简码
        for c1 in SIMPLE_CODES_02_INDEXES:
            for c2 in SIMPLE_CODES_02_INDEXES:
                code = c1 + c2
                character = simple_codes_02(code)
                weight = jieba.suggest_freq(character)
                if character != NULL:
                    full_code = wubi_dict[character]
                    f.write(f"{character}\t{code}\t{weight}\t{full_code}\n")
        # 三级简码
        for code in simple_codes_03:
            character = simple_codes_03[code]
            weight = jieba.suggest_freq(character)
            full_code = wubi_dict[character]
            f.write(f"{character}\t{code}\t{weight}\t{full_code}\n")


    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="tool.py",
        description='''根据词汇生成Rime字典'''
    )
    parser.add_argument(
        "command",
        choices=['conv', 'freq', 'jian'],
        help=(
            'conv: 根据词汇生成Rime格式的字典; '
            'freq: 为现有的Rime字典添加Weight; '
            'jian: 生成单字的简码'
        )
    )
    
    parser.add_argument(
        "-d", "--dictionary",
        default="wubi98.dict.yaml",
        help=(
            '五笔98单字码表，基础码表，根据它来制成其它词语的编码，也是Rime字典，GB18030-27533'
        )
    )

    parser.add_argument(
        "-w", "--weight",
        type=int,
        default=0,
        help=(
            '最小的weight值，如果小于它，词汇不会被收录，weight也就是字词频率'
        ),
    )

    parser.add_argument(
        "infile",
        type=str,
        help=(
            '输入文件名'
        )
    )

    parser.add_argument(
        "outfile",
        type=str,
        help=(
            '输出文件名'
        )
    )

    args = parser.parse_args()

    # 直接修改文件
    if args.infile == args.outfile:
        os.rename(args.infile, args.infile+'.backup')
        args.infile = args.infile+'.backup'

    if args.command == 'freq':
        freq(args.infile, args.outfile, args.weight)
    elif args.command == 'conv':
        conv(args.infile, args.outfile, args.dictionary)
    elif args.command == 'jian':
        jian(args.infile, args.outfile, args.dictionary)
