from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import db, Character
from PIL import Image
import base64
import io

characters = Blueprint('characters', __name__)

NEN_TYPES = [
    ('Enhancement',    'สายเสริมพลัง'),
    ('Emission',       'สายแผ่พุ่ง'),
    ('Transmutation',  'สายเปลี่ยนแปลง'),
    ('Conjuration',    'สายแปรสภาพ'),
    ('Manipulation',   'สายควบคุม'),
    ('Specialization', 'สายพิเศษ'),
]
NEN_USAGE = {
    'Enhancement':    {'สายเสริมพลัง (Enhancement)': 100, 'สายเปลี่ยนแปลง (Transmutation)': 80, 'สายแผ่พุ่ง (Emission)': 80, 'สายแปรสภาพ (Conjuration)': 60, 'สายควบคุม (Manipulation)': 60, 'สายพิเศษ (Specialization)': 0},
    'Transmutation':  {'สายเปลี่ยนแปลง (Transmutation)': 100, 'สายเสริมพลัง (Enhancement)': 80, 'สายแปรสภาพ (Conjuration)': 80, 'สายแผ่พุ่ง (Emission)': 60, 'สายควบคุม (Manipulation)': 40, 'สายพิเศษ (Specialization)': 0},
    'Conjuration':    {'สายแปรสภาพ (Conjuration)': 100, 'สายเปลี่ยนแปลง (Transmutation)': 80, 'สายควบคุม (Manipulation)': 60, 'สายเสริมพลัง (Enhancement)': 60, 'สายแผ่พุ่ง (Emission)': 40, 'สายพิเศษ (Specialization)': 0},
    'Specialization': {'สายพิเศษ (Specialization)': 100, 'สายเสริมพลัง (Enhancement)': 60, 'สายเปลี่ยนแปลง (Transmutation)': 60, 'สายแปรสภาพ (Conjuration)': 60, 'สายควบคุม (Manipulation)': 60, 'สายแผ่พุ่ง (Emission)': 60},
    'Manipulation':   {'สายควบคุม (Manipulation)': 100, 'สายแผ่พุ่ง (Emission)': 80, 'สายแปรสภาพ (Conjuration)': 60, 'สายเสริมพลัง (Enhancement)': 60, 'สายเปลี่ยนแปลง (Transmutation)': 40, 'สายพิเศษ (Specialization)': 0},
    'Emission':       {'สายแผ่พุ่ง (Emission)': 100, 'สายควบคุม (Manipulation)': 80, 'สายเสริมพลัง (Enhancement)': 80, 'สายเปลี่ยนแปลง (Transmutation)': 60, 'สายแปรสภาพ (Conjuration)': 40, 'สายพิเศษ (Specialization)': 0},
}
return render_template('characters/add.html', nen_types=NEN_TYPES, nen_usage=NEN_USAGE)

def save_image(file, max_size_kb=500, max_dimension=1024):
    """บีบอัดรูปก่อนแปลงเป็น base64 — รับได้ทุกขนาด ผลลัพธ์ไม่เกิน max_size_kb"""
    if not file or file.filename == '':
        return None

    img = Image.open(file.stream)

    # แปลงเป็น RGB เผื่อรูป PNG มี alpha channel (RGBA) หรือ palette (P)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # ย่อ dimension ถ้ากว้าง/สูงเกิน max_dimension (คงสัดส่วนไว้)
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # บีบ quality ลงเรื่อยๆ จนขนาดไม่เกิน max_size_kb
    quality = 85
    while quality >= 20:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        if buffer.tell() / 1024 <= max_size_kb:
            break
        quality -= 10

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    return f'data:image/jpeg;base64,{encoded}'


# -------------------- INDEX --------------------
@characters.route('/')
def index():
    search = request.args.get('search', '')
    nen_filter = request.args.get('nen_type', '')

    query = Character.query
    if search:
        query = query.filter(Character.name.ilike(f'%{search}%'))
    if nen_filter:
        query = query.filter(Character.nen_type_en == nen_filter)

    chars = query.order_by(Character.name).all()
    return render_template('characters/index.html',
                           characters=chars,
                           nen_types=NEN_TYPES,
                           search=search,
                           nen_filter=nen_filter)


