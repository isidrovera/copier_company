/** @odoo-module */

import { loadJS } from "@web/core/assets";

const RECAPTCHA_URL = 'https://www.google.com/recaptcha/api.js';

export class SignupValidation extends Component {
    setup() {
        this.loadRecaptcha();
        this.setupEmailValidation();
        this.disableSubmitButton();
    }

    async loadRecaptcha() {
        await loadJS(RECAPTCHA_URL);
    }

    setupEmailValidation() {
        const loginInput = document.querySelector('#login');
        if (loginInput) {
            loginInput.addEventListener('input', this.validateEmail.bind(this));
        }
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

    disableSubmitButton() {
        const submitButton = document.querySelector('.oe_signup_form button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
        }
    }
}

// Función global para reCAPTCHA
window.enableSignupSubmit = function(token) {
    const submitButton = document.querySelector('.oe_signup_form button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = false;
    }
};