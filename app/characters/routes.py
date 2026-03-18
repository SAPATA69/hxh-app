from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ..models import db, Character
from PIL import Image
import base64
import io
import json

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


def save_image(file, max_size_kb=500, max_dimension=1024):
    if not file or file.filename == '':
        return None
    img = Image.open(file.stream)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
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


def save_gallery_images(files, max_images=5, max_size_kb=600, max_dimension=1200):
    """Save multiple images for gallery, return JSON string of base64 array."""
    images = []
    for file in files:
        if len(images) >= max_images:
            break
        if file and file.filename != '':
            img_data = save_image(file, max_size_kb, max_dimension)
            if img_data:
                images.append(img_data)
    return json.dumps(images) if images else None


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


# -------------------- DETAIL --------------------
@characters.route('/<int:id>')
def detail(id):
    char = Character.query.get_or_404(id)
    gallery = []
    if char.gallery_images:
        try:
            gallery = json.loads(char.gallery_images)
        except Exception:
            gallery = []
    nen_usage = NEN_USAGE.get(char.nen_type_en, {})
    nen_color_map = {
        'Enhancement': '#4caf50',
        'Emission': '#1e90ff',
        'Transmutation': '#ffc107',
        'Conjuration': '#ab47bc',
        'Manipulation': '#ff8c42',
        'Specialization': '#ef5350',
    }
    nen_color = nen_color_map.get(char.nen_type_en, '#1e90ff')
    return render_template('characters/detail.html',
                           character=char,
                           gallery=gallery,
                           nen_usage=nen_usage,
                           nen_color=nen_color)


