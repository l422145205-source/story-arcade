#!/usr/bin/env python3
"""Original story artwork + data cards from actual fictional CLI views. Pillow is contributor-only."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BG='#111B32'; PANEL='#1B2945'; LINE='#3A4A65'; INK='#F4F0E7'
MUTED='#B2BDD1'; GOLD='#F6C260'; MINT='#87D1BC'; PURPLE='#B4A4F0'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--font',type=Path,required=True); p.add_argument('--bold-font',type=Path)
    args=p.parse_args()
    def font(n,bold=False):return ImageFont.truetype(str(args.bold_font if bold and args.bold_font else args.font),n)
    def canvas(h):
        im=Image.new('RGB',(1500,h),BG); return im,ImageDraw.Draw(im)
    def text(d,x,y,value,n=27,fill=INK,bold=False):d.text((x,y),str(value),font=font(n,bold),fill=fill)
    def wrap(d,x,y,value,width,n=27,fill=INK,gap=12):
        line=''
        for char in value:
            if char=='\n' or d.textlength(line+char,font=font(n))>width:
                text(d,x,y,line,n,fill); y+=n+gap; line='' if char=='\n' else char
            else:line+=char
        if line:text(d,x,y,line,n,fill); y+=n+gap
        return y
    def box(d,xy,fill=PANEL):d.rounded_rectangle(xy,radius=24,fill=fill,outline=LINE,width=2)
    def pill(d,x,y,label,fill=GOLD):
        w=int(d.textlength(label,font=font(21)))+34
        d.rounded_rectangle((x,y,x+w,y+40),radius=20,fill=fill)
        text(d,x+17,y+4,label,21,BG)
        return x+w+14
    def person(d,x,y,s=1,color=BG):
        d.ellipse((x-12*s,y-36*s,x+12*s,y-12*s),fill=color)
        d.rounded_rectangle((x-19*s,y-8*s,x+19*s,y+39*s),radius=int(10*s),fill=color)
    def train(d,x,y,width=720,height=210):
        d.rounded_rectangle((x,y,x+width,y+height),radius=34,fill='#CBD6D6')
        d.rectangle((x+4,y+height-53,x+width-4,y+height-34),fill=GOLD)
        win=(width-60)/7
        for i in range(7):
            xx=x+24+i*win
            d.rounded_rectangle((xx,y+29,xx+win-13,y+height-65),radius=11,fill='#314362')
            if i<6:person(d,xx+(win-13)/2,y+91,0.85,'#18243B')
            else:text(d,xx+19,y+53,'?',50,GOLD,True)
        for xx in (x+100,x+width-100):
            d.ellipse((xx-21,y+height-5,xx+21,y+height+37),fill='#060D1B',outline=LINE,width=3)
    opening=json.loads((ROOT/'examples/demo/opening.json').read_text(encoding='utf-8'))
    volunteer=json.loads((ROOT/'examples/demo/volunteer-opening.json').read_text(encoding='utf-8'))
    checkpoint=json.loads((ROOT/'examples/demo/checkpoint.json').read_text(encoding='utf-8'))
    frames_data=json.loads((ROOT/'examples/demo/frames.json').read_text(encoding='utf-8'))['frames']
    checks=json.loads((ROOT/'examples/demo/verification.json').read_text(encoding='utf-8'))
    world=json.loads((ROOT/'assets/last-train.json').read_text(encoding='utf-8'))
    media=ROOT/'media'; media.mkdir(exist_ok=True)

    im,d=canvas(820)
    # Sparse station-grid and route line, original geometric artwork.
    for x in range(60,1490,95):d.line((x,165,x,752),fill='#18263F',width=1)
    text(d,60,43,'StoryArcade',77,bold=True)
    pill(d,1145,78,'AGENT SKILL',MINT)
    text(d,63,194,'别只读结局。',62,bold=True)
    text(d,63,281,'进去，做个选择。',62,bold=True)
    wrap(d,66,393,'让 Agent 主持一场推理。\n线索、后果、存档，接着你的选择走。',725,29,fill=MUTED)
    d.ellipse((1068,202,1308,442),fill='#273450',outline='#425271',width=3)
    text(d,1109,231,'23:17',44,GOLD,True)
    train(d,759,375,665,190)
    d.line((752,614,1432,614),fill=MINT,width=5)
    for x in (792,1083,1391):d.ellipse((x-9,605,x+9,623),fill=BG,outline=MINT,width=3)
    text(d,779,638,'7 人统计',24,MUTED); text(d,1092,638,'6 个身影',24,MUTED)
    x=66
    for label in ['原创短案','不同视角','本地续玩']:x=pill(d,x,562,label)
    text(d,65,729,'PLAY  /  SAVE  /  WHAT IF',26,GOLD,True)
    text(d,950,734,'原创虚构场景 · 在 Agent 里开局',22,MUTED)
    im.save(media/'storyarcade-cover.png',optimize=True)

    im,d=canvas(820)
    text(d,60,35,'你的第一局：末班地铁，第七位乘客',44,bold=True)
    text(d,64,108,'只有开局，没有答案。下一步由你决定。',26,MUTED)
    for i in range(3):box(d,(60+i*475,184,505+i*475,692))
    pill(d,86,210,'01 · 看见数字')
    d.rounded_rectangle((123,294,443,495),radius=20,fill='#081322',outline=LINE,width=3)
    text(d,150,312,'本车人数',25,MUTED)
    text(d,258,335,'7',115,GOLD,True)
    wrap(d,88,557,'23:17。客流屏的数字，\n和你数到的身影对不上。',365,27)
    pill(d,560,210,'02 · 听见同一句话',PURPLE)
    for i in range(6):person(d,600+i*57,376,0.95,INK)
    d.rounded_rectangle((571,452,940,525),radius=19,fill='#2F3E5A')
    text(d,589,469,'“别把这句话带出车厢。”',24)
    wrap(d,563,557,'广播又重复了一遍。\n你还不知道它的语境。',365,27)
    pill(d,1035,210,'03 · 先做哪件事？',MINT)
    choices=[('查看屏幕小字','read-screen'),('比对两轮广播','compare-audio'),('询问列车员','ask-attendant')]
    allowed={a['id']:a for a in opening['choices']}
    for i,(label,id_) in enumerate(choices):
        yy=309+i*85
        d.rounded_rectangle((1036,yy,1421,yy+64),radius=15,fill='#30425A')
        text(d,1058,yy+15,label,27)
        text(d,1329,yy+17,f'{allowed[id_]["cost"]} 格',23,GOLD)
    wrap(d,1038,589,'直接说你的行动，\nAgent 会匹配可用选择。',350,25,fill=MUTED)
    text(d,64,742,'图中为原创剧本开场与实际可用行动；不是真实事件或 Agent 录屏。',23,MUTED)
    im.save(media/'first-scene.png',optimize=True)

    im,d=canvas(760)
    text(d,60,33,'同一节车厢，每个人拿到的资料不同',44,bold=True)
    text(d,64,106,'当前视角按需加载；作者答案留在完整剧本里。',26,MUTED)
    npc=world['npcs'][0]
    panels=[('夜归乘客',len(opening['known_facts']),GOLD,'从可见现象开始调查'),
            ('录音志愿者',len(volunteer['known_facts']),MINT,'开局多一条声音判断'),
            ('列车员',len(npc['initial_facts']),PURPLE,'角色资料单独提供给主持')]
    for i,(name,count,color,caption) in enumerate(panels):
        x=60+i*475;box(d,(x,186,x+445,625))
        d.rounded_rectangle((x+34,228,x+188,263),radius=11,fill=color)
        d.rounded_rectangle((x+34,249,x+408,444),radius=15,fill='#2A3B56',outline=color,width=3)
        for page in range(count):
            xx=x+80+page*77
            d.rounded_rectangle((xx,293,xx+54,384),radius=6,fill=INK)
            d.line((xx+12,315,xx+43,315),fill=LINE,width=3)
            d.line((xx+12,334,xx+38,334),fill=LINE,width=3)
        text(d,x+37,483,name,33,bold=True)
        text(d,x+37,535,f'{count} 条初始资料',26,color,True)
        text(d,x+37,580,caption,22,MUTED)
    text(d,65,668,'区别在资料视图与可执行规则；语言表达仍由宿主 Agent 负责。',25,MUTED)
    text(d,65,710,'视图分层不是加密或读源码防护，不承诺模型绝不剧透。',21,MUTED)
    im.save(media/'perspective-cards.png',optimize=True)

    im,d=canvas(740)
    text(d,60,36,'先保存，再问一句：如果我当时……',47,bold=True)
    text(d,64,115,'接力和分支使用真实工具产物；这个图不展示结局答案。',25,MUTED)
    box(d,(60,224,490,562))
    text(d,95,265,'两次选择后的节点',31,bold=True)
    text(d,95,328,f'{checkpoint["revision"]} 次选择 / {checkpoint["remaining"]} 格剩余',29,GOLD,True)
    text(d,95,383,f'{len(checkpoint["known_facts"])} 条已知线索',29)
    text(d,95,454,'可以就此导出接力包',24,MUTED)
    d.line((492,390,638,390,638,303,747,303),fill=MINT,width=5)
    d.line((638,390,638,510,747,510),fill=PURPLE,width=5)
    box(d,(749,214,1440,385));text(d,785,245,'路线 A · 继续原存档',33,MINT,True)
    wrap(d,785,306,'私下核实，按当前证据继续。',600,27)
    box(d,(749,429,1440,600));text(d,785,460,'路线 B · 从该节点分支',33,PURPLE,True)
    wrap(d,785,521,'试另一个决定，保留不同的后果。',600,27)
    text(d,65,651,'实际复现：原路线保留、两条路线结局不同、接力恢复的线索一致。',24,MUTED)
    text(d,65,698,'这是脚本化工具检查，不是玩家体验或模型性能评测。',21,MUTED)
    im.save(media/'branch-relay.png',optimize=True)

    frames=[]
    for index,r in enumerate(frames_data[:3]+[checkpoint]):
        im,d=canvas(810)
        text(d,60,34,'StoryArcade / 选择会留下记录',43,bold=True)
        label=['开局','第一次选择','第二次选择','暂停、重试与接力'][index]
        pill(d,1110,55,label,MINT)
        box(d,(60,146,1440,361))
        text(d,91,170,r['role']['label'],25,MUTED)
        wrap(d,93,224,r['last_outcome'],1295,30,gap=14)
        box(d,(60,400,480,684));text(d,96,429,'当前状态',29,bold=True)
        text(d,96,493,f'{r["revision"]} 次选择',37,GOLD,True)
        text(d,96,556,f'{r["remaining"]} / {r["initial_budget"]} 格剩余',31)
        text(d,96,615,f'{len(r["known_facts"])} 条已知线索',28,MUTED)
        box(d,(514,400,1440,684))
        if index<3:
            text(d,548,429,'下一步依然由你选',30,bold=True)
            for i,a in enumerate(r['choices'][:3]):
                wrap(d,552,493+i*53,a['label'],830,25,fill=INK)
        else:
            text(d,548,429,'工具复现结果',30,bold=True)
            wrap(d,552,493,'同一事件重试：未再次扣时间，文件未变化。\n接力包恢复：相同进度与已知线索。\n原存档保留，可从这里另开分支。',830,25)
        text(d,62,745,'原创虚构 / 实际脚本化工具输出的流程演示，并非 Agent 操作录屏。',23,MUTED)
        frames.append(im)
    frames[0].save(media/'play-save.gif',save_all=True,append_images=frames[1:],duration=[2500,2000,2300,3300],loop=0,optimize=False)
    print(json.dumps({'media':[p.name for p in media.iterdir()], 'fictional':True, 'agent_recording':False}))


if __name__=='__main__':main()
