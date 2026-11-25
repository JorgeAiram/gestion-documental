// Version Diff & Comparison Component
const VersionDiff = {
    async compare(versionAId, versionBId) {
        try {
            const res = await window.Api.post('/versions/diff', {
                version_a_id: versionAId,
                version_b_id: versionBId
            });
            this.render(res);
            window.DocuApp.openModal('modal-diff');
        } catch (e) {
            console.error('Diff error:', e);
        }
    },

    render(diffData) {
        const meta = diffData.metadata;
        const container = document.getElementById('diff-metadata-container');

        const formatDate = (iso) => new Date(iso).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });

        container.innerHTML = `
            <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-800 text-sm">Versión Base (v${meta.version_a.version_number})</span>
                    <span class="text-slate-400">${formatDate(meta.version_a.created_at)}</span>
                </div>
                <div><strong>Autor:</strong> ${meta.version_a.author}</div>
                <div><strong>Tamaño:</strong> ${window.Explorer.formatBytes(meta.version_a.file_size)}</div>
                <div><strong>Motivo:</strong> "${meta.version_a.comment}"</div>
                <div class="font-mono text-[10px] text-slate-400 truncate">SHA: ${meta.version_a.content_hash}</div>
            </div>

            <div class="p-3.5 bg-blue-50/50 border border-blue-200 rounded-xl space-y-2 text-xs">
                <div class="flex items-center justify-between">
                    <span class="font-bold text-blue-900 text-sm">Versión Comparada (v${meta.version_b.version_number})</span>
                    <span class="text-slate-400">${formatDate(meta.version_b.created_at)}</span>
                </div>
                <div><strong>Autor:</strong> ${meta.version_b.author}</div>
                <div><strong>Tamaño:</strong> ${window.Explorer.formatBytes(meta.version_b.file_size)} (${meta.size_difference >= 0 ? '+' : ''}${window.Explorer.formatBytes(meta.size_difference)})</div>
                <div><strong>Motivo:</strong> "${meta.version_b.comment}"</div>
                <div class="font-mono text-[10px] text-slate-400 truncate">SHA: ${meta.version_b.content_hash}</div>
            </div>
        `;

        const codeView = document.getElementById('diff-code-view');
        const statusLabel = document.getElementById('diff-status-label');

        if (meta.is_content_identical) {
            statusLabel.textContent = 'Contenido idéntico (SHA-256 coincide)';
            statusLabel.className = 'text-emerald-400';
            codeView.innerHTML = '<span class="text-slate-400">Los binarios o contenidos de ambas versiones son exactamente idénticos.</span>';
            return;
        }

        if (diffData.is_text && diffData.text_diff && diffData.text_diff.length > 0) {
            statusLabel.textContent = 'Diferencias encontradas en texto';
            statusLabel.className = 'text-amber-400';
            let diffHtml = '';
            diffData.text_diff.forEach(line => {
                const escaped = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                if (line.startsWith('+')) {
                    diffHtml += `<span class="diff-added">${escaped}</span>`;
                } else if (line.startsWith('-')) {
                    diffHtml += `<span class="diff-deleted">${escaped}</span>`;
                } else if (line.startsWith('@@')) {
                    diffHtml += `<span class="diff-header">${escaped}</span>`;
                } else {
                    diffHtml += `<span>${escaped}</span>\n`;
                }
            });
            codeView.innerHTML = diffHtml;
        } else {
            statusLabel.textContent = 'Archivo binario / formato enriquecido';
            statusLabel.className = 'text-blue-400';
            codeView.innerHTML = '<span class="text-slate-400">Este es un archivo binario (Word, Excel, PDF, etc.). La comparación de metadatos, tamaño y hash de integridad SHA-256 está disponible en las tarjetas superiores.</span>';
        }
    }
};

window.VersionDiff = VersionDiff;