# -------------------- ADD --------------------
@characters.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nen_en = request.form.get('nen_type_en')
        nen_th = dict(NEN_TYPES).get(nen_en, '')
        image_data = save_image(request.files.get('image'))

        # Handle gallery images (up to 5)
        gallery_files = request.files.getlist('gallery_images')
        gallery_data = save_gallery_images(gallery_files)

        char = Character(
            name           = request.form.get('name'),
            nen_type_en    = nen_en,
            nen_type_th    = nen_th,
            ability        = request.form.get('ability'),
            description    = request.form.get('description'),
            biography      = request.form.get('biography'),
            image          = image_data,
            gallery_images = gallery_data,
        )
        db.session.add(char)
        db.session.commit()
        flash(f'เพิ่ม {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.index'))

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
        char.biography   = request.form.get('biography')

        new_image = save_image(request.files.get('image'))
        if new_image:
            char.image = new_image

        # Handle gallery: new uploads + keep existing
        gallery_files = request.files.getlist('gallery_images')
        new_gallery = []
        for f in gallery_files:
            if f and f.filename != '':
                img = save_image(f, max_size_kb=600, max_dimension=1200)
                if img:
                    new_gallery.append(img)

        # Merge with existing gallery (if "keep_gallery" checked)
        keep_existing = request.form.get('keep_gallery') == 'on'
        if keep_existing and char.gallery_images:
            try:
                existing = json.loads(char.gallery_images)
            except Exception:
                existing = []
            combined = existing + new_gallery
            char.gallery_images = json.dumps(combined[:5]) if combined else None
        else:
            char.gallery_images = json.dumps(new_gallery[:5]) if new_gallery else char.gallery_images

        db.session.commit()
        flash(f'แก้ไข {char.name} สำเร็จแล้วครับ!', 'success')
        return redirect(url_for('characters.detail', id=char.id))

    existing_gallery = []
    if char.gallery_images:
        try:
            existing_gallery = json.loads(char.gallery_images)
        except Exception:
            existing_gallery = []

    return render_template('characters/edit.html',
                           character=char,
                           nen_types=NEN_TYPES,
                           existing_gallery=existing_gallery)


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
        {'en': 'Enhancement', 'th': 'สายเสริมพลัง', 'color': '#4caf50', 'icon': 'enhancement.png',
         'desc': 'เพิ่มความสามารถทางกายภาพของตัวเองหรือสิ่งของ แข็งแกร่งที่สุดในการต่อสู้ตรงๆ (27%)',
         'usage': NEN_USAGE['Enhancement']},
        {'en': 'Emission', 'th': 'สายแผ่พุ่ง', 'color': '#1e90ff', 'icon': 'emission.png',
         'desc': 'ปล่อยออร่าออกจากร่างกาย โจมตีได้จากระยะไกล (24%)',
         'usage': NEN_USAGE['Emission']},
        {'en': 'Transmutation', 'th': 'สายเปลี่ยนแปลง', 'color': '#ffc107', 'icon': 'transmutation.png',
         'desc': 'เปลี่ยนคุณสมบัติของออร่าให้เป็นสิ่งอื่น เช่น ไฟฟ้า ยาง (19%)',
         'usage': NEN_USAGE['Transmutation']},
        {'en': 'Conjuration', 'th': 'สายแปรสภาพ', 'color': '#ab47bc', 'icon': 'conjuration.png',
         'desc': 'สร้างวัตถุจริงจากออร่า คงอยู่ได้แม้ไม่ใช้ออร่า (15%)',
         'usage': NEN_USAGE['Conjuration']},
        {'en': 'Manipulation', 'th': 'สายควบคุม', 'color': '#ff8c42', 'icon': 'manipulation.png',
         'desc': 'ควบคุมสิ่งมีชีวิตหรือวัตถุด้วยออร่า (15%)',
         'usage': NEN_USAGE['Manipulation']},
        {'en': 'Specialization', 'th': 'สายพิเศษ', 'color': '#ef5350', 'icon': 'specialization.png',
         'desc': 'ความสามารถนอกหมวดหมู่ หายากที่สุด (0.033%)',
         'usage': NEN_USAGE['Specialization']},
    ]

    NEN_TECHNIQUES = [
        {
            'category': '🔰 วิชาพื้นฐาน (Basic Techniques)',
            'techniques': [
                {'name': 'เท็น (Ten - 纏)', 'desc': 'ห่อหุ้มออร่ารอบร่างกาย ป้องกันการสูญเสียออร่าและชะลอการแก่ชรา พื้นฐานของทุกวิชา'},
                {'name': 'เร็น (Ren - 錬)', 'desc': 'เพิ่มปริมาณออร่าในร่างกายให้มากกว่าปกติ เสริมพลังโจมตีและป้องกัน'},
                {'name': 'เซ็ตสึ (Zetsu - 絶)', 'desc': 'หยุดการไหลของออร่าทั้งหมด ซ่อนพลังเน็น ช่วยฟื้นฟูร่างกาย'},
                {'name': 'ฮัตสึ (Hatsu - 発)', 'desc': 'ปล่อยออร่าในแบบเฉพาะตัวของผู้ใช้ คือความสามารถพิเศษส่วนตัว'},
            ]
        },
        {
            'category': '⚡ วิชาขั้นสูง (Advanced Techniques)',
            'techniques': [
                {'name': 'เกียว (Gyo - 凝)', 'desc': 'รวมออร่า 100% ไปที่จุดเดียว มักใช้กับดวงตาเพื่อมองเห็นออร่าที่ซ่อนอยู่'},
                {'name': 'อิน (In - 隱)', 'desc': 'ซ่อนออร่าให้มองไม่เห็นแม้ใช้ Gyo ขั้นสูงมาก'},
                {'name': 'เค็น (Ken - 堅)', 'desc': 'คง Ren ตลอดทั่วร่างกายสำหรับป้องกันระยะยาว'},
                {'name': 'โค (Ko - 硬)', 'desc': 'รวมออร่าทั้งหมดไปจุดเดียว พลังโจมตี/ป้องกันสูงสุด'},
                {'name': 'ริว (Ryu - 流)', 'desc': 'แจกจ่ายออร่าแบบ Real-time ระหว่างส่วนต่างๆ ของร่างกาย'},
                {'name': 'ชู (Shu - 周)', 'desc': 'ขยายออร่าไปครอบวัตถุที่ถืออยู่ ทำให้วัตถุแข็งแกร่ง'},
                {'name': 'เอ็น (En - 円)', 'desc': 'ขยาย Ten ออกไปรอบๆ ร่างกายในรัศมีกว้าง รับรู้ทุกสิ่งในรัศมีนั้น'},
                {'name': 'ชุน (Shun - 瞬)', 'desc': 'ใช้ Ten ขณะเคลื่อนที่เร็ว ออร่าห่อหุ้มร่างกายขณะวิ่ง'},
            ]
        },
        {
            'category': '🔒 หลักการเสริมพลัง (Vow & Limitation)',
            'techniques': [
                {'name': 'การปฏิญาณ (Vow)', 'desc': 'ตั้งคำมั่นสัญญากับตัวเองเพื่อเพิ่มพลัง ยิ่งเงื่อนไขยากหรืออันตราย ยิ่งเพิ่มพลังมาก'},
                {'name': 'การจำกัด (Limitation)', 'desc': 'ตั้งขีดจำกัดการใช้ความสามารถ เช่น ใช้ได้เฉพาะกับศัตรูบางประเภท'},
            ]
        }
    ]

    return render_template('characters/nen_guide.html', nen_info=NEN_INFO, nen_techniques=NEN_TECHNIQUES)

