# Plataforma Web de Gestión Documental con Control de Versiones (DocuControl v1.0)

Sistema corporativo desarrollado para sustituir de forma definitiva la carpeta compartida en red, garantizando el control inmutable de versiones, control preventivo de concurrencia mediante bloqueo de edición (Check-Out), roles de usuario, permisos por carpeta, bitácora de auditoría inmutable y respaldos automáticos y manuales con recuperación ante desastres.

---

## 🚀 Puesta en Marcha Rápida (1-Clic en Windows)

### Opción 1: Lanzador Directo
- Haga doble clic sobre **`run.bat`** o ejecute en PowerShell **`run.ps1`**.
- El script iniciará el servidor web en `http://127.0.0.1:8000` y abrirá la aplicación en su navegador automáticamente.

### Opción 2: Abrir en Visual Studio 2022
1. Haga doble clic en el archivo de solución **`GestionDocumental.sln`**.
2. Presione **F5** para iniciar la depuración y ejecución. El navegador se abrirá en `http://127.0.0.1:8000`.

### Opción 3: Abrir en Visual Studio Code
1. Abra la carpeta en VS Code (`File > Open Folder...`).
2. Presione **F5** (la configuración está lista en `.vscode/launch.json`).

---

## 👥 Credenciales de Acceso para Demostración

| Rol | Usuario | Contraseña | Descripción de Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` | Gestión de usuarios, auditoría, respaldos y permisos totales. |
| **Editor** | `carlos.editor` | `editor123` | Sube documentos, bloquea archivos, comenta y solicita revisiones. |
| **Revisor** | `elena.revisora` | `revisora123` | Marca revisiones con observaciones o aprobaciones sin trabar el flujo. |
| **Lector** | `mario.lector` | `lector123` | Solo consulta y descarga. Tiene restringida la subida y edición. |

> **Nota:** La pantalla de inicio de sesión incluye un selector rápido de perfiles para alternar entre roles con un solo clic.

---

## 📋 Requerimientos y Criterios de Aceptación Cubiertos (100%)

- **RF-01 a RF-11 (Fase 1 - Núcleo Indispensable):**
  - Autenticación JWT y expiración de sesiones.
  - Catálogo de usuarios y asignación de los 4 roles corporativos.
  - Subida, descarga, renombrado, movimiento y papelera de archivos (hasta 500 MB).
  - Árbol multinivel de carpetas empresariales.
  - Control inmutable de versiones con consecutivos automáticos (v1, v2, v3...).
  - Registro de autor, fecha, tamaño y **comentario obligatorio de cambio**.
  - Historial completo en línea de tiempo, descarga de versiones históricas y restauración como nueva versión vigente v(N+1).
  - Bloqueo de concurrencia exclusivo en edición con liberación automática al subir versión o forzada por el administrador.
  - Búsqueda por nombre, autor, extensión y fechas.
  - Papelera de reciclaje con restauración íntegra de versiones.
  - Bitácora inmutable de auditoría (solo-inserción) de cada acción relevante con IP y usuario.

- **RF-12 a RF-17 (Fase 2 - Colaboración):**
  - Matriz de permisos por carpeta (Lectura, Edición, Administración).
  - Comparador de versiones (Diff): metadatos lado a lado y visor de diferencias de texto plano.
  - Etiquetas, categorías y filtros rápidos.
  - Hilo de comentarios por archivo o versión con detección de menciones (`@usuario`).
  - Revisión opcional colaborativa (estados 'Revisado' o 'Con observaciones' sin burocracia).
  - Notificaciones en tiempo real en la plataforma.

- **RF-18 a RF-21 (Fase 3 - Complementos y Continuidad):**
  - Visor integrado de vista previa en navegador (PDF, imágenes, código y texto).
  - Búsqueda por contenido indexado.
  - Generación de enlaces temporales de consulta con fecha de vencimiento.
  - Centro de respaldos automáticos y manuales (base de datos + archivos binarios en ZIP) con restauración en caliente.

---

## 📄 Documentación Oficial en PDF

El documento oficial completo con portada ejecutiva, manual de usuario ilustrado, manual de administración, arquitectura y reporte de pruebas se encuentra en:
📁 **`docs/Documentacion_Plataforma_Gestion_Documental.pdf`**

---

## 🛠️ Estructura del Proyecto

```text
gestion-documental/
├── .vscode/                 # Configuraciones para Visual Studio Code (F5)
├── backend/
│   ├── routes/              # Endpoints API REST (/api/v1)
│   ├── tests/               # Suite automatizada de pruebas (RF-01 a RF-21)
│   ├── auth.py              # Seguridad, JWT y control de roles
│   ├── config.py            # Configuraciones y límites
│   ├── database.py          # Esquema relacional SQLite y semillas
│   ├── main.py              # Entrada FastAPI y montaje de frontend
│   └── storage.py           # Almacén binario deduplicado por SHA-256
├── data/
│   ├── backups/             # Paquetes ZIP de respaldo del sistema
│   ├── storage/             # Archivos binarios indexados por hash SHA-256
│   └── dms.db               # Base de datos relacional SQLite
├── docs/
│   ├── screenshots/         # Capturas de pantalla reales de la plataforma
│   ├── Documentacion_Plataforma_Gestion_Documental.pdf # PDF Oficial
│   └── generate_pdf.py      # Generador automatizado de la memoria técnica
├── frontend/
│   ├── css/style.css        # Estilos modernos y accesibles (WCAG 2.1 AA)
│   ├── js/                  # Módulos SPA (Explorer, FileDetail, Diff, Admin, Preview)
│   └── index.html           # Interfaz de usuario de una sola página
├── GestionDocumental.sln    # Solución oficial para Visual Studio 2022
├── GestionDocumental.pyproj # Proyecto de Python para Visual Studio
├── run.bat                  # Lanzador 1-clic para Windows (CMD)
├── run.ps1                  # Lanzador para PowerShell
└── requirements.txt         # Dependencias del proyecto
```
