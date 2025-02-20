/** @odoo-module **/

import { Component, onWillStart, onMounted } from "@odoo/owl";

export class SignupValidation extends Component {
    setup() {
        onWillStart(() => this.loadRecaptcha());
        onMounted(() => {
            this.setupEmailValidation();
            this.setupFormValidation();
        });
    }

    async loadRecaptcha() {
        const script = document.createElement('script');
        script.src = 'https://www.google.com/recaptcha/api.js';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    }

    setupEmailValidation() {
        const loginInput = document.querySelector('#login');
        if (loginInput) {
            loginInput.addEventListener('input', this.validateEmail);
        }
    }

    setupFormValidation() {
        document.addEventListener('DOMContentLoaded', () => {
            const submitButton = document.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }
        });
    }

    validateEmail(event) {
        const email = event.target.value.toLowerCase();
        const pattern = /^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com$/;
        
        if (!pattern.test(email)) {
            event.target.setCustomValidity('Use un correo de Gmail, Hotmail, Outlook o Yahoo');
        } else {
            event.target.setCustomValidity('');
        }
    }
}

// Función global para reCAPTCHA callback
window.enableSignupSubmit = function(token) {
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton && token) {
        submitButton.disabled = false;
    }
};

// Registrar el componente
odoo.define('auth_signup.SignupValidation', function (require) {
    'use strict';
    
    const { registry } = require('@web/core/registry');
    registry.category('public_components').add('signup_validation', SignupValidation);
});