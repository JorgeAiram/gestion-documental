import sqlite3
import datetime
import hashlib
import json
from pathlib import Path
from backend.config import DB_PATH, STORAGE_DIR

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def hash_password(password: str) -> str:
    salt = "s@lt_dms_2026_"
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Administrador', 'Editor', 'Revisor', 'Lector')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    ''')

    # 2. Folders
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        owner_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE,
        FOREIGN KEY (owner_id) REFERENCES users(id)
    );
    ''')

    # 3. Files
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER,
        name TEXT NOT NULL,
        extension TEXT NOT NULL,
        current_version_id INTEGER,
        is_locked INTEGER NOT NULL DEFAULT 0,
        locked_by_user_id INTEGER,
        locked_at TEXT,
        is_in_trash INTEGER NOT NULL DEFAULT 0,
        trashed_at TEXT,
        tags TEXT DEFAULT '',
        category TEXT DEFAULT 'General',
        created_by_user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL,
        FOREIGN KEY (locked_by_user_id) REFERENCES users(id),
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    );
    ''')

    # 4. Versions (Immutable)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        comment TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        content_text TEXT,
        review_status TEXT DEFAULT 'Sin revisión' CHECK(review_status IN ('Sin revisión', 'Pendiente', 'Revisado', 'Con observaciones')),
        reviewed_by_user_id INTEGER,
        reviewed_at TEXT,
        review_notes TEXT,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id),
        FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id)
    );
    ''')

    # 5. Permissions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER NOT NULL,
        user_id INTEGER,
        role TEXT,
        access_level TEXT NOT NULL CHECK(access_level IN ('Lectura', 'Edicion', 'Administracion')),
        created_at TEXT NOT NULL,
        FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # 6. Comments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        version_id INTEGER,
        author_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id)
    );
    ''')

    # 7. Notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER NOT NULL,
        sender_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        link TEXT,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users(id)
    );
    ''')

    # 8. Audit Log (Insert-only)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER,
        target_name TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TEXT NOT NULL
    );
    ''')

    # 9. Shared Links (Public with expiration)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shared_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_by_user_id INTEGER NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        access_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    );
    ''')

    # Seed Default Data if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().isoformat()
        
        # 1. Default Users
        users_to_seed = [
            ("admin", "admin@empresa.local", "Administrador del Sistema", hash_password("admin123"), "Administrador"),
            ("carlos.editor", "carlos@empresa.local", "Carlos Morales (Editor)", hash_password("editor123"), "Editor"),
            ("elena.revisora", "elena@empresa.local", "Elena Rivas (Revisora)", hash_password("revisora123"), "Revisor"),
            ("mario.lector", "mario@empresa.local", "Mario Santos (Lector)", hash_password("lector123"), "Lector")
        ]
        cursor.executemany('''
            INSERT INTO users (username, email, full_name, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [(u[0], u[1], u[2], u[3], u[4], now) for u in users_to_seed])
        
        # 2. Default Folders
        folders_to_seed = [
            ("01. Dirección General", None, 1),
            ("02. Finanzas y Presupuesto", None, 1),
            ("03. Recursos Humanos y Contratos", None, 1),
            ("04. Operaciones y Proyectos", None, 1),
            ("05. Políticas y Normatividad", None, 1),
            ("Presupuestos 2026", 2, 1),
            ("Manuales de Operación", 4, 1),
        ]
        for name, pid, oid in folders_to_seed:
            cursor.execute('''
                INSERT INTO folders (name, parent_id, owner_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (name, pid, oid, now))

        # 3. Default Folder Permissions
        # Finanzas: Editor can edit, Lector can read
        cursor.execute("INSERT INTO permissions (folder_id, role, access_level, created_at) VALUES (2, 'Editor', 'Edicion', ?)", (now,))
        cursor.execute("INSERT INTO permissions (folder_id, role, access_level, created_at) VALUES (2, 'Lector', 'Lectura', ?)", (now,))

        # 4. Seed initial documents with multiple versions to showcase version control
        # Doc 1: Politica_Seguridad_Informacion.txt in "05. Políticas y Normatividad" (folder 5)
        content_v1 = "POLÍTICA DE SEGURIDAD DE LA INFORMACIÓN V1.0\n1. Todos los usuarios deben proteger sus claves.\n2. No compartir archivos por medios no autorizados."
        content_v2 = "POLÍTICA DE SEGURIDAD DE LA INFORMACIÓN V2.0\n1. Todos los usuarios deben proteger sus claves y renovarlas cada 90 días.\n2. No compartir archivos por medios no autorizados.\n3. Bloquear archivos antes de editar para evitar sobrescritura accidental."
        
        def save_blob(text):
            data = text.encode('utf-8')
            sha = hashlib.sha256(data).hexdigest()
            target = STORAGE_DIR / sha
            with open(target, 'wb') as f:
                f.write(data)
            return sha, len(data), str(target)

        sha1, size1, path1 = save_blob(content_v1)
        sha2, size2, path2 = save_blob(content_v2)

        # Insert file
        cursor.execute('''
            INSERT INTO files (folder_id, name, extension, current_version_id, is_locked, locked_by_user_id, tags, category, created_by_user_id, created_at, updated_at)
            VALUES (5, 'Politica_Seguridad_Informacion.txt', 'txt', NULL, 0, NULL, 'seguridad, normativa, ti', 'Políticas', 1, ?, ?)
        ''', (now, now))
        file_id = cursor.lastrowid

        # Insert v1
        cursor.execute('''
            INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
            VALUES (?, 1, 1, ?, 'Versión inicial redactada y aprobada preliminarmente', ?, 'text/plain', ?, ?, ?, 'Revisado')
        ''', (file_id, now, size1, sha1, path1, content_v1))
        v1_id = cursor.lastrowid

        # Insert v2
        cursor.execute('''
            INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
            VALUES (?, 2, 2, ?, 'Actualización con reglas de bloqueo de archivos y vigencia de contraseñas', ?, 'text/plain', ?, ?, ?, 'Revisado')
        ''', (file_id, now, size2, sha2, path2, content_v2))
        v2_id = cursor.lastrowid

        # Update current version pointer
        cursor.execute("UPDATE files SET current_version_id = ? WHERE id = ?", (v2_id, file_id))

        # Add comment
        cursor.execute('''
            INSERT INTO comments (file_id, version_id, author_id, text, created_at)
            VALUES (?, ?, 3, 'Revisión técnica conforme al estándar ISO 27001 aprobada sin observaciones.', ?)
        ''', (file_id, v2_id, now))

        # Doc 2: Manual_Procedimientos_Operativos.txt in "Manuales de Operación" (folder 7)
        manual_content = "MANUAL DE PROCEDIMIENTOS OPERATIVOS\nDepartamento de Operaciones\nProcedimiento OP-01: Control de Versiones y Flujo Documental.\nFlujo continuo sin cuellos de botella."
        m_sha, m_size, m_path = save_blob(manual_content)
        cursor.execute('''
            INSERT INTO files (folder_id, name, extension, current_version_id, is_locked, locked_by_user_id, tags, category, created_by_user_id, created_at, updated_at)
            VALUES (7, 'Manual_Procedimientos_Operativos.txt', 'txt', NULL, 0, NULL, 'operaciones, manual, guia', 'Manuales', 2, ?, ?)
        ''', (now, now))
        m_file_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO versions (file_id, version_number, author_id, created_at, comment, file_size, mime_type, content_hash, storage_path, content_text, review_status)
            VALUES (?, 1, 2, ?, 'Publicación inicial del manual operativo', ?, 'text/plain', ?, ?, ?, 'Revisado')
        ''', (m_file_id, now, m_size, m_sha, m_path, manual_content))
        m_v1_id = cursor.lastrowid
        cursor.execute("UPDATE files SET current_version_id = ? WHERE id = ?", (m_v1_id, m_file_id))

        # Initial Audit Log entry
        cursor.execute('''
            INSERT INTO audit_log (user_id, username, action, target_type, target_id, target_name, details, ip_address, created_at)
            VALUES (1, 'admin', 'SISTEMA_INICIALIZADO', 'SISTEMA', 1, 'Plataforma Documental', 'Base de datos inicializada con usuarios y datos de demostración.', '127.0.0.1', ?)
        ''', (now,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