# -------------------- NEN TYPE EDIT (admin) --------------------
@characters.route('/nen-type/<nen_en>/edit', methods=['POST'])
@login_required
def edit_nen_type(nen_en):
    from ..models import NenTypeInfo
    info = NenTypeInfo.query.filter_by(nen_type_en=nen_en).first()
    if not info:
        info = NenTypeInfo(nen_type_en=nen_en)
        db.session.add(info)

    info.extended = request.form.get('extended', '')

    new_image = save_image(request.files.get('nen_image'), max_size_kb=800, max_dimension=1200)
    if new_image:
        info.image = new_image

    db.session.commit()
    flash(f'อัปเดตข้อมูล {nen_en} แล้วครับ', 'success')
    return redirect(url_for('characters.nen_guide') + f'#{nen_en}')

@characters.route('/nen-guide')
def nen_guide():
    from ..models import NenTypeInfo
    # โหลด extended info จาก DB
    nen_extras = {n.nen_type_en: n for n in NenTypeInfo.query.all()}
    
    NEN_INFO = [
        {'en': 'Enhancement', 'th': 'สายเสริมพลัง', 'color': '#4caf50', 'icon': 'enhancement.png',
         'desc': 'เพิ่มความสามารถทางกายภาพของตัวเองหรือสิ่งของ แข็งแกร่งที่สุดในการต่อสู้ตรงๆ (27%)',
         'usage': NEN_USAGE['Enhancement'],
         'extra': nen_extras.get('Enhancement')},
        {'en': 'Emission', 'th': 'สายแผ่พุ่ง', 'color': '#1e90ff', 'icon': 'emission.png',
         'desc': 'ปล่อยออร่าออกจากร่างกาย โจมตีได้จากระยะไกล (24%)',
         'usage': NEN_USAGE['Emission'],
         'extra': nen_extras.get('Emission')},
        {'en': 'Transmutation', 'th': 'สายเปลี่ยนแปลง', 'color': '#ffc107', 'icon': 'transmutation.png',
         'desc': 'เปลี่ยนคุณสมบัติของออร่าให้เป็นสิ่งอื่น เช่น ไฟฟ้า ยาง (19%)',
         'usage': NEN_USAGE['Transmutation'],
         'extra': nen_extras.get('Transmutation')},
        {'en': 'Conjuration', 'th': 'สายแปรสภาพ', 'color': '#ab47bc', 'icon': 'conjuration.png',
         'desc': 'สร้างวัตถุจริงจากออร่า คงอยู่ได้แม้ไม่ใช้ออร่า (15%)',
         'usage': NEN_USAGE['Conjuration'],
         'extra': nen_extras.get('Conjuration')},
        {'en': 'Manipulation', 'th': 'สายควบคุม', 'color': '#ff8c42', 'icon': 'manipulation.png',
         'desc': 'ควบคุมสิ่งมีชีวิตหรือวัตถุด้วยออร่า (15%)',
         'usage': NEN_USAGE['Manipulation'],
         'extra': nen_extras.get('Manipulation')},
        {'en': 'Specialization', 'th': 'สายพิเศษ', 'color': '#ef5350', 'icon': 'specialization.png',
         'desc': 'ความสามารถนอกหมวดหมู่ หายากที่สุด (0.033%)',
         'usage': NEN_USAGE['Specialization'],
         'extra': nen_extras.get('Specialization')},
    ]
    # ... NEN_TECHNIQUES เหมือนเดิม ...
    return render_template('characters/nen_guide.html', nen_info=NEN_INFO, nen_techniques=NEN_TECHNIQUES)