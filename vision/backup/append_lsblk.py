from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from pathlib import Path

path = Path('D:/racecar/output/树莓派最小镜像备份与新SD卡恢复操作指南.docx')
img = Path(r'C:\Users\ASUS\AppData\Local\Temp\QQ_1794756571592.png')
doc = Document(path)

def font(run, size=10.5, bold=False, color=(0,0,0), name='Microsoft YaHei'):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor(*color)

def para(text='', size=10.5, bold=False, after=6, align=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    font(r, size=size, bold=bold)
    return p

def heading(text, level=1):
    p = doc.add_paragraph(style=f'Heading {level}')
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text)
    font(r, size=14 if level == 1 else 11.5, bold=True)
    return p

def code(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.right_indent = Inches(0.18)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.1
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), 'F3F5F7')
    pPr.append(shd)
    r = p.add_run(text)
    font(r, size=9.5, name='Consolas')
    return p

def cell_border(cell, color='D9D9D9', sz='6'):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.first_child_found_in('w:tcBorders')
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tcPr.append(borders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e = borders.find(qn('w:'+edge))
        if e is None:
            e = OxmlElement('w:'+edge)
            borders.append(e)
        e.set(qn('w:val'),'single'); e.set(qn('w:sz'),sz); e.set(qn('w:space'),'0'); e.set(qn('w:color'),color)

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

# Add appendix with actual screenshot interpretation
heading('附录 这张 lsblk 输出如何识别设备', 1)
para('截图显示，系统当前同时看到了外置存储设备 /dev/sda 和正在运行系统的树莓派 SD 卡 /dev/mmcblk0。备份时应把镜像保存到 /media/xiaoche/9802-BA23 目录下的外置设备。恢复时如果把新卡接到 Linux 电脑或读卡器上，设备名可能变成 /dev/sda 或 /dev/sdb，必须重新执行 lsblk 确认。')
if img.exists():
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(img), width=Inches(5.8))
    cp = doc.add_paragraph('图 2  备份前的设备与挂载点示例'); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; cp.paragraph_format.space_after = Pt(6)
    for r in cp.runs: font(r, size=9, color=(89,89,89))

t = doc.add_table(rows=1, cols=3)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
headers = ['设备或路径', '截图中的含义', '操作建议']
widths = [1.55, 2.55, 2.45]
for i,h in enumerate(headers):
    c=t.rows[0].cells[i]; c.width=Inches(widths[i]); shade(c,'44546A'); cell_border(c)
    p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(h); font(r,size=9.5,bold=True,color=(255,255,255))
rows=[
    ('/dev/sda1', '29.1G exfat，挂载在 /media/xiaoche/9802-BA23', '外置 SD 卡分区。可把备份镜像写到这个目录。'),
    ('/dev/mmcblk0p1', '512M vfat，挂载在 /boot/firmware', '系统 SD 卡的 boot 分区。不要把它当作外置目标盘。'),
    ('/dev/mmcblk0p2', '28.6G ext4，挂载为 /', '系统 SD 卡的根分区，脚本会从这里复制系统文件。'),
    ('/dev/ram0', '1.8G swap，挂载为 [SWAP]', '交换设备，不参与备份文件保存。'),
]
for ri,row in enumerate(rows):
    cells=t.add_row().cells
    for i,val in enumerate(row):
        c=cells[i]; c.width=Inches(widths[i]); shade(c,'F7F9FB' if ri%2 else 'FFFFFF'); cell_border(c)
        c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.15
        r=p.add_run(val); font(r,size=9.2)
doc.add_paragraph().paragraph_format.space_after=Pt(2)
para('根据截图，可以直接使用下面的备份命令。命令中的目录与截图一致，实际使用时以 df -h 和 lsblk 显示的挂载点为准。', after=5)
code('sudo ./back.sh /media/xiaoche/9802-BA23/backup.img')
para('如果外置设备没有出现在 /media 下，先挂载它，再执行备份。恢复命令中的 /dev/sdX 代表整张目标 SD 卡，不能填成 /dev/sdX1 这样的分区设备。', after=6)

path = Path('D:/racecar/output/树莓派最小镜像备份与新SD卡恢复操作指南_含设备截图.docx')
doc.save(path)




