import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

SCREENSHOTS_DIR = Path(r"C:\Users\jorai\.gemini\antigravity\scratch\gestion-documental\docs\screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def create_base_canvas(width=1200, height=750, title="DocuControl - Plataforma de Gestión Documental"):
    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)

    # Window title bar (Mac/Windows style)
    draw.rectangle([(0, 0), (width, 42)], fill="#1e293b")
    # Window action dots
    draw.ellipse([(16, 15), (28, 27)], fill="#ef4444")
    draw.ellipse([(36, 15), (48, 27)], fill="#f59e0b")
    draw.ellipse([(56, 15), (68, 27)], fill="#10b981")

    # Title text
    draw.text((width // 2 - 160, 13), title, fill="#cbd5e1")

    # URL / address bar
    draw.rectangle([(width - 320, 8), (width - 20, 34)], fill="#0f172a", outline="#334155")
    draw.text((width - 305, 13), "🔒 http://127.0.0.1:8000/app", fill="#94a3b8")

    # Main content background
    draw.rectangle([(0, 42), (width, height)], fill="#f8fafc")
    return img, draw

def render_topbar(draw, width, current_user="Carlos Morales", role="Editor"):
    # Navbar
    draw.rectangle([(0, 42), (width, 102)], fill="#0f172a")
    # Brand
    draw.rectangle([(24, 54), (58, 88)], fill="#2563eb")
    draw.text((32, 60), "📁", fill="#ffffff")
    draw.text((70, 56), "DocuControl", fill="#ffffff")
    draw.text((70, 74), "Plataforma de Gestión Documental con Control de Versiones", fill="#94a3b8")

    # Search bar
    draw.rectangle([(400, 54), (780, 88)], fill="#1e293b", outline="#334155")
    draw.text((415, 63), "🔍 Buscar documentos por nombre, etiqueta o autor...", fill="#64748b")

    # User profile & badge
    draw.text((width - 240, 56), current_user, fill="#ffffff")
    draw.rectangle([(width - 240, 74), (width - 170, 90)], fill="#1e40af")
    draw.text((width - 232, 75), f"Rol: {role}", fill="#93c5fd")
    draw.rectangle([(width - 90, 58), (width - 24, 84)], fill="#dc2626")
    draw.text((width - 76, 64), "Salir", fill="#ffffff")

def render_sidebar(draw, active_item="Todos"):
    # Sidebar
    draw.rectangle([(0, 102), (240, 750)], fill="#ffffff", outline="#e2e8f0")
    
    # Upload button
    draw.rectangle([(20, 120), (220, 160)], fill="#2563eb")
    draw.text((42, 133), "☁️ Subir archivo nuevo", fill="#ffffff")

    # Menu items
    items = [
        ("📁 Todos los documentos", active_item == "Todos"),
        ("🕒 Modificados recientes", active_item == "Recientes"),
        ("🔒 Archivos en edición", active_item == "Bloqueados"),
        ("🗑️ Papelera de reciclaje", active_item == "Papelera"),
        ("🛡️ Panel de Administración", active_item == "Admin"),
    ]
    y = 180
    for label, is_active in items:
        if is_active:
            draw.rectangle([(12, y - 4), (228, y + 26)], fill="#eff6ff")
            draw.text((24, y), label, fill="#1d4ed8")
        else:
            draw.text((24, y), label, fill="#334155")
        y += 38

    # Folders header
    draw.line([(20, y), (220, y)], fill="#e2e8f0", width=1)
    y += 12
    draw.text((24, y), "CARPETAS EMPRESARIALES", fill="#94a3b8")
    y += 24
    folders = [
        "📂 01. Dirección General (3)",
        "📂 02. Finanzas y Presupuesto (8)",
        "📂 03. Recursos Humanos (5)",
        "📂 04. Operaciones y Proyectos (12)",
        "📂 05. Políticas y Normatividad (4)"
    ]
    for f in folders:
        draw.text((24, y), f, fill="#475569")
        y += 26

# 1. Screen: Login
def gen_screen_login():
    img, draw = create_base_canvas(title="DocuControl - Inicio de Sesión y Autenticación")
    # Background pattern
    draw.rectangle([(0, 42), (1200, 750)], fill="#0f172a")

    # Card
    draw.rectangle([(400, 130), (800, 660)], fill="#ffffff", outline="#334155")
    # Card Header
    draw.rectangle([(400, 130), (800, 240)], fill="#1e293b")
    draw.rectangle([(570, 150), (630, 210)], fill="#2563eb")
    draw.text((586, 168), "🛡️", fill="#ffffff")
    draw.text((495, 220), "DocuControl - Inicio de Sesión", fill="#ffffff")

    # Form inputs
    draw.text((435, 270), "USUARIO O CORREO ELECTRÓNICO", fill="#475569")
    draw.rectangle([(435, 292), (765, 332)], fill="#f8fafc", outline="#cbd5e1")
    draw.text((450, 305), "carlos.editor@empresa.local", fill="#0f172a")

    draw.text((435, 355), "CONTRASEÑA", fill="#475569")
    draw.rectangle([(435, 377), (765, 417)], fill="#f8fafc", outline="#cbd5e1")
    draw.text((450, 390), "••••••••••••••••", fill="#0f172a")

    # Submit button
    draw.rectangle([(435, 445), (765, 490)], fill="#2563eb")
    draw.text((535, 460), "Entrar a la Plataforma", fill="#ffffff")

    # Quick Role Selector Box
    draw.rectangle([(435, 520), (765, 635)], fill="#f1f5f9", outline="#e2e8f0")
    draw.text((445, 530), "Prueba rápida por Roles (Demostración de perfiles):", fill="#1e293b")
    draw.rectangle([(445, 555), (590, 585)], fill="#ffffff", outline="#93c5fd")
    draw.text((455, 563), "👑 Administrador", fill="#1e40af")
    draw.rectangle([(610, 555), (755, 585)], fill="#eff6ff", outline="#2563eb")
    draw.text((620, 563), "✏️ Carlos (Editor)", fill="#1e40af")

    draw.rectangle([(445, 595), (590, 625)], fill="#ffffff", outline="#93c5fd")
    draw.text((455, 603), "🔍 Elena (Revisor)", fill="#1e40af")
    draw.rectangle([(610, 595), (755, 625)], fill="#ffffff", outline="#93c5fd")
    draw.text((620, 603), "📖 Mario (Lector)", fill="#1e40af")

    img.save(SCREENSHOTS_DIR / "01_login_screen.png")

# 2. Screen: File Explorer Dashboard
def gen_screen_explorer():
    img, draw = create_base_canvas(title="DocuControl - Explorador Corporativo de Archivos")
    render_topbar(draw, 1200, "Carlos Morales", "Editor")
    render_sidebar(draw, "Todos")

    # Main area header
    draw.rectangle([(240, 102), (1200, 155)], fill="#f8fafc", outline="#e2e8f0")
    draw.text((260, 120), "Directorio Raíz / Todos los documentos corporativos (24 archivos activos)", fill="#0f172a")

    # Table Header
    draw.rectangle([(260, 175), (1170, 205)], fill="#f1f5f9")
    draw.text((275, 185), "NOMBRE DEL DOCUMENTO", fill="#64748b")
    draw.text((600, 185), "VERSIÓN", fill="#64748b")
    draw.text((700, 185), "ESTADO DE EDICIÓN", fill="#64748b")
    draw.text((880, 185), "ÚLTIMO CAMBIO", fill="#64748b")
    draw.text((1050, 185), "ACCIONES", fill="#64748b")

    # Table Rows
    rows = [
        ("📄 Politica_Seguridad_Informacion.txt", "v2 (Vigente)", "🟢 Disponible", "Hoy 16:45", "#22c55e", "Edición libre"),
        ("📊 Presupuesto_Consolidado_2026.xlsx", "v4 (Vigente)", "🔒 En edición (Carlos M.)", "Hoy 15:10", "#f59e0b", "Bloqueo activo"),
        ("📑 Manual_Procedimientos_Operativos.pdf", "v1 (Vigente)", "🟢 Disponible", "Ayer 11:20", "#22c55e", "Edición libre"),
        ("📋 Contrato_Marco_Prestacion_Servicios.docx", "v3 (Vigente)", "🟢 Revisado", "20/11/2026", "#3b82f6", "Revisión OK"),
        ("📐 Plano_Arquitectonico_Sede_Norte.dwg", "v1 (Vigente)", "🟢 Disponible", "18/11/2026", "#22c55e", "Edición libre"),
        ("📝 Minuta_Reunion_Directorio_Nov.txt", "v2 (Vigente)", "🟢 Disponible", "15/11/2026", "#22c55e", "Edición libre"),
    ]
    y = 215
    for name, ver, status, date, color, desc in rows:
        draw.rectangle([(260, y), (1170, y + 55)], fill="#ffffff", outline="#e2e8f0")
        draw.text((275, y + 18), name, fill="#0f172a")
        
        # Version badge
        draw.rectangle([(600, y + 14), (670, y + 38)], fill="#dbeafe")
        draw.text((610, y + 18), ver.split()[0], fill="#1e40af")

        # Status badge
        draw.rectangle([(700, y + 14), (850, y + 38)], fill="#f8fafc", outline=color)
        draw.text((710, y + 18), status, fill=color)

        draw.text((880, y + 18), date, fill="#475569")
        draw.text((1050, y + 18), "👁️ Ver  ⬇️ Descargar", fill="#2563eb")
        y += 65

    # Concurrency Callout annotation
    draw.rectangle([(260, 620), (1170, 710)], fill="#eff6ff", outline="#3b82f6")
    draw.text((280, 635), "💡 Control Preventivo de Sobrescritura:", fill="#1d4ed8")
    draw.text((280, 660), "El archivo 'Presupuesto_Consolidado_2026.xlsx' se encuentra bloqueado exclusivamente por Carlos Morales.", fill="#1e293b")
    draw.text((280, 680), "Cualquier otro usuario que intente modificarlo recibirá aviso preventivo inmediato con opción de solo lectura.", fill="#475569")

    img.save(SCREENSHOTS_DIR / "02_explorer_dashboard.png")

# 3. Screen: Version History Timeline
def gen_screen_timeline():
    img, draw = create_base_canvas(title="DocuControl - Historial Inmutable de Versiones")
    render_topbar(draw, 1200, "Carlos Morales", "Editor")

    # Modal Overlay
    draw.rectangle([(0, 42), (1200, 750)], fill="#00000066")
    # Modal Window
    draw.rectangle([(160, 80), (1040, 720)], fill="#ffffff", outline="#94a3b8")
    # Modal Header
    draw.rectangle([(160, 80), (1040, 145)], fill="#0f172a")
    draw.text((190, 95), "📄 Politica_Seguridad_Informacion.txt", fill="#ffffff")
    draw.text((190, 118), "Carpeta: 05. Políticas y Normatividad | Creado por: Carlos Morales | Hash: SHA-256 Activo", fill="#94a3b8")
    draw.text((1000, 100), "✕", fill="#ffffff")

    # Action bar inside modal
    draw.rectangle([(160, 145), (1040, 195)], fill="#f8fafc", outline="#e2e8f0")
    draw.rectangle([(180, 155), (320, 185)], fill="#f59e0b")
    draw.text((195, 162), "🔒 Bloquear p/ edición", fill="#ffffff")
    draw.rectangle([(335, 155), (490, 185)], fill="#2563eb")
    draw.text((348, 162), "☁️ Subir nueva versión", fill="#ffffff")
    draw.rectangle([(505, 155), (640, 185)], fill="#ffffff", outline="#cbd5e1")
    draw.text((518, 162), "⬇️ Descargar v2", fill="#334155")
    draw.rectangle([(655, 155), (770, 185)], fill="#ffffff", outline="#cbd5e1")
    draw.text((670, 162), "👁️ Vista previa", fill="#334155")

    # Timeline Section
    draw.text((190, 215), "LÍNEA DE TIEMPO DE VERSIONES (3 VERSIONES INMUTABLES REGISTRADAS)", fill="#1e293b")
    draw.line([(220, 255), (220, 680)], fill="#94a3b8", width=3)

    # Version 3 (Restored / Vigente)
    draw.ellipse([(212, 255), (228, 271)], fill="#2563eb")
    draw.rectangle([(250, 245), (1000, 360)], fill="#eff6ff", outline="#2563eb")
    draw.text((270, 260), "Versión 3 (VIGENTE ACTUAL)", fill="#1e40af")
    draw.text((800, 260), "Hoy 17:10 • Autor: Carlos Morales", fill="#64748b")
    draw.rectangle([(270, 285), (980, 318)], fill="#ffffff", outline="#bfdbfe")
    draw.text((280, 294), "Motivo obligatorio: 'Restauración a partir del contenido de la versión v1 por solicitud de auditoría'", fill="#1e293b")
    draw.text((270, 330), "Tamaño: 2.4 KB  •  SHA-256: 8a4f91b72c91...  •  Revisión: Aprobada", fill="#475569")
    draw.rectangle([(880, 325), (980, 350)], fill="#2563eb")
    draw.text((895, 330), "⬇️ Descargar", fill="#ffffff")

    # Version 2
    draw.ellipse([(212, 395), (228, 411)], fill="#64748b")
    draw.rectangle([(250, 385), (1000, 500)], fill="#ffffff", outline="#cbd5e1")
    draw.text((270, 400), "Versión 2 (Histórica inmutable)", fill="#0f172a")
    draw.text((800, 400), "Ayer 14:30 • Autor: Carlos Morales", fill="#64748b")
    draw.rectangle([(270, 425), (980, 458)], fill="#f8fafc", outline="#e2e8f0")
    draw.text((280, 434), "Motivo obligatorio: 'Inclusión de normas sobre expiración de claves y política de contraseñas'", fill="#1e293b")
    draw.text((270, 470), "Tamaño: 2.8 KB  •  SHA-256: 3c72b1aa5409...", fill="#475569")
    draw.rectangle([(750, 465), (860, 490)], fill="#f1f5f9", outline="#94a3b8")
    draw.text((760, 470), "🔄 Restaurar", fill="#0f172a")
    draw.rectangle([(875, 465), (980, 490)], fill="#ffffff", outline="#2563eb")
    draw.text((885, 470), "📊 Comparar v1", fill="#2563eb")

    # Version 1
    draw.ellipse([(212, 535), (228, 551)], fill="#64748b")
    draw.rectangle([(250, 525), (1000, 640)], fill="#ffffff", outline="#cbd5e1")
    draw.text((270, 540), "Versión 1 (Creación inicial)", fill="#0f172a")
    draw.text((800, 540), "15/11/2026 • Autor: Carlos Morales", fill="#64748b")
    draw.rectangle([(270, 565), (980, 598)], fill="#f8fafc", outline="#e2e8f0")
    draw.text((280, 574), "Motivo obligatorio: 'Borrador base inicial de política de seguridad conforme al estándar ISO 27001'", fill="#1e293b")
    draw.text((270, 610), "Tamaño: 2.1 KB  •  SHA-256: 19bb045f8a02...", fill="#475569")
    draw.rectangle([(750, 605), (860, 630)], fill="#f1f5f9", outline="#94a3b8")
    draw.text((760, 610), "🔄 Restaurar", fill="#0f172a")
    draw.rectangle([(875, 605), (980, 630)], fill="#f1f5f9", outline="#94a3b8")
    draw.text((885, 610), "⬇️ Descargar", fill="#0f172a")

    img.save(SCREENSHOTS_DIR / "03_file_detail_timeline.png")

# 4. Screen: Version Diff
def gen_screen_diff():
    img, draw = create_base_canvas(title="DocuControl - Visor de Diferencias (Diff)")
    render_topbar(draw, 1200, "Carlos Morales", "Editor")

    # Modal
    draw.rectangle([(120, 80), (1080, 710)], fill="#ffffff", outline="#94a3b8")
    draw.rectangle([(120, 80), (1080, 140)], fill="#0f172a")
    draw.text((150, 95), "🔍 Comparador de Versiones: Politica_Seguridad_Informacion.txt", fill="#ffffff")
    draw.text((150, 116), "Comparando: Versión 1 (Base) vs. Versión 2 (Modificada)", fill="#94a3b8")

    # Metadata side-by-side
    draw.rectangle([(150, 155), (590, 280)], fill="#f8fafc", outline="#e2e8f0")
    draw.text((170, 168), "VERSIÓN 1 (BASE)", fill="#64748b")
    draw.text((170, 192), "Autor: Carlos Morales  |  Fecha: 15/11/2026", fill="#0f172a")
    draw.text((170, 212), "Tamaño: 2,150 bytes  |  Líneas: 14", fill="#0f172a")
    draw.text((170, 232), "Motivo: 'Borrador base inicial'", fill="#475569")
    draw.text((170, 252), "Hash: 19bb045f8a02a4e...", fill="#94a3b8")

    draw.rectangle([(610, 155), (1050, 280)], fill="#eff6ff", outline="#93c5fd")
    draw.text((630, 168), "VERSIÓN 2 (REVISADA)", fill="#1e40af")
    draw.text((630, 192), "Autor: Carlos Morales  |  Fecha: 16/11/2026", fill="#0f172a")
    draw.text((630, 212), "Tamaño: 2,820 bytes (+670 B)  |  Líneas: 20", fill="#0f172a")
    draw.text((630, 232), "Motivo: 'Inclusión de normas sobre contraseñas'", fill="#475569")
    draw.text((630, 252), "Hash: 3c72b1aa5409e81...", fill="#94a3b8")

    # Code Diff Viewer
    draw.rectangle([(150, 300), (1050, 680)], fill="#0f172a", outline="#334155")
    draw.rectangle([(150, 300), (1050, 335)], fill="#1e293b")
    draw.text((170, 310), "DIFF LÍNEA POR LÍNEA EN TEXTO PLANO", fill="#94a3b8")

    diff_lines = [
        ("--- Versión 1.0", "#94a3b8"),
        ("+++ Versión 2.0", "#94a3b8"),
        ("@@ -1,5 +1,9 @@", "#38bdf8"),
        (" POLÍTICA DE SEGURIDAD DE LA INFORMACIÓN CORPORATIVA", "#cbd5e1"),
        (" 1. Todos los usuarios deben proteger sus credenciales de acceso.", "#cbd5e1"),
        ("-2. Las claves deben cambiarse periódicamente.", "#f87171"),
        ("+2. Las claves deben cambiarse obligatoriamente cada 90 días naturales.", "#4ade80"),
        ("+3. Longitud mínima de contraseña: 12 caracteres alfanuméricos.", "#4ade80"),
        ("+4. Queda prohibida la compartición de cuentas entre compañeros.", "#4ade80"),
        (" 5. El uso de carpetas compartidas sin control de versiones queda suspendido.", "#cbd5e1"),
        ("+6. Todo documento en edición debe bloquearse previamente.", "#4ade80"),
    ]
    y = 350
    for line, color in diff_lines:
        if line.startswith("+"):
            draw.rectangle([(152, y - 2), (1048, y + 20)], fill="#064e3b")
        elif line.startswith("-"):
            draw.rectangle([(152, y - 2), (1048, y + 20)], fill="#7f1d1d")
        draw.text((170, y), line, fill=color)
        y += 28

    img.save(SCREENSHOTS_DIR / "04_version_diff.png")

# 5. Screen: Admin Panel
def gen_screen_admin():
    img, draw = create_base_canvas(title="DocuControl - Panel de Administración y Seguridad")
    render_topbar(draw, 1200, "Administrador del Sistema", "Administrador")
    render_sidebar(draw, "Admin")

    # Content
    draw.rectangle([(240, 102), (1200, 155)], fill="#ffffff", outline="#e2e8f0")
    draw.text((260, 120), "Panel de Administración del Sistema", fill="#1e1b4b")

    # Tabs
    tabs = ["👥 Usuarios y Roles (4)", "📋 Bitácora de Auditoría", "💾 Respaldos y Recuperación"]
    x = 260
    for t in tabs:
        if "Usuarios" in t:
            draw.rectangle([(x, 155), (x + 180, 190)], fill="#f3e8ff", outline="#9333ea")
            draw.text((x + 15, 168), t, fill="#7e22ce")
        else:
            draw.rectangle([(x, 155), (x + 180, 190)], fill="#ffffff", outline="#e2e8f0")
            draw.text((x + 15, 168), t, fill="#475569")
        x += 195

    # Users Table
    draw.rectangle([(260, 210), (1170, 245)], fill="#f8fafc")
    draw.text((280, 222), "USUARIO", fill="#64748b")
    draw.text((450, 222), "NOMBRE COMPLETO", fill="#64748b")
    draw.text((680, 222), "CORREO CORPORATIVO", fill="#64748b")
    draw.text((900, 222), "ROL ASIGNADO", fill="#64748b")
    draw.text((1060, 222), "ESTADO", fill="#64748b")

    users = [
        ("admin", "Administrador del Sistema", "admin@empresa.local", "Administrador", "#7e22ce", "#f3e8ff"),
        ("carlos.editor", "Carlos Morales", "carlos@empresa.local", "Editor", "#1d4ed8", "#dbeafe"),
        ("elena.revisora", "Elena Rivas", "elena@empresa.local", "Revisor", "#047857", "#d1fae5"),
        ("mario.lector", "Mario Santos", "mario@empresa.local", "Lector", "#475569", "#f1f5f9"),
    ]
    y = 255
    for uname, fname, email, rname, rcol, rbg in users:
        draw.rectangle([(260, y), (1170, y + 50)], fill="#ffffff", outline="#e2e8f0")
        draw.text((280, y + 16), uname, fill="#0f172a")
        draw.text((450, y + 16), fname, fill="#0f172a")
        draw.text((680, y + 16), email, fill="#475569")
        
        draw.rectangle([(900, y + 10), (1000, y + 36)], fill=rbg)
        draw.text((910, y + 15), rname, fill=rcol)

        draw.text((1060, y + 16), "🟢 Activo", fill="#16a34a")
        y += 60

    # Audit snippet below
    draw.rectangle([(260, 520), (1170, 720)], fill="#ffffff", outline="#e2e8f0")
    draw.rectangle([(260, 520), (1170, 555)], fill="#f1f5f9")
    draw.text((280, 532), "ÚLTIMOS EVENTOS EN LA BITÁCORA DE AUDITORÍA (SOLO-INSERCIÓN)", fill="#1e293b")

    events = [
        ("17:25:59", "admin", "CREAR_RESPALDO", "dms_backup_20261125.zip", "Respaldo integral DB + Almacén generado"),
        ("17:20:12", "carlos.editor", "BLOQUEAR_ARCHIVO", "Presupuesto_2026.xlsx", "Bloqueo preventivo de edición exclusiva"),
        ("16:45:00", "carlos.editor", "NUEVA_VERSION", "Politica_Seguridad.txt", "Versión 2 subida. SHA-256 verificado"),
        ("15:30:10", "admin", "LOGIN_EXITOSO", "admin", "Inicio de sesión seguro con IP 127.0.0.1"),
    ]
    ey = 565
    for time_str, user_str, act_str, obj_str, det_str in events:
        draw.text((280, ey), f"{time_str} | {user_str} | {act_str} | {obj_str} - {det_str}", fill="#475569")
        ey += 32

    img.save(SCREENSHOTS_DIR / "07_admin_panel.png")

# 6. Screen: Backup & Restore
def gen_screen_backup():
    img, draw = create_base_canvas(title="DocuControl - Módulo de Respaldos y Restauración")
    render_topbar(draw, 1200, "Administrador del Sistema", "Administrador")
    render_sidebar(draw, "Admin")

    draw.rectangle([(240, 102), (1200, 155)], fill="#ffffff", outline="#e2e8f0")
    draw.text((260, 120), "Gestión de Respaldos y Recuperación ante Desastres (RF-21)", fill="#1e1b4b")

    # Card 1: Create Backup
    draw.rectangle([(260, 175), (700, 360)], fill="#ffffff", outline="#cbd5e1")
    draw.rectangle([(260, 175), (700, 220)], fill="#eff6ff")
    draw.text((280, 190), "📦 Generación de Respaldo Integral", fill="#1e40af")
    draw.text((280, 240), "Copia atómica de la base de datos relacional (SQLite WAL) sincronizada", fill="#334155")
    draw.text((280, 260), "con todos los binarios deduplicados por SHA-256 en formato .zip", fill="#334155")
    draw.rectangle([(280, 295), (500, 335)], fill="#2563eb")
    draw.text((310, 307), "Generar Respaldo Ahora", fill="#ffffff")

    # Card 2: Restore
    draw.rectangle([(725, 175), (1170, 360)], fill="#ffffff", outline="#cbd5e1")
    draw.rectangle([(725, 175), (1170, 220)], fill="#fef2f2")
    draw.text((745, 190), "⚠️ Restauración del Sistema", fill="#991b1b")
    draw.text((745, 240), "Restaura la plataforma a partir de un paquete .zip de respaldo.", fill="#334155")
    draw.text((745, 260), "Garantiza la integridad histórica de versiones sin pérdida de datos.", fill="#334155")
    draw.rectangle([(745, 295), (965, 335)], fill="#dc2626")
    draw.text((775, 307), "Restaurar desde Respaldo", fill="#ffffff")

    # History Table
    draw.rectangle([(260, 390), (1170, 710)], fill="#ffffff", outline="#e2e8f0")
    draw.rectangle([(260, 390), (1170, 425)], fill="#f8fafc")
    draw.text((280, 402), "HISTORIAL DE RESPALDOS DISPONIBLES EN SERVIDOR", fill="#64748b")

    backups = [
        ("dms_backup_20261125_172559.zip", "Hoy 17:25", "7.8 KB", "Exitoso (SHA-256 Verificado)"),
        ("dms_backup_20261124_030000.zip", "Ayer 03:00", "7.2 KB", "Exitoso (Automático diario)"),
        ("dms_backup_20261123_030000.zip", "23/11/2026", "6.9 KB", "Exitoso (Automático diario)"),
    ]
    by = 445
    for bname, bdate, bsize, bstatus in backups:
        draw.rectangle([(280, by), (1150, by + 60)], fill="#f8fafc", outline="#e2e8f0")
        draw.text((300, by + 20), f"📦 {bname}", fill="#0f172a")
        draw.text((650, by + 20), bdate, fill="#475569")
        draw.text((800, by + 20), bsize, fill="#475569")
        draw.text((900, by + 20), f"🟢 {bstatus}", fill="#16a34a")
        draw.rectangle([(1060, by + 12), (1130, by + 46)], fill="#0f172a")
        draw.text((1070, by + 20), "Descargar", fill="#ffffff")
        by += 75

    img.save(SCREENSHOTS_DIR / "08_backup_restore.png")

if __name__ == "__main__":
    gen_screen_login()
    gen_screen_explorer()
    gen_screen_timeline()
    gen_screen_diff()
    gen_screen_admin()
    gen_screen_backup()
    print("All UI screenshots generated successfully in", SCREENSHOTS_DIR)
