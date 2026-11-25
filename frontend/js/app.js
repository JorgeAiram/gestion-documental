// Main Controller Application
const DocuApp = {
    currentFolderId: null,
    currentView: 'all', // 'all', 'recent', 'locked', 'trash'
    folders: [],

    async init() {
        // Check session or auto-login with admin for demo
        if (!window.Api.getToken()) {
            await this.quickLogin('admin');
        } else {
            this.updateAuthUI();
        }

        window.Explorer.init();
        this.setupEventListeners();
        await this.loadInitialData();

        // Polling for notifications every 10 seconds
        setInterval(() => this.pollNotifications(), 10000);
    },

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('nav-btn-all').onclick = () => this.setView('all');
        document.getElementById('nav-btn-recent').onclick = () => this.setView('recent');
        document.getElementById('nav-btn-locked').onclick = () => this.setView('locked');
        document.getElementById('nav-btn-trash').onclick = () => this.setView('trash');
        document.getElementById('nav-btn-admin').onclick = () => window.Admin.open();

        // Top Search input
        const searchInput = document.getElementById('global-search-input');
        let searchTimeout;
        searchInput.oninput = (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.searchFiles(e.target.value), 300);
        };

        // Refresh
        document.getElementById('btn-refresh').onclick = () => this.refreshCurrentView();

        // New upload button
        document.getElementById('btn-main-upload').onclick = () => this.openUploadModal();

        // Create folder button
        document.getElementById('btn-create-folder').onclick = () => this.openModal('modal-folder');

        // Form submits
        document.getElementById('form-login').onsubmit = (e) => this.handleLogin(e);
        document.getElementById('form-upload').onsubmit = (e) => this.handleUpload(e);
        document.getElementById('form-create-folder').onsubmit = (e) => this.handleCreateFolder(e);
        document.getElementById('form-add-comment').onsubmit = (e) => this.handleAddComment(e);

        // Notifications dropdown toggle
        document.getElementById('btn-notifications').onclick = (e) => {
            e.stopPropagation();
            const dd = document.getElementById('notif-dropdown');
            dd.classList.toggle('hidden');
        };

        document.addEventListener('click', (e) => {
            const wrapper = document.getElementById('notifications-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                document.getElementById('notif-dropdown').classList.add('hidden');
            }
        });

        document.getElementById('btn-mark-all-read').onclick = async () => {
            await window.Api.put('/notifications/read-all', {});
            await this.pollNotifications();
        };

        // Auth logout button
        document.getElementById('btn-auth-action').onclick = () => this.logout();

        // Admin backup buttons
        document.getElementById('btn-trigger-backup').onclick = () => window.Admin.triggerBackup();
        document.getElementById('btn-trigger-restore').onclick = () => {
            const input = document.getElementById('restore-backup-file');
            if (input.files && input.files[0]) {
                window.Admin.triggerRestore(input.files[0]);
            } else {
                this.showToast('Por favor selecciona un archivo .zip de respaldo', 'error');
            }
        };

        // Share copy link
        document.getElementById('btn-copy-share').onclick = () => {
            const input = document.getElementById('share-link-input');
            input.select();
            document.execCommand('copy');
            this.showToast('Enlace copiado al portapapeles', 'success');
        };

        // Close modal on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                ['modal-login', 'modal-upload', 'modal-folder', 'modal-file-detail', 'modal-diff', 'modal-preview', 'modal-share', 'modal-admin'].forEach(id => {
                    this.closeModal(id);
                });
            }
        });
    },

    async quickLogin(username) {
        const passwords = {
            'admin': 'admin123',
            'carlos.editor': 'editor123',
            'elena.revisora': 'revisora123',
            'mario.lector': 'lector123'
        };
        try {
            const res = await window.Api.post('/auth/login', {
                username: username,
                password: passwords[username] || 'admin123'
            });
            window.Api.setToken(res.access_token);
            window.Api.setUser(res.user);
            this.updateAuthUI();
            this.showToast(`Sesión iniciada como: ${res.user.full_name} (${res.user.role})`, 'success');
            await this.loadInitialData();
            this.closeModal('modal-login');
        } catch (e) {
            console.error('Quick login failed', e);
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errBox = document.getElementById('login-error-msg');
        errBox.classList.add('hidden');

        try {
            const res = await window.Api.post('/auth/login', { username, password });
            window.Api.setToken(res.access_token);
            window.Api.setUser(res.user);
            this.updateAuthUI();
            this.showToast(`Bienvenido, ${res.user.full_name}`, 'success');
            this.closeModal('modal-login');
            await this.loadInitialData();
        } catch (error) {
            errBox.textContent = error.message;
            errBox.classList.remove('hidden');
        }
    },

    logout() {
        window.Api.removeToken();
        this.updateAuthUI();
        this.showToast('Sesión cerrada correctamente', 'info');
        this.openModal('modal-login');
    },

    updateAuthUI() {
        const user = window.Api.getUser();
        const nameEl = document.getElementById('user-display-name');
        const roleEl = document.getElementById('user-display-role');
        const adminBtn = document.getElementById('nav-btn-admin');

        if (user) {
            nameEl.textContent = user.full_name;
            roleEl.textContent = user.role;
            if (user.role === 'Administrador') {
                adminBtn.classList.remove('hidden');
            } else {
                adminBtn.classList.add('hidden');
            }
        } else {
            nameEl.textContent = 'Invitado';
            roleEl.textContent = 'Sin sesión';
            adminBtn.classList.add('hidden');
        }
    },

    async loadInitialData() {
        await this.loadFolders();
        await this.refreshCurrentView();
        await this.pollNotifications();
    },

    async loadFolders() {
        try {
            const folders = await window.Api.get('/folders');
            this.folders = folders;
            this.renderFoldersTree();
            this.populateFolderSelects();
        } catch (e) {}
    },

    renderFoldersTree() {
        const container = document.getElementById('folders-tree-list');
        if (!this.folders || this.folders.length === 0) {
            container.innerHTML = '<p class="text-xs text-slate-400 py-2">No hay carpetas creadas</p>';
            return;
        }

        let html = '';
        this.folders.forEach(f => {
            const isSelected = this.currentFolderId === f.id;
            html += `
                <button onclick="window.DocuApp.navigateToFolder(${f.id})" 
                        class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium ${isSelected ? 'bg-blue-100 text-blue-900 font-bold' : 'text-slate-700 hover:bg-slate-100'} transition">
                    <div class="flex items-center gap-2 truncate">
                        <i class="fa-solid fa-folder ${isSelected ? 'text-blue-600' : 'text-amber-400'}"></i>
                        <span class="truncate">${f.name}</span>
                    </div>
                    <span class="text-[10px] text-slate-400 font-mono">(${f.file_count || 0})</span>
                </button>
            `;
        });
        container.innerHTML = html;
    },

    populateFolderSelects() {
        const selects = [document.getElementById('upload-folder-select'), document.getElementById('new-folder-parent')];
        selects.forEach(sel => {
            if (!sel) return;
            const currentVal = sel.value;
            sel.innerHTML = '<option value="">(Directorio Raíz / Principal)</option>';
            this.folders.forEach(f => {
                sel.innerHTML += `<option value="${f.id}">${f.name}</option>`;
            });
            if (currentVal) sel.value = currentVal;
        });
    },

    async setView(view) {
        this.currentView = view;
        this.currentFolderId = null;
        document.getElementById('global-search-input').value = '';

        // Update active sidebar styling
        ['all', 'recent', 'locked', 'trash'].forEach(v => {
            const btn = document.getElementById(`nav-btn-${v}`);
            if (btn) {
                if (v === view) {
                    btn.className = 'w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 transition';
                } else {
                    btn.className = 'w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition';
                }
            }
        });

        await this.refreshCurrentView();
    },

    navigateToFolder(folderId) {
        this.currentFolderId = folderId;
        this.currentView = 'folder';
        this.refreshCurrentView();
        this.renderFoldersTree();
    },

    async refreshCurrentView() {
        const breadcrumbTitle = document.getElementById('current-folder-title');
        let files = [];

        try {
            if (this.currentView === 'trash') {
                breadcrumbTitle.textContent = 'Papelera de Reciclaje';
                files = await window.Api.get('/files/trash/list');
                // Render trash items in explorer
                window.Explorer.setFiles(files);
                return;
            }

            if (this.currentFolderId) {
                const folder = this.folders.find(f => f.id === this.currentFolderId);
                breadcrumbTitle.textContent = folder ? folder.name : 'Carpeta';
                files = await window.Api.get(`/files?folder_id=${this.currentFolderId}`);
            } else if (this.currentView === 'recent') {
                breadcrumbTitle.textContent = 'Modificados Recientemente';
                files = await window.Api.get('/files');
            } else if (this.currentView === 'locked') {
                breadcrumbTitle.textContent = 'Archivos Bloqueados en Edición';
                const all = await window.Api.get('/files');
                files = all.filter(f => f.is_locked);
            } else {
                breadcrumbTitle.textContent = 'Todos los Documentos';
                files = await window.Api.get('/files');
            }

            // Update stats
            document.getElementById('total-files-count').textContent = files.length;
            const lockedCount = files.filter(f => f.is_locked).length;
            document.getElementById('locked-files-count').textContent = lockedCount;

            window.Explorer.setFiles(files);
        } catch (e) {
            console.error('Error refreshing view:', e);
        }
    },

    async searchFiles(query) {
        if (!query || query.trim() === '') {
            return this.refreshCurrentView();
        }
        try {
            const files = await window.Api.get(`/files?search=${encodeURIComponent(query.trim())}`);
            document.getElementById('current-folder-title').textContent = `Resultados de búsqueda: "${query}"`;
            window.Explorer.setFiles(files);
        } catch (e) {}
    },

    openUploadModal(preselectedFolderId = null) {
        const user = window.Api.getUser();
        if (user && user.role === 'Lector') {
            this.showToast('Los usuarios con rol Lector tienen acceso de solo lectura', 'error');
            return;
        }
        document.getElementById('modal-upload-title').textContent = 'Subir Documento';
        document.getElementById('form-upload').reset();
        if (preselectedFolderId || this.currentFolderId) {
            document.getElementById('upload-folder-select').value = preselectedFolderId || this.currentFolderId;
        }
        this.openModal('modal-upload');
    },

    prepareNewVersionUpload(file) {
        const user = window.Api.getUser();
        if (user && user.role === 'Lector') {
            this.showToast('Los usuarios Lectores no pueden subir versiones', 'error');
            return;
        }
        document.getElementById('modal-upload-title').textContent = `Subir Nueva Versión de: ${file.name}`;
        document.getElementById('form-upload').reset();
        document.getElementById('upload-folder-select').value = file.folder_id || '';
        document.getElementById('upload-comment-input').placeholder = `Describe las mejoras o cambios con respecto a la versión v${file.version_number || 1}...`;
        this.closeModal('modal-file-detail');
        this.openModal('modal-upload');
    },

    async handleUpload(e) {
        e.preventDefault();
        const fileInput = document.getElementById('upload-file-input');
        if (!fileInput.files || fileInput.files.length === 0) {
            this.showToast('Por favor selecciona un archivo', 'error');
            return;
        }

        const file = fileInput.files[0];
        const folderId = document.getElementById('upload-folder-select').value;
        const comment = document.getElementById('upload-comment-input').value.trim();
        const category = document.getElementById('upload-category-input').value;
        const tags = document.getElementById('upload-tags-input').value;

        const formData = new FormData();
        formData.append('file', file);
        if (folderId) formData.append('folder_id', folderId);
        formData.append('comment', comment);
        formData.append('category', category);
        formData.append('tags', tags);

        const progressBar = document.getElementById('upload-progress-bar');
        progressBar.classList.remove('hidden');

        try {
            const res = await window.Api.upload('/files/upload', formData);
            progressBar.classList.add('hidden');
            this.showToast(res.message, 'success');
            this.closeModal('modal-upload');
            await this.refreshCurrentView();
            await this.loadFolders();
        } catch (e) {
            progressBar.classList.add('hidden');
        }
    },

    async handleCreateFolder(e) {
        e.preventDefault();
        const name = document.getElementById('new-folder-name').value.trim();
        const parentId = document.getElementById('new-folder-parent').value;
        try {
            await window.Api.post('/folders', {
                name: name,
                parent_id: parentId ? parseInt(parentId) : null
            });
            this.showToast(`Carpeta '${name}' creada exitosamente`, 'success');
            this.closeModal('modal-folder');
            document.getElementById('form-create-folder').reset();
            await this.loadFolders();
        } catch (e) {}
    },

    openFileDetail(fileId) {
        window.FileDetail.open(fileId);
    },

    switchAdminTab(tab) {
        window.Admin.switchTab(tab);
    },

    loadAuditLog() {
        window.Admin.loadAudit();
    },

    showNewUserForm() {
        const username = prompt("Nombre de usuario (ej: nuevo.editor):");
        if (!username) return;
        const fullName = prompt("Nombre completo:");
        const email = prompt("Correo electrónico:");
        const role = prompt("Rol (Administrador, Editor, Revisor, Lector):", "Editor");
        const password = prompt("Contraseña inicial:", "temporal123");
        
        window.Api.post('/users', {
            username: username.trim(),
            full_name: fullName.trim(),
            email: email.trim(),
            role: role.trim(),
            password: password
        }).then(() => {
            this.showToast("Usuario registrado exitosamente", "success");
            window.Admin.loadUsers();
        }).catch(err => {
            this.showToast(err.message, "error");
        });
    },

    switchFileTab(tab) {
        const vBtn = document.getElementById('tab-btn-versions');
        const cBtn = document.getElementById('tab-btn-comments');
        const vContent = document.getElementById('tab-content-versions');
        const cContent = document.getElementById('tab-content-comments');

        if (tab === 'versions') {
            vBtn.className = 'py-3 px-4 text-xs font-bold border-b-2 border-blue-600 text-blue-600 flex items-center gap-2';
            cBtn.className = 'py-3 px-4 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2';
            vContent.classList.remove('hidden');
            cContent.classList.add('hidden');
        } else {
            cBtn.className = 'py-3 px-4 text-xs font-bold border-b-2 border-blue-600 text-blue-600 flex items-center gap-2';
            vBtn.className = 'py-3 px-4 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-2';
            cContent.classList.remove('hidden');
            vContent.classList.add('hidden');
        }
    },

    async handleAddComment(e) {
        e.preventDefault();
        const input = document.getElementById('comment-text-input');
        const text = input.value.trim();
        if (!text) return;

        const fileId = window.FileDetail.currentFile.id;
        try {
            await window.Api.post(`/comments/file/${fileId}`, { text });
            input.value = '';
            this.showToast('Comentario publicado', 'success');
            await window.FileDetail.loadComments();
        } catch (e) {}
    },

    downloadFile(fileId) {
        window.location.href = `/api/v1/files/${fileId}/download`;
    },

    downloadSpecificVersion(versionId, filename, versionNumber) {
        window.location.href = `/api/v1/versions/${versionId}/download`;
    },

    async restoreVersion(versionId, versionNumber) {
        if (!confirm(`¿Restaurar la versión v${versionNumber}? Esto creará una versión consecutiva nueva preservando el historial completo.`)) {
            return;
        }
        try {
            const res = await window.Api.post(`/versions/${versionId}/restore`, {});
            this.showToast(res.message, 'success');
            await window.FileDetail.open(window.FileDetail.currentFile.id);
            await this.refreshCurrentView();
        } catch (e) {}
    },

    compareWithPrevious(versionAId, versionBId) {
        window.VersionDiff.compare(versionBId, versionAId);
    },

    previewFile(fileId, filename, extension) {
        window.Preview.open(fileId, filename, extension);
    },

    async openShareModal(fileId) {
        this.openModal('modal-share');
        document.getElementById('share-result-container').classList.add('hidden');
        document.getElementById('btn-generate-share-link').onclick = async () => {
            const hours = parseInt(document.getElementById('share-expiry-hours').value);
            try {
                const res = await window.Api.post('/shares', { file_id: fileId, expires_in_hours: hours });
                const fullUrl = `${window.location.origin}/api/v1/shares/public/${res.token}/download`;
                document.getElementById('share-link-input').value = fullUrl;
                document.getElementById('share-expires-label').textContent = `Vence el: ${new Date(res.expires_at).toLocaleString('es-MX')}`;
                document.getElementById('share-result-container').classList.remove('hidden');
            } catch (e) {}
        };
    },

    async pollNotifications() {
        const user = window.Api.getUser();
        if (!user) return;
        try {
            const res = await window.Api.get('/notifications');
            const badge = document.getElementById('notif-badge');
            if (res.unread_count > 0) {
                badge.textContent = res.unread_count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }

            const list = document.getElementById('notif-list');
            if (res.notifications.length === 0) {
                list.innerHTML = '<p class="p-4 text-xs text-slate-400 text-center">No hay notificaciones</p>';
                return;
            }

            let html = '';
            res.notifications.forEach(n => {
                const dateStr = new Date(n.created_at).toLocaleString('es-MX', { timeStyle: 'short', dateStyle: 'short' });
                html += `
                    <div class="p-3 hover:bg-slate-50 transition text-xs ${n.is_read ? 'opacity-70' : 'bg-blue-50/40'}">
                        <div class="flex items-center justify-between font-bold text-slate-800">
                            <span>${n.title}</span>
                            <span class="text-[10px] text-slate-400 font-normal">${dateStr}</span>
                        </div>
                        <p class="text-slate-600 mt-1">${n.message}</p>
                    </div>
                `;
            });
            list.innerHTML = html;
        } catch (e) {}
    },

    openModal(id) {
        const m = document.getElementById(id);
        if (m) m.classList.remove('hidden');
    },

    closeModal(id) {
        const m = document.getElementById(id);
        if (m) m.classList.add('hidden');
    },

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const msgEl = document.getElementById('toast-message');
        const icon = document.getElementById('toast-icon');

        msgEl.textContent = message;
        if (type === 'error') {
            toast.className = 'fixed bottom-5 right-5 max-w-sm bg-red-900 text-white text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-0 opacity-100 transition-all duration-300 z-50';
            icon.className = 'fa-solid fa-triangle-exclamation text-red-300 text-base';
        } else if (type === 'info') {
            toast.className = 'fixed bottom-5 right-5 max-w-sm bg-blue-900 text-white text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-0 opacity-100 transition-all duration-300 z-50';
            icon.className = 'fa-solid fa-circle-info text-blue-300 text-base';
        } else {
            toast.className = 'fixed bottom-5 right-5 max-w-sm bg-slate-900 text-white text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-0 opacity-100 transition-all duration-300 z-50';
            icon.className = 'fa-solid fa-circle-check text-emerald-400 text-base';
        }

        setTimeout(() => {
            toast.className = 'fixed bottom-5 right-5 max-w-sm bg-slate-900 text-white text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 transform translate-y-20 opacity-0 transition-all duration-300 z-50';
        }, 3500);
    }
};

window.DocuApp = DocuApp;

// Auto-run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    DocuApp.init();
});