# -------------------- ADD --------------------
@characters.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nen_en = request.form.get('nen_type_en')
        nen_th = dict(NEN_TYPES).get(nen_en, '')

        image_data = save_image(request.files.get('image'))

        char = Character(
            name        = request.form.get('name'),
            nen_type_en = nen_en,
            nen_type_th = nen_th,
            ability     = request.form.get('ability'),
            description = request.form.get('description'),
            image       = image_data,
        )
        db.session.add(char)
        db.session.commit()
        flash(f'เพิ่ม {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.index'))
# ✅ เพิ่ม nen_usage=NEN_USAGE
return render_template('characters/add.html', nen_types=NEN_TYPES, nen_usage=NEN_USAGE)


# -------------------- EDIT --------------------
@characters.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    char = Character.query.get_or_404(id)

    if request.method == 'POST':
        nen_en = request.form.get('nen_type_en')
        char.name        = request.form.get('name')
        char.nen_type_en = nen_en
        char.nen_type_th = dict(NEN_TYPES).get(nen_en, '')
        char.ability     = request.form.get('ability')
        char.description = request.form.get('description')

        # อัปเดตรูปเฉพาะตอนที่มีการอัปโหลดใหม่
        new_image = save_image(request.files.get('image'))
        if new_image:
            char.image = new_image

        db.session.commit()
        flash(f'แก้ไข {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.index'))

    return render_template('characters/edit.html', character=char, nen_types=NEN_TYPES)


# -------------------- DELETE --------------------
@characters.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    char = Character.query.get_or_404(id)
    db.session.delete(char)
    db.session.commit()
    flash(f'ลบ {char.name} แล้วครับ', 'warning')
    return redirect(url_for('characters.index'))

