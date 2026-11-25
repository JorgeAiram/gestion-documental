// File Explorer Component
const Explorer = {
    viewMode: 'list', // 'list' or 'grid'
    currentFiles: [],

    init() {
        document.getElementById('btn-view-list').addEventListener('click', () => {
            this.viewMode = 'list';
            this.updateViewButtons();
            this.render();
        });

        document.getElementById('btn-view-grid').addEventListener('click', () => {
            this.viewMode = 'grid';
            this.updateViewButtons();
            this.render();
        });

        document.getElementById('sort-select').addEventListener('change', (e) => {
            this.sortFiles(e.target.value);
            this.render();
        });

        this.setupDragAndDrop();
    },

    updateViewButtons() {
        const listBtn = document.getElementById('btn-view-list');
        const gridBtn = document.getElementById('btn-view-grid');
        if (this.viewMode === 'list') {
            listBtn.className = 'px-2.5 py-1.5 text-xs bg-blue-50 text-blue-600 font-bold';
            gridBtn.className = 'px-2.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100';
        } else {
            gridBtn.className = 'px-2.5 py-1.5 text-xs bg-blue-50 text-blue-600 font-bold';
            listBtn.className = 'px-2.5 py-1.5 text-xs text-slate-600 hover:bg-slate-100';
        }
    },

    setupDragAndDrop() {
        const dropZone = document.getElementById('drop-zone');
        const dragOverlay = document.getElementById('drag-overlay');

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragOverlay.classList.remove('hidden');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragOverlay.classList.add('hidden');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                window.DocuApp.handleDroppedFiles(files);
            }
        });
    },

    setFiles(files) {
        this.currentFiles = files;
        this.sortFiles(document.getElementById('sort-select').value);
        this.render();
    },

    sortFiles(sortCriteria) {
        if (!this.currentFiles) return;
        this.currentFiles.sort((a, b) => {
            if (sortCriteria === 'name_asc') {
                return a.name.localeCompare(b.name);
            } else if (sortCriteria === 'size_desc') {
                return (b.file_size || 0) - (a.file_size || 0);
            } else {
                // updated_desc
                return new Date(b.updated_at) - new Date(a.updated_at);
            }
        });
    },

    formatBytes(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    getFileIcon(extension) {
        const ext = (extension || '').toLowerCase().replace('.', '');
        if (['pdf'].includes(ext)) return { icon: 'fa-file-pdf', color: 'text-red-500', bg: 'bg-red-50' };
        if (['doc', 'docx'].includes(ext)) return { icon: 'fa-file-word', color: 'text-blue-600', bg: 'bg-blue-50' };
        if (['xls', 'xlsx', 'csv'].includes(ext)) return { icon: 'fa-file-excel', color: 'text-emerald-600', bg: 'bg-emerald-50' };
        if (['png', 'jpg', 'jpeg', 'svg', 'gif'].includes(ext)) return { icon: 'fa-file-image', color: 'text-purple-600', bg: 'bg-purple-50' };
        if (['txt', 'md', 'log'].includes(ext)) return { icon: 'fa-file-lines', color: 'text-slate-600', bg: 'bg-slate-100' };
        return { icon: 'fa-file', color: 'text-slate-500', bg: 'bg-slate-50' };
    },

    render() {
        const container = document.getElementById('explorer-container');
        const emptyState = document.getElementById('empty-state');

        if (!this.currentFiles || this.currentFiles.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');

        if (this.viewMode === 'list') {
            let html = `
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs divide-y divide-slate-200">
                    <thead class="bg-slate-50 font-semibold text-slate-500">
                        <tr>
                            <th class="py-2.5 px-3">Documento</th>
                            <th class="py-2.5 px-3">Versión Vigente</th>
                            <th class="py-2.5 px-3">Estado de Edición</th>
                            <th class="py-2.5 px-3">Último Cambio</th>
                            <th class="py-2.5 px-3">Tamaño</th>
                            <th class="py-2.5 px-3">Ubicación</th>
                            <th class="py-2.5 px-3 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
            `;

            this.currentFiles.forEach(f => {
                const iconInfo = this.getFileIcon(f.extension);
                const isLocked = f.is_locked;
                const lockBadge = isLocked 
                    ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold badge-locked inline-flex items-center gap-1" title="Bloqueado por ${f.locked_by_name}">
                         <i class="fa-solid fa-lock text-[9px]"></i> En edición (${f.locked_by_name?.split(' ')[0] || 'Usuario'})
                       </span>`
                    : `<span class="px-2 py-0.5 rounded text-[10px] font-bold badge-free inline-flex items-center gap-1">
                         <i class="fa-solid fa-lock-open text-[9px]"></i> Disponible
                       </span>`;

                const dateStr = new Date(f.updated_at).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });

                html += `
                    <tr class="hover:bg-blue-50/40 cursor-pointer transition-colors group" onclick="window.DocuApp.openFileDetail(${f.id})">
                        <td class="py-3 px-3">
                            <div class="flex items-center gap-2.5">
                                <div class="w-8 h-8 rounded-lg ${iconInfo.bg} ${iconInfo.color} flex items-center justify-center text-sm shadow-xs">
                                    <i class="fa-solid ${iconInfo.icon}"></i>
                                </div>
                                <div>
                                    <div class="font-bold text-slate-800 group-hover:text-blue-600 transition flex items-center gap-1.5">
                                        ${f.name}
                                    </div>
                                    <div class="text-[11px] text-slate-400">
                                        Subido por: ${f.created_by_name || 'Desconocido'}
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td class="py-3 px-3">
                            <span class="px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-bold text-[11px]">
                                v${f.version_number || 1}
                            </span>
                        </td>
                        <td class="py-3 px-3">${lockBadge}</td>
                        <td class="py-3 px-3 text-slate-600 text-[11px]">${dateStr}</td>
                        <td class="py-3 px-3 text-slate-500 font-mono text-[11px]">${this.formatBytes(f.file_size)}</td>
                        <td class="py-3 px-3 text-slate-500 text-[11px]">
                            <i class="fa-solid fa-folder text-amber-400 mr-1"></i>${f.folder_name || 'Directorio Raíz'}
                        </td>
                        <td class="py-3 px-3 text-right" onclick="event.stopPropagation()">
                            <div class="flex items-center justify-end gap-1">
                                <button onclick="window.DocuApp.downloadFile(${f.id})" class="p-1.5 text-slate-500 hover:text-blue-600 rounded hover:bg-slate-100" title="Descargar versión vigente">
                                    <i class="fa-solid fa-download"></i>
                                </button>
                                <button onclick="window.DocuApp.previewFile(${f.id}, '${f.name}', '${f.extension}')" class="p-1.5 text-slate-500 hover:text-blue-600 rounded hover:bg-slate-100" title="Vista previa">
                                    <i class="fa-solid fa-eye"></i>
                                </button>
                                <button onclick="window.DocuApp.openFileDetail(${f.id})" class="p-1.5 text-slate-500 hover:text-blue-600 rounded hover:bg-slate-100" title="Historial de versiones">
                                    <i class="fa-solid fa-timeline"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;
            container.innerHTML = html;

        } else {
            // Grid View
            let html = `<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 p-1">`;
            this.currentFiles.forEach(f => {
                const iconInfo = this.getFileIcon(f.extension);
                const isLocked = f.is_locked;
                const lockBadge = isLocked 
                    ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold badge-locked flex items-center gap-1">
                         <i class="fa-solid fa-lock"></i> Bloqueado
                       </span>`
                    : `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold badge-free flex items-center gap-1">
                         <i class="fa-solid fa-lock-open"></i> Libre
                       </span>`;

                html += `
                    <div class="file-card bg-white border border-slate-200 rounded-xl p-4 flex flex-col justify-between cursor-pointer hover:border-blue-400"
                         onclick="window.DocuApp.openFileDetail(${f.id})">
                        <div>
                            <div class="flex items-start justify-between mb-3">
                                <div class="w-10 h-10 rounded-xl ${iconInfo.bg} ${iconInfo.color} flex items-center justify-center text-lg shadow-sm">
                                    <i class="fa-solid ${iconInfo.icon}"></i>
                                </div>
                                <div class="flex items-center gap-1">
                                    <span class="px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded font-bold text-[10px]">
                                        v${f.version_number || 1}
                                    </span>
                                    ${lockBadge}
                                </div>
                            </div>
                            <h4 class="font-bold text-xs text-slate-800 truncate mb-1" title="${f.name}">${f.name}</h4>
                            <p class="text-[11px] text-slate-400 mb-2 truncate">${f.folder_name || 'Directorio Raíz'}</p>
                        </div>
                        <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                            <span class="font-mono">${this.formatBytes(f.file_size)}</span>
                            <div class="flex items-center gap-1" onclick="event.stopPropagation()">
                                <button onclick="window.DocuApp.previewFile(${f.id}, '${f.name}', '${f.extension}')" class="p-1 hover:text-blue-600" title="Vista previa">
                                    <i class="fa-solid fa-eye"></i>
                                </button>
                                <button onclick="window.DocuApp.downloadFile(${f.id})" class="p-1 hover:text-blue-600" title="Descargar">
                                    <i class="fa-solid fa-download"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
            container.innerHTML = html;
        }
    }
};

window.Explorer = Explorer;
