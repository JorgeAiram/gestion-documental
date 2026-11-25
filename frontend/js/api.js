// API Helper & State Client
const API_BASE = '/api/v1';

const Api = {
    getToken() {
        return localStorage.getItem('dms_token');
    },

    setToken(token) {
        localStorage.setItem('dms_token', token);
    },

    removeToken() {
        localStorage.removeItem('dms_token');
        localStorage.removeItem('dms_user');
    },

    getUser() {
        const u = localStorage.getItem('dms_user');
        return u ? JSON.parse(u) : null;
    },

    setUser(user) {
        localStorage.setItem('dms_user', JSON.stringify(user));
    },

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
        const headers = options.headers || {};
        
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (!options.isFormData && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        const config = {
            ...options,
            headers
        };

        try {
            const res = await fetch(url, config);

            if (res.status === 401) {
                this.removeToken();
                window.DocuApp.updateAuthUI();
                window.DocuApp.openModal('modal-login');
                throw new Error('Sesión expirada o credenciales requeridas');
            }

            if (!res.ok) {
                const errData = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(errData.detail || `Error en la petición (${res.status})`);
            }

            // Return json or blob
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await res.json();
            }
            return res;
        } catch (error) {
            console.error(`API Error on ${url}:`, error);
            window.DocuApp.showToast(error.message, 'error');
            throw error;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    upload(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            isFormData: true
        });
    }
};

window.Api = Api;