# -------------------- NEN GUIDE --------------------
@characters.route('/nen-guide')
def nen_guide():
    NEN_INFO = [
        {
            'en': 'Enhancement', 'th': 'สายเสริมพลัง',
            'color': '#4caf50', 'icon': 'enhancement.png',
            'desc': 'เพิ่มความสามารถทางกายภาพของตัวเองหรือสิ่งของ แข็งแกร่งที่สุดในการต่อสู้ตรงๆ เป็นสายที่พบบ่อยที่สุด (27% ของผู้ใช้เน็น)',
            'usage': NEN_USAGE['Enhancement']
        },
        {
            'en': 'Emission', 'th': 'สายแผ่พุ่ง',
            'color': '#1e90ff', 'icon': 'emission.png',
            'desc': 'ปล่อยออร่าออกจากร่างกาย โจมตีได้จากระยะไกล เป็นสายที่พบบ่อยเป็นอันดับสอง (24%)',
            'usage': NEN_USAGE['Emission']
        },
        {
            'en': 'Transmutation', 'th': 'สายเปลี่ยนแปลง',
            'color': '#ffc107', 'icon': 'transmutation.png',
            'desc': 'เปลี่ยนคุณสมบัติของออร่าให้เป็นสิ่งอื่น เช่น ไฟฟ้า ยาง ไม่ได้สร้างวัตถุจริง แต่เลียนแบบคุณสมบัติ (19%)',
            'usage': NEN_USAGE['Transmutation']
        },
        {
            'en': 'Conjuration', 'th': 'สายแปรสภาพ',
            'color': '#ab47bc', 'icon': 'conjuration.png',
            'desc': 'สร้างวัตถุจริงจากออร่า สิ่งที่สร้างคงอยู่ได้แม้ไม่ใช้ออร่า การตั้งเงื่อนไขจะทำให้พลังแกร่งขึ้น (15%)',
            'usage': NEN_USAGE['Conjuration']
        },
        {
            'en': 'Manipulation', 'th': 'สายควบคุม',
            'color': '#ff8c42', 'icon': 'manipulation.png',
            'desc': 'ควบคุมสิ่งมีชีวิตหรือวัตถุด้วยออร่า เงื่อนไขที่ยากกว่าจะให้การควบคุมที่ดีกว่า (15%)',
            'usage': NEN_USAGE['Manipulation']
        },
        {
            'en': 'Specialization', 'th': 'สายพิเศษ',
            'color': '#ef5350', 'icon': 'specialization.png',
            'desc': 'ความสามารถนอกหมวดหมู่ เป็นสายที่หายากที่สุด (0.033%) มักเปลี่ยนมาจาก Conjuration หรือ Manipulation',
            'usage': NEN_USAGE['Specialization']
        },
    ]

    NEN_TECHNIQUES = [
        {
            'category': '🔰 วิชาพื้นฐาน (Basic Techniques)',
            'techniques': [
                {'name': 'เท็น (Ten - 纏)', 'desc': 'ห่อหุ้มออร่ารอบร่างกาย ป้องกันการสูญเสียออร่าและชะลอการแก่ชรา พื้นฐานของทุกวิชา'},
                {'name': 'เร็น (Ren - 錬)', 'desc': 'เพิ่มปริมาณออร่าในร่างกายให้มากกว่าปกติ เสริมพลังโจมตีและป้องกัน แต่ใช้ออร่าเร็วกว่า Ten'},
                {'name': 'เซ็ตสึ (Zetsu - 絶)', 'desc': 'หยุดการไหลของออร่าทั้งหมด ซ่อนพลังเน็น ช่วยฟื้นฟูร่างกาย แต่เสี่ยงต่อการโจมตีจากผู้ใช้เน็น'},
                {'name': 'ฮัตสึ (Hatsu - 発)', 'desc': 'ปล่อยออร่าในแบบเฉพาะตัวของผู้ใช้ คือความสามารถพิเศษส่วนตัวที่สะท้อนบุคลิกและสายเน็น'},
            ]
        },
        {
            'category': '⚡ วิชาขั้นสูง (Advanced Techniques)',
            'techniques': [
                {'name': 'เกียว (Gyo - 凝)', 'desc': 'รวมออร่า 100% ไปที่จุดเดียว มักใช้กับดวงตาเพื่อมองเห็นออร่าที่ซ่อนอยู่ (In)'},
                {'name': 'อิน (In - 隱)', 'desc': 'ซ่อนออร่าให้มองไม่เห็นแม้ใช้ Gyo ขั้นสูงมาก ใช้สำหรับซุ่มโจมตีหรือสอดแนม'},
                {'name': 'เค็น (Ken - 堅)', 'desc': 'คง Ren ตลอดทั่วร่างกายสำหรับป้องกันระยะยาว สมดุลระหว่าง Ren และ Ten ป้องกันได้ทั้งตัว'},
                {'name': 'โค (Ko - 硬)', 'desc': 'รวมออร่าทั้งหมดไปจุดเดียว พลังโจมตี/ป้องกันสูงสุด แต่ส่วนที่เหลือไม่มีการป้องกัน'},
                {'name': 'ริว (Ryu - 流)', 'desc': 'แจกจ่ายออร่าแบบ Real-time ระหว่างส่วนต่างๆ ของร่างกาย ต้องอาศัยทักษะและประสบการณ์สูง'},
                {'name': 'ชู (Shu - 周)', 'desc': 'ขยายออร่าไปครอบวัตถุที่ถืออยู่ ทำให้วัตถุแข็งแกร่งและได้รับการป้องกันเสมือนร่างกาย'},
                {'name': 'เอ็น (En - 円)', 'desc': 'ขยาย Ten ออกไปรอบๆ ร่างกายในรัศมีกว้าง รับรู้ทุกสิ่งในรัศมีนั้น ต้องใช้ออร่ามาก'},
                {'name': 'ชุน (Shun - 瞬)', 'desc': 'ใช้ Ten ขณะเคลื่อนที่เร็ว ออร่าจะห่อหุ้มร่างกายขณะวิ่ง ลดความต้านทานและป้องกันได้ขณะเคลื่อนไหว'},
            ]
        },
        {
            'category': '🔒 หลักการเสริมพลัง (Vow & Limitation)',
            'techniques': [
                {'name': 'การปฏิญาณ (Vow)', 'desc': 'การตั้งคำมั่นสัญญากับตัวเองเพื่อเพิ่มพลัง ยิ่งเงื่อนไขยากหรืออันตราย ยิ่งเพิ่มพลังมาก'},
                {'name': 'การจำกัด (Limitation)', 'desc': 'ตั้งขีดจำกัดการใช้ความสามารถ เช่น ใช้ได้เฉพาะกับศัตรูบางประเภท จะทำให้พลังโดยรวมสูงขึ้น'},
            ]
        }
    ]
    