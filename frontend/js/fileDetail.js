// File Details, Version Timeline & Comments Module
const FileDetail = {
    currentFile: null,
    currentVersions: [],
    activeTab: 'versions',

    async open(fileId) {
        try {
            const file = await window.Api.get(`/files/${fileId}`);
            this.currentFile = file;
            this.activeTab = 'versions';
            this.renderHeader();
            await this.loadVersions();
            await this.loadComments();
            window.DocuApp.openModal('modal-file-detail');
        } catch (e) {
            console.error('Error opening file details:', e);
        }
    },

    renderHeader() {
        const f = this.currentFile;
        document.getElementById('modal-file-name').textContent = f.name;
        document.getElementById('modal-file-meta').textContent = 
            `Carpeta: ${f.folder_name || 'Raíz'} | Creado por: ${f.created_by_name || 'Desconocido'} | Formato: .${f.extension}`;

        const lockBtn = document.getElementById('btn-toggle-lock');
        const lockText = document.getElementById('btn-lock-text');

        if (f.is_locked) {
            lockBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white shadow-sm transition';
            lockText.textContent = `Liberar Bloqueo (${f.locked_by_name?.split(' ')[0] || 'En edición'})`;
            lockBtn.onclick = () => this.toggleLock(false);
        } else {
            lockBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 bg-amber-500 hover:bg-amber-600 text-white shadow-sm transition';
            lockText.textContent = 'Bloquear para edición';
            lockBtn.onclick = () => this.toggleLock(true);
        }

        // Action buttons
        document.getElementById('btn-modal-download').onclick = () => window.DocuApp.downloadFile(f.id);
        document.getElementById('btn-modal-preview').onclick = () => window.DocuApp.previewFile(f.id, f.name, f.extension);
        document.getElementById('btn-modal-share').onclick = () => window.DocuApp.openShareModal(f.id);
        document.getElementById('btn-modal-upload-version').onclick = () => {
            window.DocuApp.prepareNewVersionUpload(f);
        };
        document.getElementById('btn-modal-trash').onclick = () => this.moveToTrash();
    },

    async toggleLock(shouldLock) {
        try {
            const f = this.currentFile;
            if (shouldLock) {
                await window.Api.post(`/files/${f.id}/lock`, {});
                window.DocuApp.showToast('Archivo bloqueado exclusivamente para ti. Nadie más podrá sobrescribirlo.', 'success');
            } else {
                await window.Api.post(`/files/${f.id}/unlock`, {});
                window.DocuApp.showToast('Archivo liberado exitosamente.', 'success');
            }
            await this.open(f.id);
            window.DocuApp.refreshCurrentView();
        } catch (e) {
            // Handled in Api
        }
    },

    async moveToTrash() {
        if (!confirm(`¿Estás seguro de mover '${this.currentFile.name}' a la papelera? Su historial se conservará para posible restauración.`)) {
            return;
        }
        try {
            await window.Api.post(`/files/${this.currentFile.id}/trash`, {});
            window.DocuApp.showToast('Archivo movido a la papelera', 'success');
            window.DocuApp.closeModal('modal-file-detail');
            window.DocuApp.refreshCurrentView();
        } catch (e) {}
    },

    async loadVersions() {
        try {
            const versions = await window.Api.get(`/versions/file/${this.currentFile.id}`);
            this.currentVersions = versions;
            document.getElementById('file-version-count').textContent = versions.length;
            this.renderVersionTimeline();
        } catch (e) {}
    },

    renderVersionTimeline() {
        const container = document.getElementById('version-timeline-container');
        if (!this.currentVersions || this.currentVersions.length === 0) {
            container.innerHTML = '<p class="text-xs text-slate-400">No hay versiones registradas</p>';
            return;
        }

        let html = '';
        this.currentVersions.forEach((v, index) => {
            const isCurrent = v.is_current;
            const isLatest = index === 0;
            const dateStr = new Date(v.created_at).toLocaleString('es-MX', {
                dateStyle: 'medium',
                timeStyle: 'short'
            });

            // Review status pill
            let reviewBadge = '';
            if (v.review_status === 'Revisado') {
                reviewBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    <i class="fa-solid fa-check text-[9px]"></i> Revisado por ${v.reviewer_name?.split(' ')[0] || 'Revisor'}
                </span>`;
            } else if (v.review_status === 'Con observaciones') {
                reviewBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                    <i class="fa-solid fa-triangle-exclamation text-[9px]"></i> Con observaciones
                </span>`;
            } else if (v.review_status === 'Pendiente') {
                reviewBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                    <i class="fa-solid fa-hourglass-half text-[9px]"></i> Revisión solicitada
                </span>`;
            }

            html += `
                <div class="relative pl-6 pb-2">
                    <!-- Circle on line -->
                    <div class="absolute -left-4 top-1.5 w-4 h-4 rounded-full border-2 border-white shadow-sm flex items-center justify-center ${isCurrent ? 'bg-blue-600' : 'bg-slate-400'}">
                    </div>

                    <div class="bg-white rounded-xl p-4 border ${isCurrent ? 'border-blue-400 shadow-md ring-1 ring-blue-400/20' : 'border-slate-200 shadow-xs'} space-y-2">
                        <div class="flex items-center justify-between flex-wrap gap-2">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 text-xs font-bold rounded ${isCurrent ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700'}">
                                    Versión ${v.version_number}
                                </span>
                                ${isCurrent ? '<span class="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">Vigente</span>' : ''}
                                ${reviewBadge}
                            </div>
                            <span class="text-xs text-slate-400 font-mono">${dateStr}</span>
                        </div>

                        <!-- Mandatory change comment -->
                        <div class="bg-slate-50 border border-slate-100 rounded-lg p-2.5 text-xs text-slate-700">
                            <span class="font-bold text-slate-500 block text-[10px] uppercase mb-0.5">Motivo del cambio:</span>
                            <p class="italic text-slate-800 font-medium">"${v.comment}"</p>
                        </div>

                        <!-- Metadata info -->
                        <div class="flex items-center justify-between text-[11px] text-slate-500 flex-wrap gap-2 pt-1 border-t border-slate-100">
                            <div>
                                <i class="fa-solid fa-user text-slate-400 mr-1"></i> Autor: <strong class="text-slate-700">${v.author_name}</strong>
                                <span class="mx-2">•</span>
                                <i class="fa-solid fa-hard-drive text-slate-400 mr-1"></i> ${window.Explorer.formatBytes(v.file_size)}
                                <span class="mx-2">•</span>
                                <span class="font-mono text-[10px] text-slate-400" title="Hash SHA-256 de integridad">SHA: ${v.content_hash.substring(0, 10)}...</span>
                            </div>

                            <!-- Version action buttons -->
                            <div class="flex items-center gap-2">
                                <button onclick="window.DocuApp.downloadSpecificVersion(${v.id}, '${this.currentFile.name}', ${v.version_number})" 
                                        class="px-2 py-1 text-xs text-slate-700 hover:text-blue-600 bg-slate-100 hover:bg-slate-200 rounded font-medium transition" title="Descargar esta versión">
                                    <i class="fa-solid fa-download mr-1"></i> Descargar
                                </button>

                                ${index < this.currentVersions.length - 1 ? `
                                    <button onclick="window.DocuApp.compareWithPrevious(${v.id}, ${this.currentVersions[index + 1].id})" 
                                            class="px-2 py-1 text-xs text-slate-700 hover:text-purple-600 bg-slate-100 hover:bg-purple-50 rounded font-medium transition" title="Comparar diferencias con versión previa">
                                        <i class="fa-solid fa-code-compare mr-1"></i> Comparar
                                    </button>
                                ` : ''}

                                ${!isCurrent ? `
                                    <button onclick="window.DocuApp.restoreVersion(${v.id}, ${v.version_number})" 
                                            class="px-2.5 py-1 text-xs text-white bg-blue-600 hover:bg-blue-700 rounded font-bold transition shadow-xs" title="Restaurar esta versión como la nueva versión vigente">
                                        <i class="fa-solid fa-rotate-left mr-1"></i> Restaurar
                                    </button>
                                ` : ''}

                                <!-- Optional review button -->
                                <button onclick="window.DocuApp.openReviewModal(${v.id}, ${v.version_number})" 
                                        class="px-2 py-1 text-xs text-slate-600 hover:text-emerald-700 bg-slate-100 hover:bg-emerald-50 rounded font-medium transition" title="Revisión técnica o comentarios">
                                    <i class="fa-solid fa-clipboard-check mr-1"></i> Revisión
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    },

    async loadComments() {
        try {
            const comments = await window.Api.get(`/comments/file/${this.currentFile.id}`);
            document.getElementById('file-comment-count').textContent = comments.length;
            const container = document.getElementById('comments-list-container');
            
            if (!comments || comments.length === 0) {
                container.innerHTML = '<p class="text-xs text-slate-400 text-center py-4">No hay comentarios aún. Usa @usuario para mencionar a un compañero.</p>';
                return;
            }

            let html = '';
            comments.forEach(c => {
                const dateStr = new Date(c.created_at).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });
                // Highlight mentions
                const textWithMentions = c.text.replace(/@([a-zA-Z0-9_\.]+)/g, '<span class="text-blue-600 font-bold bg-blue-50 px-1 rounded">@$1</span>');

                html += `
                    <div class="p-3 bg-white border border-slate-200 rounded-xl space-y-1 text-xs">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-slate-800">${c.author_name} <span class="text-[10px] text-slate-400 font-normal">(${c.author_role})</span></span>
                            <span class="text-[10px] text-slate-400">${dateStr}</span>
                        </div>
                        <p class="text-slate-700">${textWithMentions}</p>
                    </div>
                `;
            });
            container.innerHTML = html;
        } catch (e) {}
    }
};

window.FileDetail = FileDetail;
