from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_LINE_SPACING
from docx.enum.section import WD_ORIENT
from pathlib import Path

out_dir = Path(r'D:\racecar\output')
out_dir.mkdir(exist_ok=True)
out_path = out_dir / '树莓派最小镜像备份与新SD卡恢复操作指南.docx'
img_path = Path(r'C:\Users\ASUS\AppData\Local\Temp\QQ_1794742822191.png')

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.55)
sec.bottom_margin = Inches(0.55)
sec.left_margin = Inches(0.78)
sec.right_margin = Inches(0.78)

# helpers

def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

def set_cell_border(cell, color='D9D9D9', sz='6'):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders = tcPr.first_child_found_in('w:tcBorders')
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tcPr.append(borders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        tag = 'w:' + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn('w:val'), 'single')
        element.set(qn('w:sz'), sz)
        element.set(qn('w:space'), '0')
        element.set(qn('w:color'), color)

def set_cell_margins(cell, top=100, start=130, bottom=100, end=130):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node = tcMar.find(qn('w:' + m))
        if node is None:
            node = OxmlElement('w:' + m)
            tcMar.append(node)
        node.set(qn('w:w'), str(v))
        node.set(qn('w:type'), 'dxa')

def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)

def set_run_font(run, name='Microsoft YaHei', size=None, bold=None, color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)

def style_para(p, space_after=6, line=1.25):
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    return p

def add_body(text='', bold_lead=None):
    p = doc.add_paragraph()
    style_para(p, 6, 1.28)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        set_run_font(r, size=10.5, bold=True)
        r2 = p.add_run(text[len(bold_lead):])
        set_run_font(r2, size=10.5)
    else:
        r = p.add_run(text)
        set_run_font(r, size=10.5)
    return p

def add_bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    style_para(p, 3, 1.2)
    r = p.add_run(text)
    set_run_font(r, size=10.2)
    return p

def add_number(text):
    p = doc.add_paragraph(style='List Number')
    style_para(p, 3, 1.2)
    r = p.add_run(text)
    set_run_font(r, size=10.2)
    return p

def add_code(text):
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
    set_run_font(r, name='Consolas', size=9.5)
    return p

def add_heading(text, level=1):
    p = doc.add_paragraph(style=f'Heading {level}')
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text)
    set_run_font(r, size=14 if level == 1 else 11.5, bold=True, color=(0,0,0))
    return p

