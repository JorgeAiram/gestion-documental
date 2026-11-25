// In-Browser Document Previewer (PDF, Images, Text)
const Preview = {
    async open(fileId, filename, extension) {
        document.getElementById('preview-title').textContent = `Vista Previa: ${filename}`;
        const downloadLink = document.getElementById('preview-download-link');
        downloadLink.href = `/api/v1/files/${fileId}/download`;
        downloadLink.download = filename;

        const body = document.getElementById('preview-body');
        body.innerHTML = '<div class="text-center p-8"><i class="fa-solid fa-spinner fa-spin text-3xl text-blue-500 mb-2"></i><p class="text-xs text-slate-500">Cargando documento...</p></div>';
        window.DocuApp.openModal('modal-preview');

        const ext = (extension || '').toLowerCase().replace('.', '');
        const downloadUrl = `/api/v1/files/${fileId}/download`;

        try {
            if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext)) {
                // Image preview
                body.innerHTML = `
                    <div class="max-w-full max-h-full flex items-center justify-center p-4">
                        <img src="${downloadUrl}" alt="${filename}" class="max-w-full max-h-[75vh] object-contain rounded-lg shadow-lg">
                    </div>
                `;
            } else if (ext === 'pdf') {
                // PDF viewer
                body.innerHTML = `
                    <iframe src="${downloadUrl}" class="w-full h-[75vh] rounded-lg border border-slate-300" title="Visor PDF"></iframe>
                `;
            } else if (['txt', 'md', 'csv', 'json', 'xml', 'log', 'py', 'js', 'html', 'css', 'sql'].includes(ext)) {
                // Plain text / code preview
                const res = await fetch(downloadUrl, {
                    headers: { 'Authorization': `Bearer ${window.Api.getToken()}` }
                });
                const text = await res.text();
                body.innerHTML = `
                    <div class="w-full h-[75vh] overflow-auto bg-slate-900 text-slate-100 p-6 rounded-lg font-mono text-xs leading-relaxed">
                        <pre class="whitespace-pre-wrap">${text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                    </div>
                `;
            } else {
                // Unsupported formats (Word, Excel, Zip, etc.): show preview notice and download button
                body.innerHTML = `
                    <div class="text-center p-12 bg-white rounded-xl shadow-sm border border-slate-200 max-w-md">
                        <div class="w-16 h-16 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-2xl mx-auto mb-3">
                            <i class="fa-solid fa-file"></i>
                        </div>
                        <h4 class="font-bold text-slate-800 text-sm mb-1">${filename}</h4>
                        <p class="text-xs text-slate-500 mb-4">Los documentos de tipo .${ext.toUpperCase()} se descargan para su edición o visualización en la aplicación correspondiente (Word, Excel, AutoCAD, etc.).</p>
                        <a href="${downloadUrl}" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow inline-flex items-center gap-2">
                            <i class="fa-solid fa-download"></i> Descargar Documento
                        </a>
                    </div>
                `;
            }
        } catch (e) {
            body.innerHTML = '<div class="text-center text-red-500 p-8"><i class="fa-solid fa-circle-exclamation text-2xl mb-2"></i><p class="text-xs">Error al cargar la vista previa</p></div>';
        }
    }
};

window.Preview = Preview;
