// Administration Panel Component
const Admin = {
    activeTab: 'users',

    async open() {
        const user = window.Api.getUser();
        if (!user || user.role !== 'Administrador') {
            window.DocuApp.showToast('Acceso restringido a Administradores', 'error');
            return;
        }
        this.activeTab = 'users';
        this.updateTabUI();
        await this.loadUsers();
        window.DocuApp.openModal('modal-admin');
    },

    updateTabUI() {
        ['users', 'audit', 'backup'].forEach(tab => {
            const btn = document.getElementById(`admin-tab-${tab}`);
            const content = document.getElementById(`admin-content-${tab}`);
            if (tab === this.activeTab) {
                btn.className = 'py-3 px-3 text-xs font-bold border-b-2 border-purple-600 text-purple-700 flex items-center gap-1.5';
                content.classList.remove('hidden');
            } else {
                btn.className = 'py-3 px-3 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center gap-1.5';
                content.classList.add('hidden');
            }
        });
    },

    async switchTab(tab) {
        this.activeTab = tab;
        this.updateTabUI();
        if (tab === 'users') await this.loadUsers();
        if (tab === 'audit') await this.loadAudit();
        if (tab === 'backup') await this.loadBackups();
    },

    async loadUsers() {
        try {
            const users = await window.Api.get('/users');
            const tbody = document.getElementById('admin-users-tbody');
            let html = '';
            users.forEach(u => {
                const badgeColor = {
                    'Administrador': 'bg-purple-100 text-purple-800',
                    'Editor': 'bg-blue-100 text-blue-800',
                    'Revisor': 'bg-emerald-100 text-emerald-800',
                    'Lector': 'bg-slate-100 text-slate-800'
                }[u.role] || 'bg-slate-100 text-slate-700';

                html += `
                    <tr class="hover:bg-slate-50">
                        <td class="p-3 font-bold text-slate-800">${u.username}</td>
                        <td class="p-3">${u.full_name}</td>
                        <td class="p-3 text-slate-500">${u.email}</td>
                        <td class="p-3"><span class="px-2 py-0.5 rounded font-bold text-[10px] ${badgeColor}">${u.role}</span></td>
                        <td class="p-3">${u.is_active ? '<span class="text-emerald-600 font-bold">Activo</span>' : '<span class="text-red-500">Inactivo</span>'}</td>
                        <td class="p-3 text-right">
                            ${u.id !== 1 ? `
                                <button onclick="window.Admin.deactivateUser(${u.id}, '${u.username}')" class="text-xs text-red-600 hover:underline">
                                    Desactivar
                                </button>
                            ` : '<span class="text-[10px] text-slate-400">Principal</span>'}
                        </td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        } catch (e) {}
    },

    async deactivateUser(id, username) {
        if (!confirm(`¿Desactivar al usuario ${username}?`)) return;
        try {
            await window.Api.delete(`/users/${id}`);
            window.DocuApp.showToast(`Usuario ${username} desactivado`, 'success');
            await this.loadUsers();
        } catch (e) {}
    },

    async loadAudit() {
        try {
            const filter = document.getElementById('audit-filter-input').value;
            const url = filter ? `/audit?action=${encodeURIComponent(filter)}` : '/audit';
            const logs = await window.Api.get(url);
            const tbody = document.getElementById('admin-audit-tbody');
            let html = '';
            logs.forEach(l => {
                const dateStr = new Date(l.created_at).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });
                html += `
                    <tr class="hover:bg-slate-50 text-[11px]">
                        <td class="p-3 font-mono text-slate-500">${dateStr}</td>
                        <td class="p-3 font-bold text-slate-800">${l.username}</td>
                        <td class="p-3"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-800 font-mono font-bold">${l.action}</span></td>
                        <td class="p-3 text-slate-700">${l.target_name || '-'}</td>
                        <td class="p-3 text-slate-600 truncate max-w-xs" title="${l.details || ''}">${l.details || '-'}</td>
                        <td class="p-3 font-mono text-slate-400">${l.ip_address}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        } catch (e) {}
    },

    async loadBackups() {
        try {
            const backups = await window.Api.get('/backup/list');
            const container = document.getElementById('backups-list-container');
            if (!backups || backups.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">No hay respaldos previos.</p>';
                return;
            }
            let html = '';
            backups.forEach(b => {
                const dateStr = new Date(b.created_at).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
                html += `
                    <div class="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div class="flex items-center gap-2">
                            <i class="fa-solid fa-file-zipper text-blue-600 text-lg"></i>
                            <div>
                                <span class="font-bold text-slate-800 block">${b.filename}</span>
                                <span class="text-[11px] text-slate-400">${dateStr} • ${window.Explorer.formatBytes(b.size_bytes)}</span>
                            </div>
                        </div>
                        <a href="/api/v1/backup/download/${b.filename}" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-medium">
                            <i class="fa-solid fa-download mr-1"></i> Descargar
                        </a>
                    </div>
                `;
            });
            container.innerHTML = html;
        } catch (e) {}
    },

    async triggerBackup() {
        try {
            window.DocuApp.showToast('Generando respaldo completo de base de datos y almacén binario...', 'info');
            const res = await window.Api.post('/backup/create', {});
            window.DocuApp.showToast(`Respaldo generado con éxito: ${res.filename}`, 'success');
            await this.loadBackups();
        } catch (e) {}
    },

    async triggerRestore(file) {
        if (!confirm('ADVERTENCIA: La restauración sobrescribirá el estado actual de la base de datos y archivos con los del respaldo. ¿Deseas continuar?')) {
            return;
        }
        try {
            window.DocuApp.showToast('Restaurando sistema desde el archivo...', 'info');
            const formData = new FormData();
            formData.append('file', file);
            await window.Api.upload('/backup/restore', formData);
            window.DocuApp.showToast('Sistema restaurado exitosamente', 'success');
            location.reload();
        } catch (e) {}
    }
};

window.Admin = Admin;