def add_table(headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        if widths:
            cell.width = Inches(widths[i])
        set_cell_shading(cell, '44546A')
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        set_run_font(r, size=9.5, bold=True, color=(255,255,255))
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cell = cells[i]
            if widths:
                cell.width = Inches(widths[i])
            set_cell_shading(cell, 'F7F9FB' if ridx % 2 else 'FFFFFF')
            set_cell_border(cell)
            set_cell_margins(cell, top=90, bottom=90)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(str(val))
            set_run_font(r, size=9.4)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table

# styles
styles = doc.styles
normal = styles['Normal']
normal.font.name = 'Microsoft YaHei'
normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
normal.font.size = Pt(10.5)
for name in ['Heading 1','Heading 2','Title']:
    st = styles[name]
    st.font.name = 'Microsoft YaHei'
    st._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    st.font.color.rgb = RGBColor(0,0,0)
# title
p = doc.add_paragraph(style='Title')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run('树莓派最小镜像备份与新 SD 卡恢复操作指南')
set_run_font(r, size=21, bold=True, color=(0,0,0))
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(14)
r = sub.add_run('适用于图片中 nanhantianyi/rpi-backup 脚本的操作说明')
set_run_font(r, size=10.5, color=(89,89,89))

add_body('这份指南说明如何使用 rpi-backup 脚本把正在运行的树莓派系统制作成可启动的最小镜像，如何把镜像保存到新的 SD 卡或外置存储设备，以及如何在目标 SD 卡上恢复并扩容。图片中的命令是操作提示，下面的步骤补充了挂载路径、设备识别、恢复和首次启动后的处理。')

add_heading('先理解这种备份方法', 1)
add_body('脚本会读取当前系统的 boot 分区和根分区，先按“boot 分区全部空间加根分区已用空间，再乘以 1.2”估算镜像大小，然后在镜像文件中创建 FAT32 boot 分区和 ext4 根分区，再用文件级复制方式写入系统内容。它会排除 /dev、/proc、/sys、/run、/tmp、/media、/mnt 等运行时目录，也会排除交换文件。')
add_body('这种方式的重点是“最小镜像”，镜像逻辑容量通常小于原 SD 卡的完整容量，便于迁移到容量相近或更大的卡。脚本本身没有调用 gzip、xz 等压缩程序，所以生成的 .img 文件不是传统意义上的压缩包。需要进一步压缩时，可以在备份完成后把 .img 压缩为 .img.gz。')

add_heading('图片中的提示对应什么', 1)
if img_path.exists():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(str(img_path), width=Inches(6.35))
    cap = doc.add_paragraph('图 1  原始操作提示')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(6)
    for rr in cap.runs:
        set_run_font(rr, size=9, color=(89,89,89))
add_body('图片中的第一、第二、第三行给出了空间判断逻辑。先确认系统卡剩余空间能否容纳备份文件，空间足够时可直接保存到系统卡，空间不足时要把外置 SD 卡挂载后保存到外置设备。图片中的命令是：')
add_code('git clone https://github.com/nanhantianyi/rpi-backup.git && cd rpi-backup\nsudo ./back.sh 备份镜像名.img')
add_body('如果脚本没有执行权限，可以改用 sudo bash back.sh 备份镜像名.img。外置设备应挂载到 /media 下，项目说明特别要求不要挂载到 /mnt，因为脚本会把临时镜像分区挂载到 /mnt。')

add_heading('备份前准备', 1)
add_table(['项目', '要求'], [
    ('系统权限', '在树莓派上使用 root 权限运行，命令前加 sudo。'),
    ('网络', '脚本会用 apt 安装 dosfstools、parted、kpartx、rsync，首次运行需要网络。'),
    ('外置存储', '如果系统卡剩余空间不够，准备一张容量足够的新 SD 卡或 USB 存储设备。'),
    ('挂载路径', '外置设备挂载在 /media 下，例如 /media/pi/BACKUP。不要把它挂到 /mnt。'),
    ('容量', '目标新卡至少要能容纳备份镜像的逻辑容量。恢复到更大卡后可再扩容。'),
    ('稳定性', '备份过程中不要拔出存储设备，不要强制关机，等待命令返回提示符。')
], widths=[1.35, 5.2])

add_heading('一 在树莓派上创建备份镜像', 1)
add_heading('1 连接并确认外置 SD 卡', 2)
add_body('把新的 SD 卡接入读卡器并连接到树莓派。执行 lsblk 查看设备和挂载点，确认新卡不是当前系统卡。桌面系统通常会把它挂载到 /media/$USER/卷标 目录下。')
add_code('lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS\ndf -h')
add_body('如果设备没有自动挂载，可以先创建挂载目录，再挂载对应分区。下面的 /dev/sda1 只是示例，必须根据 lsblk 的结果替换。')
add_code('sudo mkdir -p /media/backup\nsudo mount /dev/sda1 /media/backup\ndf -h /media/backup')
add_heading('2 下载脚本', 2)
add_code('cd ~\ngit clone https://github.com/nanhantianyi/rpi-backup.git\ncd rpi-backup')
add_heading('3 运行备份', 2)
add_body('把镜像文件直接写到外置设备时，文件名使用 /media 下的完整路径。下面的 backup-2026-11-15.img 可按日期或用途修改。')
add_code('sudo ./back.sh /media/backup/backup-2026-11-15.img')
add_body('脚本执行时会创建镜像分区、格式化镜像内的 FAT32 和 ext4 分区、复制 boot 和根文件系统内容、更新镜像中的 PARTUUID，最后卸载临时分区。命令结束后用 ls 和 du 检查文件是否存在。')
add_code('ls -lh /media/backup/backup-2026-11-15.img\nsync')
add_body('如果备份文件要留在系统卡上，文件名可以写成当前目录下的 backup.img，但必须先确认系统卡剩余空间足够。备份文件不能放在脚本复制到镜像的系统路径中，否则会增加空间占用或被脚本排除。')

add_heading('二 可选的真正压缩', 1)
add_body('如果需要减少长期存储占用，可以在备份结束并执行 sync 后压缩镜像。gzip 会读取整个镜像文件，因此速度和占用取决于镜像大小。')
add_code('cd /media/backup\ngzip -1 backup-2026-11-15.img\nls -lh backup-2026-11-15.img.gz')
add_body('压缩后的文件名是 backup-2026-11-15.img.gz。恢复时不要把 .gz 文件直接交给写卡工具，需要先解压为 .img，或使用 gzip -dc 直接通过管道写入目标设备。')

add_heading('三 把备份恢复到新的 SD 卡', 1)
add_body('恢复会覆盖目标 SD 卡上的分区和数据。先确认目标卡的设备名，再执行写入。目标卡应至少能容纳镜像的逻辑大小，容量小于镜像的卡无法恢复。')
add_heading('方法 A 在 Windows 上使用 Raspberry Pi Imager', 2)
add_number('把 backup.img 从保存位置复制到 Windows 电脑。若文件是 backup.img.gz，先用 7-Zip 解压得到 backup.img。')
add_number('打开 Raspberry Pi Imager，选择自定义镜像或 Use custom，选中 backup.img。')
add_number('选择新的 SD 卡作为存储设备，确认盘符和容量后开始写入。写入完成后安全弹出 SD 卡。')
add_number('把新卡插入树莓派并启动。首次启动后按“扩容”步骤处理更大容量卡的剩余空间。')
add_heading('方法 B 在 Linux 上使用 dd', 2)
add_body('先用 lsblk 确认整张目标 SD 卡的设备名，例如 /dev/sdb。写入目标必须是整盘设备，不是已有的分区号。')
add_code('lsblk -o NAME,SIZE,MODEL,MOUNTPOINTS\nsudo umount /dev/sdX1 /dev/sdX2 2>/dev/null\nsudo dd if=/path/to/backup.img of=/dev/sdX bs=4M status=progress conv=fsync\nsync')
add_body('把 /dev/sdX 替换成目标 SD 卡的整盘设备。写入完成后再拔卡。设备名填错会覆盖其他磁盘。')
add_heading('方法 C 直接把 .img.gz 写入 SD 卡', 2)
add_code('gzip -dc /path/to/backup.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync\nsync')

add_heading('四 首次启动后的扩容', 1)
add_body('如果新 SD 卡比备份时的原卡大，恢复后通常只会先使用镜像中已有的分区大小，剩余空间不会自动加入根分区。项目提供 resize.sh 扩容脚本，也可以使用树莓派系统自带的 raspi-config。')
add_heading('使用项目脚本扩容', 2)
add_code('cd ~/rpi-backup\nsudo bash resize.sh')
add_body('脚本会把根分区扩展到磁盘末尾，再调用对应文件系统工具扩展 ext4 等文件系统，最后重启。重启后用 df -h / 检查根分区容量。')
add_heading('使用 raspi-config 扩容', 2)
add_code('sudo raspi-config')
add_body('在菜单中选择 Advanced Options 或对应版本中的 Expand Filesystem，完成后退出并重启。菜单名称会随系统版本变化。')
add_code('df -h /\nlsblk')

add_heading('五 恢复后的检查', 1)
add_table(['检查内容', '命令或现象', '判断标准'], [
    ('系统启动', '树莓派能够正常进入系统', '启动过程没有停在 emergency mode。'),
    ('根分区', 'df -h /', '容量和已用空间符合预期。'),
    ('boot 分区', 'ls /boot 或 ls /boot/firmware', '能看到内核、配置和启动文件。'),
    ('网络与服务', 'systemctl --failed', '没有关键服务持续失败。'),
    ('文件完整性', '检查用户目录、配置、程序和数据', '关键文件可读取，应用能正常运行。')
], widths=[1.2, 2.65, 2.7])

add_heading('常见问题', 1)
add_body('备份时报空间不足。先检查 df -h 和外置设备的可用空间，确认外置设备挂载在 /media 下，再把镜像路径写到 /media 的挂载目录。')
add_body('提示脚本没有执行权限。使用 sudo bash back.sh 备份镜像名.img，或者先执行 chmod +x back.sh。')
add_body('恢复后系统没有使用新卡的全部容量。运行 sudo bash resize.sh 或使用 raspi-config 扩容，然后重启并用 df -h / 验证。')
add_body('新卡无法启动。重新确认写入的是整张目标卡，检查镜像文件是否完整，换用质量可靠且容量不小于镜像逻辑容量的 SD 卡。')
add_body('系统卡正在运行时备份可能遇到正在变化的文件。重要数据建议在停机或业务暂停后备份，并在恢复后检查数据库、日志和应用状态。')

add_heading('命令速查', 1)
add_code('git clone https://github.com/nanhantianyi/rpi-backup.git && cd rpi-backup\nsudo ./back.sh /media/backup/backup.img\n\n# 可选压缩\ngzip -1 /media/backup/backup.img\n\n# Linux 恢复\ngzip -dc /media/backup/backup.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync\n\n# 恢复后扩容\nsudo bash resize.sh')

add_heading('参考资料', 1)
add_body('项目仓库：https://github.com/nanhantianyi/rpi-backup')
add_body('项目说明中给出了镜像大小估算、外置设备挂载到 /media 的要求和恢复后的 resize.sh 扩容方法。本文根据项目 README、back.sh、resize.sh 以及用户提供的图片整理。')

# footer
footer = sec.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = fp.add_run('树莓派最小镜像备份与恢复指南')
set_run_font(fr, size=8.5, color=(128,128,128))

# core props
props = doc.core_properties
props.title = '树莓派最小镜像备份与新 SD 卡恢复操作指南'
props.subject = 'rpi-backup 脚本操作说明'
props.author = 'OpenAI'

doc.save(out_path)
print(out_path)

